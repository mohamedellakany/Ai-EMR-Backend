from django.urls import path
from .views import (LoginView, LogoutView, CheckSessionView, RegisterView, 
                    ForgotPasswordView, VerifyOTPView, ResetPasswordView, 
                    UpdateProfileView, VerifyEmailView)

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('check-session/', CheckSessionView.as_view(), name='check-session'), 
    path('register/', RegisterView.as_view(), name='register'), 
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('update-profile/', UpdateProfileView.as_view(), name='update-profile'),
    path('verify-email/<str:token>/', VerifyEmailView.as_view(), name='verify-email'),
]