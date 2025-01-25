from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import json
import random
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import User, OTP

@method_decorator(csrf_exempt, name='dispatch')
class LoginView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')

            if not username or not password:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Username and password are required.'
                }, status=400)

            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return JsonResponse({
                    'status': 'success',
                    'message': 'Login successful.',
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                    }
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid username or password.'
                }, status=400)
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON data.'
            }, status=400)

    def get(self, request, *args, **kwargs):
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid request method. Use POST.'
        }, status=405)

@method_decorator(csrf_exempt, name='dispatch')
class LogoutView(View):
    def post(self, request, *args, **kwargs):
        logout(request)
        return JsonResponse({
            'status': 'success',
            'message': 'Logout successful.'
        })

    def get(self, request, *args, **kwargs):
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid request method. Use POST.'
        }, status=405)

@method_decorator(login_required, name='dispatch')
class CheckSessionView(View):
    def get(self, request, *args, **kwargs):
        user = request.user
        return JsonResponse({
            'status': 'success',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
            }
        })

@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')

            if not username or not email or not password:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Username, email, and password are required.'
                }, status=400)

            if User.objects.filter(username=username).exists():
                return JsonResponse({
                    'status': 'error',
                    'message': 'Username already exists.'
                }, status=400)

            if User.objects.filter(email=email).exists():
                return JsonResponse({
                    'status': 'error',
                    'message': 'Email already exists.'
                }, status=400)

            # Create the user
            user = User.objects.create_user(username=username, email=email, password=password)
            user.is_verified = False
            user.save()

            # Generate and send verification email
            token = user.generate_verification_token()
            verification_link = f"http://localhost:3000/verify-email/{token}/"
            send_mail(
                'Verify Your Email',
                f'Please click the link to verify your email: {verification_link}',
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
            )

            return JsonResponse({
                'status': 'success',
                'message': 'User registered successfully. Please check your email to verify your account.'
            })
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON data.'
            }, status=400)

    def get(self, request, *args, **kwargs):
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid request method. Use POST.'
        }, status=405)

@method_decorator(csrf_exempt, name='dispatch')
class ForgotPasswordView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            email = data.get('email')

            if not email:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Email is required.'
                }, status=400)

            user = User.objects.filter(email=email).first()
            if not user:
                return JsonResponse({
                    'status': 'error',
                    'message': 'User with this email does not exist.'
                }, status=404)

            # Generate OTP
            otp = str(random.randint(100000, 999999))

            # Store OTP in the database
            OTP.objects.create(user=user, otp=otp)

            # Send OTP via email
            send_mail(
                'Password Reset OTP',
                f'Your OTP for password reset is: {otp}',
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
            )

            return JsonResponse({
                'status': 'success',
                'message': 'OTP sent to your email.'
            })
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON data.'
            }, status=400)

    def get(self, request, *args, **kwargs):
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid request method. Use POST.'
        }, status=405)

@method_decorator(csrf_exempt, name='dispatch')
class VerifyOTPView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            otp_entered = data.get('otp')

            if not otp_entered:
                return JsonResponse({
                    'status': 'error',
                    'message': 'OTP is required.'
                }, status=400)

            # Retrieve the OTP from the database
            otp_record = OTP.objects.filter(otp=otp_entered).first()

            if otp_record:
                email = otp_record.user.email
                otp_record.delete()
                return JsonResponse({
                    'status': 'success',
                    'message': 'OTP verified successfully.',
                    'email': email 
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid OTP.'
                }, status=400)
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON data.'
            }, status=400)

    def get(self, request, *args, **kwargs):
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid request method. Use POST.'
        }, status=405)

@method_decorator(csrf_exempt, name='dispatch')
class ResetPasswordView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            email = data.get('email')
            new_password = data.get('new_password')
            confirm_password = data.get('confirm_password')

            if not email or not new_password or not confirm_password:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Email, new password, and confirm password are required.'
                }, status=400)

            if new_password != confirm_password:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Passwords do not match.'
                }, status=400)

            user = User.objects.filter(email=email).first()
            if not user:
                return JsonResponse({
                    'status': 'error',
                    'message': 'User with this email does not exist.'
                }, status=404)

            user.set_password(new_password)
            user.save()

            return JsonResponse({
                'status': 'success',
                'message': 'Password reset successfully.'
            })
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON data.'
            }, status=400)

    def get(self, request, *args, **kwargs):
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid request method. Use POST.'
        }, status=405)

@method_decorator(csrf_exempt, name='dispatch')
class UpdateProfileView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            username = data.get('username')
            email = data.get('email')
            old_password = data.get('old_password') 
            new_password = data.get('new_password')
            confirm_password = data.get('confirm_password')

            user = request.user
            if not user.is_authenticated:
                return JsonResponse({
                    'status': 'error',
                    'message': 'User not authenticated.'
                }, status=401)

            # Validate old password
            if not authenticate(username=user.username, password=old_password):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Old password is incorrect.'
                }, status=400)

            # Update username and email
            if username:
                user.username = username
            if email:
                user.email = email

            # Update password if new password is provided
            if new_password and confirm_password:
                if new_password != confirm_password:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'New passwords do not match.'
                    }, status=400)
                user.set_password(new_password)

            user.save()

            return JsonResponse({
                'status': 'success',
                'message': 'Profile updated successfully.'
            })
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON data.'
            }, status=400)

    def get(self, request, *args, **kwargs):
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid request method. Use POST.'
        }, status=405)

@method_decorator(csrf_exempt, name='dispatch')
class VerifyEmailView(View):
    def get(self, request, token, *args, **kwargs):
        try:
            user = User.objects.get(verification_token=token)
            if user.is_verified:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Email is already verified.'
                }, status=400)

            user.is_verified = True
            user.verification_token = None
            user.save()

            return JsonResponse({
                'status': 'success',
                'message': 'Email verified successfully. You can now log in.'
            })
        except User.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid verification token.'
            }, status=400)
        