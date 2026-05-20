from rest_framework.permissions import BasePermission


class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'super_admin'


class IsAdminOrSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['super_admin', 'admin']


class IsAuthenticated(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated


class CanUseRecording(BasePermission):
    """
    Platform admin (super_admin with no org): always allowed.
    Org super admin / admin: org must have can_use_recording=True.
    Member: org must have can_use_recording=True AND user has 'use_video_transcription'
            permission via a role or as a direct permission.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        user = request.user
        if user.role == 'super_admin' and user.organization is None:
            return True  # platform admin
        if not user.organization or not user.organization.can_use_recording:
            return False
        if user.role == 'admin':
            return True
        # member: check role permissions or direct permissions
        from .models import UserRole, UserDirectPermission
        has_via_role = UserRole.objects.filter(
            user=user,
            role__permissions__codename='use_video_transcription'
        ).exists()
        if has_via_role:
            return True
        return UserDirectPermission.objects.filter(
            user=user,
            permission__codename='use_video_transcription'
        ).exists()
