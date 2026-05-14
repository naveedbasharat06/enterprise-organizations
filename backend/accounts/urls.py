from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    LoginView, LogoutView, MeView,
    MyRolesView, MyDirectPermissionsView,
    InviteUserView, AcceptInvitationView,
    ForgotPasswordView, ResetPasswordConfirmView,
    OrganizationViewSet, UserViewSet, DashboardStatsView,
    AppPermissionViewSet, RoleViewSet, RecordingViewSet
)

router = DefaultRouter()
router.register(r'organizations', OrganizationViewSet)
router.register(r'users', UserViewSet)
router.register(r'permissions', AppPermissionViewSet, basename='apppermission')
router.register(r'roles', RoleViewSet)
router.register(r'recordings', RecordingViewSet, basename='recording')

urlpatterns = [
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('auth/me/', MeView.as_view(), name='me'),
    path('auth/me/roles/', MyRolesView.as_view(), name='my-roles'),
    path('auth/me/permissions/', MyDirectPermissionsView.as_view(), name='my-permissions'),
    path('auth/invite/', InviteUserView.as_view(), name='invite-user'),
    path('auth/accept-invitation/', AcceptInvitationView.as_view(), name='accept-invitation'),
    path('auth/forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('auth/reset-password-confirm/', ResetPasswordConfirmView.as_view(), name='reset-password-confirm'),
    path('dashboard/stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('', include(router.urls)),
]
