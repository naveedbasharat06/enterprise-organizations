from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, Organization, AppPermission, Role,
    UserRole, UserDirectPermission, UserInvitation,
    PasswordResetOTP, Recording
)

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'can_use_recording', 'created_at']
    search_fields = ['name']

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'role', 'organization', 'date_joined']
    list_filter = ['role', 'organization']
    fieldsets = UserAdmin.fieldsets + (
        ('Role & Organization', {'fields': ('role', 'organization')}),
    )

@admin.register(AppPermission)
class AppPermissionAdmin(admin.ModelAdmin):
    list_display = ['name', 'codename', 'organization', 'created_by', 'created_at']
    list_filter = ['organization']
    search_fields = ['name', 'codename']

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'organization', 'created_by', 'created_at']
    list_filter = ['organization']
    search_fields = ['name']
    filter_horizontal = ['permissions']

@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'assigned_by', 'assigned_at']
    list_filter = ['role']
    search_fields = ['user__username', 'role__name']

@admin.register(UserDirectPermission)
class UserDirectPermissionAdmin(admin.ModelAdmin):
    list_display = ['user', 'permission', 'assigned_by', 'assigned_at']
    search_fields = ['user__username', 'permission__name']

@admin.register(UserInvitation)
class UserInvitationAdmin(admin.ModelAdmin):
    list_display = ['email', 'organization', 'invited_by', 'is_used', 'created_at']
    list_filter = ['is_used', 'organization']
    search_fields = ['email']

@admin.register(PasswordResetOTP)
class PasswordResetOTPAdmin(admin.ModelAdmin):
    list_display = ['user', 'otp', 'created_at', 'is_used']
    search_fields = ['user__username']

@admin.register(Recording)
class RecordingAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'organization', 'status', 'created_at']
    list_filter = ['status', 'organization']
    search_fields = ['title', 'user__username']
    readonly_fields = ['transcript_data', 'created_at', 'updated_at']
