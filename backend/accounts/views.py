from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .throttles import LoginThrottle, PasswordResetThrottle, InviteThrottle

from .models import (
    User, Organization, PasswordResetOTP, AppPermission, Role,
    UserRole, UserDirectPermission, UserInvitation, Recording
)
from .serializers import (
    UserSerializer, OrganizationSerializer, LoginSerializer,
    InviteUserSerializer, AcceptInvitationSerializer,
    ForgotPasswordSerializer, ResetPasswordConfirmSerializer,
    AppPermissionSerializer, RoleSerializer,
    UserRoleSerializer, MyRoleSerializer, UserDirectPermissionSerializer,
    RecordingSerializer
)
from .permissions import IsSuperAdmin, IsAdminOrSuperAdmin, CanUseRecording


def _is_platform_admin(user):
    """Platform-wide admin (seeded superadmin, no org). Org super admins have an org assigned."""
    return user.role == 'super_admin' and user.organization is None


# ─── AUTH VIEWS ─────────────────────────────────────────────────────────────
 
class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [LoginThrottle]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password']
        )
        if not user:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        if user.organization and not user.organization.is_verified:
            return Response(
                {'error': 'Your organization is pending Super Admin verification. You will be notified once approved.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data
        })


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if refresh_token:
            try:
                RefreshToken(refresh_token).blacklist()
            except TokenError:
                pass
        return Response({'message': 'Logged out successfully'})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class MyRolesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_roles = (
            UserRole.objects
            .filter(user=request.user)
            .select_related('role', 'assigned_by')
            .prefetch_related('role__permissions')
        )
        return Response(MyRoleSerializer(user_roles, many=True).data)


class MyDirectPermissionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        perms = (
            UserDirectPermission.objects
            .filter(user=request.user)
            .select_related('permission', 'assigned_by')
        )
        return Response(UserDirectPermissionSerializer(perms, many=True).data)


