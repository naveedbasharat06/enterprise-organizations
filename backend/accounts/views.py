from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated, AllowAny

from .models import User, Organization, PasswordResetOTP, AppPermission, Role, UserRole, UserDirectPermission
from .serializers import (
    UserSerializer, OrganizationSerializer, LoginSerializer,
    ForgotPasswordSerializer, ResetPasswordConfirmSerializer,
    AppPermissionSerializer, RoleSerializer, UserRoleSerializer, UserDirectPermissionSerializer
)
from .permissions import IsSuperAdmin, IsAdminOrSuperAdmin
 
 
# ─── AUTH VIEWS ─────────────────────────────────────────────────────────────
 
class LoginView(APIView):
    permission_classes = [AllowAny]
 
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password']
        )
        if not user:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data
        })
 
 
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
 
    def post(self, request):
        request.user.auth_token.delete()
        return Response({'message': 'Logged out successfully'})
 
 
class MeView(APIView):
    permission_classes = [IsAuthenticated]
 
    def get(self, request):
        return Response(UserSerializer(request.user).data)


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'message': 'If this email is registered, an OTP has been sent.'})
        otp_obj = PasswordResetOTP.generate_for_user(user)
        try:
            send_mail(
                subject='Password Reset OTP - RoleBase',
                message=(
                    f'Hello {user.username},\n\n'
                    f'Your OTP for password reset is: {otp_obj.otp}\n\n'
                    f'This OTP is valid for 15 minutes.\n\n'
                    f'If you did not request this, please ignore this email.\n\n'
                    f'- RoleBase Team'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
        except Exception as e:
            import traceback; traceback.print_exc()
            return Response(
                {'error': f'Failed to send email: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        return Response({'message': 'If this email is registered, an OTP has been sent.'})


class ResetPasswordConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']
        new_password = serializer.validated_data['new_password']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'Invalid email or OTP'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            otp_obj = PasswordResetOTP.objects.filter(user=user, otp=otp, is_used=False).latest('created_at')
        except PasswordResetOTP.DoesNotExist:
            return Response({'error': 'Invalid or expired OTP'}, status=status.HTTP_400_BAD_REQUEST)
        if not otp_obj.is_valid():
            return Response({'error': 'OTP has expired. Please request a new one.'}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new_password)
        user.save()
        otp_obj.is_used = True
        otp_obj.save()
        Token.objects.filter(user=user).delete()
        return Response({'message': 'Password reset successfully. You can now log in.'})


# ─── ORGANIZATION VIEWSET ────────────────────────────────────────────────────
 
class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
 
    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'members', 'add_member', 'remove_member']:
            return [IsAdminOrSuperAdmin()]
        return [IsSuperAdmin()]
 
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Organization.objects.none()
        if user.role == 'super_admin':
            return Organization.objects.all()
        if user.role == 'admin':
            if user.organization:
                return Organization.objects.filter(id=user.organization.id)
            return Organization.objects.none()
        return Organization.objects.none()
 
    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        user = request.user
        org = self.get_object()
        if user.role == 'admin' and user.organization != org:
            return Response({'error': 'You can only view members of your own organization'}, status=403)
        users = org.members.all()
        return Response(UserSerializer(users, many=True).data)
 
    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        user = request.user
        org = self.get_object()
        if user.role == 'admin' and user.organization != org:
            return Response({'error': 'You can only add members to your own organization'}, status=403)
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'error': 'user_id is required'}, status=400)
        try:
            target = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)
        if target.organization:
            return Response({'error': f'{target.username} already belongs to an organization'}, status=400)
        target.organization = org
        target.save()
        return Response({'message': f'{target.username} added to {org.name}'})
 
    @action(detail=True, methods=['post'])
    def remove_member(self, request, pk=None):
        user = request.user
        org = self.get_object()
        if user.role == 'admin' and user.organization != org:
            return Response({'error': 'You can only remove members from your own organization'}, status=403)
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'error': 'user_id is required'}, status=400)
        try:
            target = User.objects.get(id=user_id, organization=org)
        except User.DoesNotExist:
            return Response({'error': 'User not found in this organization'}, status=404)
        if target.role == 'super_admin':
            return Response({'error': 'Cannot remove a Super Admin'}, status=400)
        target.organization = None
        target.save()
        return Response({'message': f'{target.username} removed from {org.name}'})
 
 
