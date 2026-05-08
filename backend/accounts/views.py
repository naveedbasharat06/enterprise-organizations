from django.contrib.auth import authenticate
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated, AllowAny
 
from .models import User, Organization
from .serializers import UserSerializer, OrganizationSerializer, LoginSerializer
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