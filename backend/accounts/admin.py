from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Organization

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    search_fields = ['name']

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'role', 'organization', 'date_joined']
    list_filter = ['role', 'organization']
    fieldsets = UserAdmin.fieldsets + (
        ('Role & Organization', {'fields': ('role', 'organization')}),
    )
