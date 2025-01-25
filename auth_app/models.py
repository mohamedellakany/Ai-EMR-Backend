from django.contrib.auth.models import AbstractUser, Group, Permission, User
from django.db import models
import uuid

class User(AbstractUser):
    is_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=100, blank=True, null=True)

    groups = models.ManyToManyField(
        Group,
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_name="auth_app_user_groups",
        related_query_name="auth_app_user",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="auth_app_user_permissions",
        related_query_name="auth_app_user",
    )

    def generate_verification_token(self):
        self.verification_token = uuid.uuid4().hex 
        self.save()
        return self.verification_token

class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"OTP for {self.user.email}"