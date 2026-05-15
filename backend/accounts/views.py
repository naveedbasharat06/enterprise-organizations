import os
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
        if user.role == 'super_admin':
            return Role.objects.all().prefetch_related('permissions')
        if user.role in ('admin', 'member') and user.organization:
            # Roles assigned directly to this user (by Super Admin or anyone)
            assigned_ids = UserRole.objects.filter(user=user).values_list('role_id', flat=True)
            return Role.objects.filter(
                Q(organization=None)           # global roles (Super Admin created)
                | Q(organization=user.organization)  # this org's roles
                | Q(id__in=assigned_ids)       # roles personally assigned to this user
            ).distinct().prefetch_related('permissions')
        return Role.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if user.role == 'admin':
            serializer.save(created_by=user, organization=user.organization)
        else:
            serializer.save(created_by=user)

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

def _extract_audio(video_path):
    """
    Extract compact mono audio from any video/audio file using the bundled ffmpeg binary.
    32 kbps mono MP3 at 16 kHz → ~12 MB/hour, well within Groq's 25 MB limit.
    """
    import subprocess
    import imageio_ffmpeg

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    audio_path = os.path.splitext(video_path)[0] + '_audio.mp3'

    # First probe whether the file actually has an audio stream
    probe = subprocess.run(
        [ffmpeg, '-i', video_path],
        capture_output=True, text=True
    )
    if 'Audio:' not in probe.stderr:
        raise ValueError(
            'This file has no audio track. '
            'For screen recordings, make sure to allow microphone access when recording.'
        )

    cmd = [
        ffmpeg, '-y',
        '-i', video_path,
        '-vn',           # drop video stream
        '-ac', '1',      # mono
        '-ar', '16000',  # 16 kHz — Whisper's native rate
        '-ab', '32k',    # 32 kbps → ~12 MB/hour
        audio_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise ValueError(f'Audio extraction failed: {result.stderr[-400:]}')
    return audio_path


def _transcribe_video(video_path):
    """Extract audio then transcribe via Groq's free Whisper API."""
    import openai

    api_key = getattr(settings, 'GROQ_API_KEY', '')
    if not api_key:
        raise ValueError('GROQ_API_KEY is not configured. Add it to your .env file.')

    audio_path = _extract_audio(video_path)
    try:
        client = openai.OpenAI(
            api_key=api_key,
            base_url='https://api.groq.com/openai/v1',
        )
        with open(audio_path, 'rb') as f:
            result = client.audio.transcriptions.create(
                model='whisper-large-v3',
                file=f,
                response_format='verbose_json',
                timestamp_granularities=['segment'],
            )
        return [
            {'start': seg.start, 'end': seg.end, 'text': seg.text.strip()}
            for seg in result.segments
        ]
    finally:
        if os.path.exists(audio_path):
            os.remove(audio_path)


def _format_timestamp(seconds):
    seconds = int(seconds)
    h, remainder = divmod(seconds, 3600)
    m, s = divmod(remainder, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def _group_segments(segments, interval=30):
    """
    Merge Whisper segments into blocks of ~`interval` seconds each.
    This avoids a new timestamp every 1-3 seconds (Whisper's natural segment size)
    and instead produces one paragraph per interval — matching how Rev, Otter.ai,
    and Zoom format their transcripts.
    """
    if not segments:
        return []
    groups = []
    block_start = segments[0]['start']
    block_texts = []
    for seg in segments:
        if seg['start'] - block_start >= interval and block_texts:
            groups.append({'start': block_start, 'text': ' '.join(block_texts)})
            block_start = seg['start']
            block_texts = []
        block_texts.append(seg['text'])
    if block_texts:
        groups.append({'start': block_start, 'text': ' '.join(block_texts)})
    return groups


def _generate_pdf(recording):
    """
    Build a professional timestamped transcript PDF — one timestamp per 30-second
    block, matching the format used by Rev.com, Otter.ai, and Zoom transcripts.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
    )

    ACCENT   = colors.HexColor('#6C63FF')
    GRAY     = colors.HexColor('#6B7280')
    LIGHT_BG = colors.HexColor('#F3F4F6')

    pdf_rel = f'transcripts/recording_{recording.id}.pdf'
    pdf_abs = os.path.join(settings.MEDIA_ROOT, pdf_rel)
    os.makedirs(os.path.dirname(pdf_abs), exist_ok=True)

    doc = SimpleDocTemplate(
        pdf_abs, pagesize=A4,
        leftMargin=22*mm, rightMargin=22*mm,
        topMargin=18*mm, bottomMargin=18*mm,
    )
    styles = getSampleStyleSheet()

    # ── custom paragraph styles ──────────────────────────────────────────────
    brand_style = ParagraphStyle(
        'Brand', parent=styles['Normal'],
        fontSize=9, textColor=ACCENT, fontName='Helvetica-Bold', spaceAfter=2,
    )
    title_style = ParagraphStyle(
        'Title', parent=styles['Normal'],
        fontSize=22, fontName='Helvetica-Bold', spaceAfter=4, leading=26,
    )
    meta_style = ParagraphStyle(
        'Meta', parent=styles['Normal'],
        fontSize=9, textColor=GRAY, leading=14,
    )
    section_style = ParagraphStyle(
        'Section', parent=styles['Normal'],
        fontSize=10, fontName='Helvetica-Bold', textColor=ACCENT,
        spaceBefore=14, spaceAfter=6,
    )
    ts_style = ParagraphStyle(
        'TS', parent=styles['Normal'],
        fontSize=8, fontName='Helvetica-Bold', textColor=ACCENT,
        spaceBefore=12, spaceAfter=2,
    )
    body_style = ParagraphStyle(
        'Body', parent=styles['Normal'],
        fontSize=11, leading=18, spaceAfter=0,
    )
    full_style = ParagraphStyle(
        'Full', parent=styles['Normal'],
        fontSize=11, leading=19, spaceAfter=0,
    )

    segments = (recording.transcript_data or {}).get('segments', [])
    groups   = _group_segments(segments, interval=30)
    full_text = ' '.join(s['text'] for s in segments)

    duration_secs = int(segments[-1]['end']) if segments else 0
    duration_str  = _format_timestamp(duration_secs)
    word_count    = len(full_text.split())

    story = []

    # ── header ───────────────────────────────────────────────────────────────
    story.append(Paragraph('RoleBase', brand_style))
    story.append(Paragraph(recording.title or 'Screen Recording', title_style))
    story.append(HRFlowable(width='100%', thickness=1, color=LIGHT_BG, spaceAfter=8))

    # metadata table
    meta_data = [
        ['Date', recording.created_at.strftime('%B %d, %Y  %H:%M UTC')],
        ['Recorded by', recording.user.username],
        ['Duration', duration_str],
        ['Word count', f'{word_count:,}'],
        ['Organization', recording.organization.name if recording.organization else '—'],
    ]
    tbl = Table(meta_data, colWidths=[35*mm, 120*mm])
    tbl.setStyle(TableStyle([
        ('FONTNAME',  (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE',  (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (0, -1), GRAY),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.black),
        ('TOPPADDING',    (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 10*mm))

    # ── timestamped transcript ────────────────────────────────────────────────
    story.append(Paragraph('TIMESTAMPED TRANSCRIPT', section_style))
    story.append(HRFlowable(width='100%', thickness=0.5, color=LIGHT_BG, spaceAfter=4))

    if not groups:
        story.append(Paragraph('No transcript data available.', body_style))
    else:
        for grp in groups:
            story.append(Paragraph(f"[{_format_timestamp(grp['start'])}]", ts_style))
            story.append(Paragraph(grp['text'], body_style))

    # ── full transcript (no timestamps) ──────────────────────────────────────
    story.append(Spacer(1, 10*mm))
    story.append(Paragraph('FULL TRANSCRIPT', section_style))
    story.append(HRFlowable(width='100%', thickness=0.5, color=LIGHT_BG, spaceAfter=6))
    story.append(Paragraph(full_text or 'No transcript data available.', full_style))

    doc.build(story)
    return pdf_rel


class RecordingViewSet(viewsets.ModelViewSet):
    serializer_class = RecordingSerializer
    parser_classes = [MultiPartParser, FormParser]
    http_method_names = ['get', 'post', 'delete', 'head', 'options']

    def get_permissions(self):
        return [CanUseRecording()]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'super_admin':
            return Recording.objects.all().order_by('-created_at')
        return Recording.objects.filter(user=user).order_by('-created_at')

    def create(self, request, *args, **kwargs):
        video_file = request.FILES.get('video')
        title = request.data.get('title', '').strip()
        if not video_file:
            return Response({'error': 'video file is required'}, status=status.HTTP_400_BAD_REQUEST)

        recording = Recording.objects.create(
            user=request.user,
            organization=request.user.organization,
            title=title or video_file.name,
            video_file=video_file,
            status=Recording.STATUS_PROCESSING,
        )

        try:
            segments = _transcribe_video(recording.video_file.path)
            recording.transcript_data = {'segments': segments}
            recording.pdf_file = _generate_pdf(recording)
            recording.status = Recording.STATUS_DONE
        except Exception as exc:
            recording.status = Recording.STATUS_FAILED
            recording.error_message = str(exc)

        recording.save()
        serializer = self.get_serializer(recording)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


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