# ─── USER VIEWSET ────────────────────────────────────────────────────────────
 
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
 
    def get_permissions(self):
        if self.action == 'create':
            return [IsSuperAdmin()]
        if self.action in ['list', 'unassigned']:
            return [IsAdminOrSuperAdmin()]
        if self.action in ['destroy', 'make_admin', 'make_member']:
            return [IsSuperAdmin()]
        return [IsAuthenticated()]
 
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return User.objects.none()
        if user.role == 'super_admin':
            return User.objects.all()
        if user.role == 'admin':
            return User.objects.filter(organization=user.organization)
        return User.objects.filter(id=user.id)
 
    @action(detail=False, methods=['get'])
    def unassigned(self, request):
        """Returns all users with no organization — for Admin add member dropdown"""
        users = User.objects.filter(organization__isnull=True, role='member')
        return Response(UserSerializer(users, many=True).data)
 
    @action(detail=True, methods=['post'], permission_classes=[IsSuperAdmin])
    def make_admin(self, request, pk=None):
        target = self.get_object()
        if not target.organization:
            return Response({'error': 'User must belong to an organization first'}, status=400)
        target.role = 'admin'
        target.save()
        return Response({'message': f'{target.username} is now an Admin'})
 
    @action(detail=True, methods=['post'], permission_classes=[IsSuperAdmin])
    def make_member(self, request, pk=None):
        target = self.get_object()
        target.role = 'member'
        target.save()
        return Response({'message': f'{target.username} is now a Member'})

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrSuperAdmin])
    def assign_role(self, request, pk=None):
        target = self.get_object()
        role_id = request.data.get('role_id')
        if not role_id:
            return Response({'error': 'role_id is required'}, status=400)
        try:
            role = Role.objects.get(id=role_id)
        except Role.DoesNotExist:
            return Response({'error': 'Role not found'}, status=404)
        if request.user.role == 'admin':
            if role.organization != request.user.organization:
                return Response({'error': 'You can only assign roles from your organization'}, status=403)
            if target.organization != request.user.organization:
                return Response({'error': 'You can only assign roles to users in your organization'}, status=403)
        UserRole.objects.get_or_create(user=target, role=role, defaults={'assigned_by': request.user})
        return Response({'message': f'Role "{role.name}" assigned to {target.username}'})

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrSuperAdmin])
    def remove_role(self, request, pk=None):
        target = self.get_object()
        role_id = request.data.get('role_id')
        try:
            user_role = UserRole.objects.get(user=target, role_id=role_id)
            user_role.delete()
            return Response({'message': 'Role removed successfully'})
        except UserRole.DoesNotExist:
            return Response({'error': 'Role not assigned to this user'}, status=404)

    @action(detail=True, methods=['get'], permission_classes=[IsAdminOrSuperAdmin])
    def roles(self, request, pk=None):
        target = self.get_object()
        user_roles = UserRole.objects.filter(user=target).select_related('role', 'assigned_by')
        return Response(UserRoleSerializer(user_roles, many=True).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrSuperAdmin])
    def assign_permission(self, request, pk=None):
        target = self.get_object()
        permission_id = request.data.get('permission_id')
        if not permission_id:
            return Response({'error': 'permission_id is required'}, status=400)
        try:
            permission = AppPermission.objects.get(id=permission_id)
        except AppPermission.DoesNotExist:
            return Response({'error': 'Permission not found'}, status=404)
        if request.user.role == 'admin' and target.organization != request.user.organization:
            return Response({'error': 'You can only assign permissions to users in your organization'}, status=403)
        UserDirectPermission.objects.get_or_create(
            user=target, permission=permission, defaults={'assigned_by': request.user}
        )
        return Response({'message': f'Permission "{permission.name}" assigned to {target.username}'})

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrSuperAdmin])
    def remove_permission(self, request, pk=None):
        target = self.get_object()
        permission_id = request.data.get('permission_id')
        try:
            udp = UserDirectPermission.objects.get(user=target, permission_id=permission_id)
            udp.delete()
            return Response({'message': 'Permission removed successfully'})
        except UserDirectPermission.DoesNotExist:
            return Response({'error': 'Permission not directly assigned to this user'}, status=404)

    @action(detail=True, methods=['get'], permission_classes=[IsAdminOrSuperAdmin])
    def direct_permissions(self, request, pk=None):
        target = self.get_object()
        perms = UserDirectPermission.objects.filter(user=target).select_related('permission', 'assigned_by')
        return Response(UserDirectPermissionSerializer(perms, many=True).data)