class InviteUserView(APIView):
    permission_classes = [IsSuperAdmin]
    throttle_classes = [InviteThrottle]

    def post(self, request):
        serializer = InviteUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        role = serializer.validated_data.get('role', 'member')
        organization = serializer.validated_data.get('organization')

        if User.objects.filter(email=email).exists():
            return Response({'error': 'A user with this email already exists.'}, status=status.HTTP_400_BAD_REQUEST)

        UserInvitation.objects.filter(email=email, is_used=False).delete()
        invitation = UserInvitation.objects.create(
            email=email, role=role, organization=organization, invited_by=request.user
        )

        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
        invite_link = f"{frontend_url}/accept-invitation?token={invitation.token}"
        role_display = {'super_admin': 'Super Admin', 'admin': 'Admin', 'member': 'Member'}.get(role, role)
        org_name = organization.name if organization else 'RoleBase'

        try:
            send_mail(
                subject=f"You've been invited to join {org_name} on RoleBase",
                message=(
                    f"Hello,\n\n"
                    f"You have been invited to join RoleBase as a {role_display}"
                    f"{' in ' + org_name if organization else ''}.\n\n"
                    f"Click the link below to set up your account:\n{invite_link}\n\n"
                    f"This link expires in 7 days.\n\n"
                    f"- RoleBase Team"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
        except Exception as e:
            import traceback; traceback.print_exc()
            invitation.delete()
            return Response(
                {'error': f'Failed to send invitation email: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response({'message': f'Invitation sent to {email}'})


class AcceptInvitationView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        token = request.query_params.get('token')
        if not token:
            return Response({'error': 'Token is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            invitation = UserInvitation.objects.select_related('organization').get(token=token)
        except (UserInvitation.DoesNotExist, Exception):
            return Response({'error': 'Invalid invitation link'}, status=status.HTTP_404_NOT_FOUND)
        if not invitation.is_valid():
            return Response({'error': 'This invitation has expired or has already been used.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            'email': invitation.email,
            'role': invitation.role,
            'organization_name': invitation.organization.name if invitation.organization else None,
        })

    def post(self, request):
        serializer = AcceptInvitationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data['token']
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        try:
            invitation = UserInvitation.objects.select_related('organization').get(token=token)
        except (UserInvitation.DoesNotExist, Exception):
            return Response({'error': 'Invalid invitation link'}, status=status.HTTP_404_NOT_FOUND)
        if not invitation.is_valid():
            return Response({'error': 'This invitation has expired or has already been used.'}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(username=username).exists():
            return Response({'error': 'This username is already taken.'}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(email=invitation.email).exists():
            return Response({'error': 'An account with this email already exists.'}, status=status.HTTP_400_BAD_REQUEST)

        user = User(
            username=username,
            email=invitation.email,
            role=invitation.role,
            organization=invitation.organization,
        )
        user.set_password(password)
        user.save()

        invitation.is_used = True
        invitation.save()

        return Response({'message': 'Account created successfully. You can now log in.'})


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [PasswordResetThrottle]

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
        # JWT tokens are stateless and expire on their own (15 min access / 7 day refresh)
        return Response({'message': 'Password reset successfully. You can now log in.'})


# How many orgs each plan allows
MAX_ORGS_BY_PLAN = {'basic': 1, 'professional': 1, 'premium': 5}


# ─── ORGANIZATION VIEWSET ────────────────────────────────────────────────────

class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer

    def get_permissions(self):
        if self.action == 'toggle_recording':
            return [IsSuperAdmin()]
        return [IsAdminOrSuperAdmin()]

    def get_queryset(self):
        from django.db.models import Q
        user = self.request.user
        if not user.is_authenticated:
            return Organization.objects.none()
        if _is_platform_admin(user):
            return Organization.objects.all()
        if user.role in ('super_admin', 'admin'):
            # See all orgs they own, plus their currently active org
            q = Q(owner=user)
            if user.organization_id:
                q |= Q(id=user.organization_id)
            return Organization.objects.filter(q).distinct()
        return Organization.objects.none()

    def create(self, request, *args, **kwargs):
        user = request.user
        if _is_platform_admin(user):
            return super().create(request, *args, **kwargs)
        # Org admins: check plan limit before creating additional orgs
        primary = Organization.objects.filter(owner=user).order_by('created_at').first()
        if not primary:
            return Response(
                {'error': 'Complete subscription onboarding first to create organizations.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        max_orgs = MAX_ORGS_BY_PLAN.get(primary.plan, 1)
        owned_count = Organization.objects.filter(owner=user).count()
        if owned_count >= max_orgs:
            if primary.plan != 'premium':
                return Response(
                    {'error': f'Your {primary.plan.capitalize()} plan allows only 1 organization. Upgrade to Premium to create up to {MAX_ORGS_BY_PLAN["premium"]}.'},
                    status=status.HTTP_403_FORBIDDEN,
                )
            return Response(
                {'error': f'Premium plan allows up to {max_orgs} organizations. You have reached the limit.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        org = serializer.save(
            owner=user,
            plan=primary.plan,
            billing_cycle=primary.billing_cycle,
            stripe_customer_id=primary.stripe_customer_id,
            stripe_subscription_id=primary.stripe_subscription_id,
            stripe_metered_item_id=primary.stripe_metered_item_id,
            storage_included_mb=primary.storage_included_mb,
            can_use_recording=primary.can_use_recording,
            is_active=True,
        )
        return Response(self.get_serializer(org).data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        org = self.get_object()
        if not _is_platform_admin(request.user) and org.stripe_subscription_id:
            return Response(
                {'error': 'Cannot delete your primary organization. Cancel your subscription first.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def switch_org(self, request, pk=None):
        """Switch the requesting user's active organization to this one (must be owned by them)."""
        org = self.get_object()
        user = request.user
        if not _is_platform_admin(user) and org.owner_id != user.id:
            return Response({'error': 'You can only switch to organizations you own.'}, status=status.HTTP_403_FORBIDDEN)
        user.organization = org
        user.save(update_fields=['organization'])
        from .serializers import UserSerializer
        return Response(UserSerializer(user).data)

    @action(detail=True, methods=['post'], permission_classes=[IsSuperAdmin])
    def approve(self, request, pk=None):
        org = self.get_object()
        org.is_verified = True
        org.is_active = True
        org.save(update_fields=['is_verified', 'is_active'])
        return Response({'message': f'"{org.name}" has been approved. Members can now log in.'})

    @action(detail=True, methods=['post'], permission_classes=[IsSuperAdmin])
    def reject(self, request, pk=None):
        org = self.get_object()
        org.is_verified = False
        org.is_active = False
        org.save(update_fields=['is_verified', 'is_active'])
        return Response({'message': f'"{org.name}" has been rejected and deactivated.'})

    @action(detail=False, methods=['get'])
    def my_limits(self, request):
        """Returns org creation limits for the current user."""
        user = request.user
        if _is_platform_admin(user):
            return Response({'plan': 'platform', 'max_orgs': None, 'owned_count': 0, 'can_add_more': True})
        primary = Organization.objects.filter(owner=user).order_by('created_at').first()
        if not primary:
            return Response({'plan': None, 'max_orgs': 1, 'owned_count': 0, 'can_add_more': False})
        max_orgs = MAX_ORGS_BY_PLAN.get(primary.plan, 1)
        owned_count = Organization.objects.filter(owner=user).count()
        return Response({
            'plan': primary.plan,
            'max_orgs': max_orgs,
            'owned_count': owned_count,
            'can_add_more': owned_count < max_orgs,
        })

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

    @action(detail=True, methods=['post'], permission_classes=[IsSuperAdmin])
    def toggle_active(self, request, pk=None):
        org = self.get_object()
        org.is_active = not org.is_active
        org.save(update_fields=['is_active'])
        state = 'activated' if org.is_active else 'suspended'
        return Response({
            'message': f'"{org.name}" has been {state}.',
            'is_active': org.is_active,
        })

    @action(detail=True, methods=['post'], permission_classes=[IsSuperAdmin])
    def toggle_recording(self, request, pk=None):
        org = self.get_object()
        org.can_use_recording = not org.can_use_recording
        org.save()

        if org.can_use_recording:
            # Auto-create the org-scoped permission so the Admin can immediately
            # find it in the Permissions page and assign it to roles / users.
            AppPermission.objects.get_or_create(
                codename='use_video_transcription',
                organization=org,
                defaults={
                    'name': 'Use Video Transcription',
                    'description': (
                        f'Allows members of {org.name} to record screens '
                        'and receive AI-generated transcripts.'
                    ),
                    'created_by': request.user,
                },
            )

        state = 'enabled' if org.can_use_recording else 'disabled'
        return Response({
            'message': f'Screen recording {state} for {org.name}',
            'can_use_recording': org.can_use_recording,
        })
 
 
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
        if _is_platform_admin(user):
            return User.objects.all()
        if user.role == 'super_admin' and user.organization:
            return User.objects.filter(organization=user.organization)
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


def _check_owner(request, instance, label):
    """
    Super Admin can always edit/delete.
    Admin can only edit/delete objects they personally created.
    Returns a 403 Response if access is denied, otherwise None.
    """
    if request.user.role == 'super_admin':
        return None
    if instance.created_by_id != request.user.id:
        return Response(
            {'error': f'Only the creator or a Super Admin can edit or delete this {label}.'},
            status=status.HTTP_403_FORBIDDEN,
        )
    return None


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
        if _is_platform_admin(user):
            return AppPermission.objects.all()
        if user.role in ('super_admin', 'admin') and user.organization:
            return AppPermission.objects.filter(
                Q(organization=None) | Q(organization=user.organization)
            )
        return AppPermission.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if _is_platform_admin(user):
            serializer.save(created_by=user, organization=None)
        else:
            serializer.save(created_by=user, organization=user.organization)

    def update(self, request, *args, **kwargs):
        err = _check_owner(request, self.get_object(), 'permission')
        if err:
            return err
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        err = _check_owner(request, self.get_object(), 'permission')
        if err:
            return err
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
        if _is_platform_admin(user):
            return Role.objects.all().prefetch_related('permissions')
        if user.role in ('super_admin', 'admin', 'member') and user.organization:
            assigned_ids = UserRole.objects.filter(user=user).values_list('role_id', flat=True)
            return Role.objects.filter(
                Q(organization=None)
                | Q(organization=user.organization)
                | Q(id__in=assigned_ids)
            ).distinct().prefetch_related('permissions')
        return Role.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if _is_platform_admin(user):
            serializer.save(created_by=user)
        else:
            serializer.save(created_by=user, organization=user.organization)

    def update(self, request, *args, **kwargs):
        err = _check_owner(request, self.get_object(), 'role')
        if err:
            return err
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        err = _check_owner(request, self.get_object(), 'role')
        if err:
            return err
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def assign_permissions(self, request, pk=None):
        role = self.get_object()
        err = _check_owner(request, role, 'role')
        if err:
            return err
        permission_ids = request.data.get('permission_ids', [])
        permissions = AppPermission.objects.filter(id__in=permission_ids)
        role.permissions.set(permissions)
        return Response(RoleSerializer(role).data)


# ─── RECORDING VIEWSET ───────────────────────────────────────────────────────

class RecordingViewSet(viewsets.ModelViewSet):
    serializer_class = RecordingSerializer
    parser_classes = [MultiPartParser, FormParser]
    http_method_names = ['get', 'post', 'delete', 'head', 'options']

    def get_permissions(self):
        return [CanUseRecording()]

    def get_queryset(self):
        user = self.request.user
        if _is_platform_admin(user):
            return Recording.objects.all().order_by('-created_at')
        if user.role == 'super_admin' and user.organization:
            return Recording.objects.filter(organization=user.organization).order_by('-created_at')
        return Recording.objects.filter(user=user).order_by('-created_at')

    def create(self, request, *args, **kwargs):
        from .tasks import process_recording

        video_file = request.FILES.get('video')
        title = request.data.get('title', '').strip()
        if not video_file:
            return Response({'error': 'video file is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Save file immediately and return — processing happens in the background
        recording = Recording.objects.create(
            user=request.user,
            organization=request.user.organization,
            title=title or video_file.name,
            video_file=video_file,
            status=Recording.STATUS_PENDING,
        )

        # Fire-and-forget: Celery worker picks this up and processes asynchronously
        process_recording.delay(recording.id)

        serializer = self.get_serializer(recording)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# ─── DASHBOARD STATS ─────────────────────────────────────────────────────────

class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]
 
    def get(self, request):
        user = request.user
        if _is_platform_admin(user):
            return Response({
                'total_organizations': Organization.objects.count(),
                'total_users': User.objects.count(),
                'total_admins': User.objects.filter(role='admin').count(),
                'total_members': User.objects.filter(role='member').count(),
            })
        elif user.role == 'super_admin' and user.organization:
            org = user.organization
            return Response({
                'organization': org.name,
                'total_members': User.objects.filter(organization=org).count(),
                'admins_in_org': User.objects.filter(organization=org, role='admin').count(),
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


# ─── AI ONBOARDING ASSISTANT ─────────────────────────────────────────────────

SYSTEM_PROMPT = """You are RoleBase's friendly onboarding assistant. Help users choose the right plan and understand the platform. Keep answers short and clear (2-4 sentences max).

RoleBase Plans:
- Basic ($20/month or $16/month billed annually): Up to 20 users, custom roles & permissions, user invitations via email, password reset via OTP, 5GB storage.
- Professional ($32/month or $26/month billed annually): Everything in Basic + unlimited users, screen recording, AI transcription, PDF export, 20GB storage, 500MB per file.
- Premium ($80/month or $64/month billed annually): Everything in Professional + up to 5 organizations, audit logs, 2GB per file, custom branding, API access, priority support, 50GB storage.

Answer only questions about RoleBase features, plans, and onboarding. If asked anything unrelated, politely redirect to RoleBase topics."""


class OnboardingChatView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        import requests as http_requests
        user_message = request.data.get('message', '').strip()
        history      = request.data.get('history', [])

        if not user_message:
            return Response({'error': 'Message is required.'}, status=400)

        api_key = settings.HUGGINGFACE_API_KEY
        if not api_key:
            return Response({'error': 'AI service not configured.'}, status=500)

        try:
            resp = http_requests.post(
                'https://router.huggingface.co/together/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json',
                },
                json={
                    'model': 'meta-llama/Llama-3.3-70B-Instruct-Turbo',
                    'messages': [
                        {'role': 'system', 'content': SYSTEM_PROMPT},
                        *[{'role': m['role'], 'content': m['content']} for m in history[-6:]],
                        {'role': 'user', 'content': user_message},
                    ],
                    'max_tokens': 200,
                    'temperature': 0.6,
                },
                timeout=30,
            )
            resp.raise_for_status()
            result = resp.json()
            reply = result['choices'][0]['message']['content'].strip()
            return Response({'reply': reply})

        except http_requests.exceptions.Timeout:
            return Response({'error': 'AI service timed out. Please try again.'}, status=503)
        except Exception as e:
            return Response({'error': str(e)}, status=500)