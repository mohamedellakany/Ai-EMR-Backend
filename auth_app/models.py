from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
import uuid

class User(AbstractUser):
    is_verified = models.BooleanField(default=False)  # Track if the user is verified
    verification_token = models.CharField(max_length=100, blank=True, null=True)  # Store the verification token

    # Add unique related_name attributes to avoid clashes
    groups = models.ManyToManyField(
        Group,
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_name="auth_app_user_groups",  # Unique related_name
        related_query_name="auth_app_user",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="auth_app_user_permissions",  # Unique related_name
        related_query_name="auth_app_user",
    )

    def generate_verification_token(self):
        self.verification_token = uuid.uuid4().hex  # Generate a unique token
        self.save()
        return self.verification_token