# ─── PERMISSION VIEWSET ───────────────────────────────────────────────────────

class AppPermissionViewSet(viewsets.ModelViewSet):
    serializer_class = AppPermissionSerializer

    def get_permissions(self):
        return [IsAdminOrSuperAdmin()]

    def get_queryset(self):
        from django.db.models import Q
        user = self.request.user
        if not user.is_authenticated:
            return AppPermission.objects.none()
        if user.role == 'super_admin':
            return AppPermission.objects.all()
        if user.role == 'admin' and user.organization:
            # Admin sees: global (org=None) + their own org's permissions
            return AppPermission.objects.filter(
                Q(organization=None) | Q(organization=user.organization)
            )
        return AppPermission.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if user.role == 'admin':
            serializer.save(created_by=user, organization=user.organization)
        else:
            serializer.save(created_by=user, organization=None)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user.role == 'admin':
            if instance.organization != request.user.organization:
                return Response(
                    {'error': 'You can only edit permissions created for your organization'},
                    status=status.HTTP_403_FORBIDDEN
                )
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user.role == 'admin':
            if instance.organization != request.user.organization:
                return Response(
                    {'error': 'You can only delete permissions created for your organization'},
                    status=status.HTTP_403_FORBIDDEN
                )
        return super().destroy(request, *args, **kwargs)


# ─── ROLE VIEWSET ─────────────────────────────────────────────────────────────

class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer

    def get_permissions(self):
        return [IsAdminOrSuperAdmin()]

    def get_queryset(self):
        from django.db.models import Q
        user = self.request.user
        if not user.is_authenticated:
            return Role.objects.none()
        if user.role == 'super_admin':
            return Role.objects.all().prefetch_related('permissions')
        if user.role == 'admin' and user.organization:
            # Admin sees: global roles (org=None) + their own org's roles
            return Role.objects.filter(
                Q(organization=None) | Q(organization=user.organization)
            ).prefetch_related('permissions')
        return Role.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if user.role == 'admin':
            serializer.save(created_by=user, organization=user.organization)
        else:
            serializer.save(created_by=user)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user.role == 'admin':
            if instance.organization is None or instance.organization != request.user.organization:
                return Response(
                    {'error': 'You can only edit roles created for your organization'},
                    status=status.HTTP_403_FORBIDDEN
                )
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user.role == 'admin':
            if instance.organization is None or instance.organization != request.user.organization:
                return Response(
                    {'error': 'You can only delete roles created for your organization'},
                    status=status.HTTP_403_FORBIDDEN
                )
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def assign_permissions(self, request, pk=None):
        role = self.get_object()
        permission_ids = request.data.get('permission_ids', [])
        permissions = AppPermission.objects.filter(id__in=permission_ids)
        role.permissions.set(permissions)
        return Response(RoleSerializer(role).data)


# ─── DASHBOARD STATS ─────────────────────────────────────────────────────────
 
class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]
 
    def get(self, request):
        user = request.user
        if user.role == 'super_admin':
            return Response({
                'total_organizations': Organization.objects.count(),
                'total_users': User.objects.count(),
                'total_admins': User.objects.filter(role='admin').count(),
                'total_members': User.objects.filter(role='member').count(),
            })
        elif user.role == 'admin':
            org = user.organization
            return Response({
                'organization': org.name if org else None,
                'total_members': User.objects.filter(organization=org).count(),
                'admins_in_org': User.objects.filter(organization=org, role='admin').count(),
            })
        else:
            return Response({
                'organization': user.organization.name if user.organization else 'Not Assigned',
                'role': user.role,
                'username': user.username,
            })