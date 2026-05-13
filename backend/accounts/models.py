import random
from datetime import timedelta
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class Organization(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class User(AbstractUser):
    ROLE_SUPER_ADMIN = 'super_admin'
    ROLE_ADMIN = 'admin'
    ROLE_MEMBER = 'member'

    ROLE_CHOICES = [
        (ROLE_SUPER_ADMIN, 'Super Admin'),
        (ROLE_ADMIN, 'Admin'),
        (ROLE_MEMBER, 'Member'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_MEMBER)
    organization = models.ForeignKey(
        Organization, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='members'
    )
    email = models.EmailField(unique=True)

    def __str__(self):
        return f"{self.username} ({self.role})"

    @property
    def is_super_admin(self):
        return self.role == self.ROLE_SUPER_ADMIN

    @property
    def is_org_admin(self):
        return self.role in [self.ROLE_SUPER_ADMIN, self.ROLE_ADMIN]


class AppPermission(models.Model):
    name = models.CharField(max_length=255)
    codename = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE,
        null=True, blank=True, related_name='app_permissions'
    )
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='created_permissions'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('codename', 'organization')

    def __str__(self):
        org = self.organization.name if self.organization else 'Global'
        return f"{self.name} ({self.codename}) [{org}]"


class Role(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE,
        null=True, blank=True, related_name='roles'
    )
    permissions = models.ManyToManyField(AppPermission, blank=True, related_name='roles')
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='created_roles'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('name', 'organization')

    def __str__(self):
        org = self.organization.name if self.organization else 'Global'
        return f"{self.name} ({org})"


class UserRole(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_roles')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='user_roles')
    assigned_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='roles_assigned_by_me'
    )
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'role')


class UserDirectPermission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='direct_permissions')
    permission = models.ForeignKey(
        AppPermission, on_delete=models.CASCADE, related_name='direct_user_permissions'
    )
    assigned_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='permissions_assigned_by_me'
    )
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'permission')


class PasswordResetOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reset_otps')
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_valid(self):
        return not self.is_used and timezone.now() < self.created_at + timedelta(minutes=15)

    @classmethod
    def generate_for_user(cls, user):
        cls.objects.filter(user=user, is_used=False).delete()
        otp = str(random.randint(100000, 999999))
        return cls.objects.create(user=user, otp=otp)
