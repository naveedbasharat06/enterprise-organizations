from rest_framework import serializers
from .models import User, Organization, AppPermission, Role, UserRole, UserDirectPermission, UserInvitation, Recording, AccessRequest


class OrganizationSerializer(serializers.ModelSerializer):
    member_count        = serializers.SerializerMethodField()
    storage_used_gb     = serializers.SerializerMethodField()
    storage_included_gb = serializers.SerializerMethodField()
    storage_overage_gb  = serializers.SerializerMethodField()
    is_owner            = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = [
            'id', 'name', 'description', 'created_at', 'is_active', 'is_verified',
            'member_count', 'can_use_recording',
            'org_type', 'org_size', 'plan', 'billing_cycle',
            'storage_included_mb', 'storage_used_mb',
            'storage_used_gb', 'storage_included_gb', 'storage_overage_gb',
            'billing_period_start', 'billing_period_end',
            'owner', 'is_owner',
        ]
        read_only_fields = ['owner']

    def get_member_count(self, obj):
        return obj.members.count()

    def get_storage_used_gb(self, obj):
        return obj.storage_used_gb()

    def get_storage_included_gb(self, obj):
        return obj.storage_included_gb()

    def get_storage_overage_gb(self, obj):
        return obj.storage_overage_gb()

    def get_is_owner(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.owner_id == request.user.id


class UserSerializer(serializers.ModelSerializer):
    organization_name     = serializers.CharField(source='organization.name', read_only=True)
    org_recording_enabled = serializers.SerializerMethodField()
    org_plan              = serializers.SerializerMethodField()
    password              = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name',
                  'role', 'organization', 'organization_name', 'org_recording_enabled',
                  'org_plan', 'password', 'date_joined']
        read_only_fields = ['date_joined']

    def get_org_recording_enabled(self, obj):
        return obj.organization.can_use_recording if obj.organization else False

    def get_org_plan(self, obj):
        return obj.organization.plan if obj.organization else None

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField()
    new_password = serializers.CharField(min_length=8)


class InviteUserSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES, default=User.ROLE_MEMBER)
    organization = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.all(), required=False, allow_null=True
    )


class AcceptInvitationSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    username = serializers.CharField(min_length=3)
    password = serializers.CharField(min_length=8)


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    new_password = serializers.CharField(min_length=8)


class AppPermissionSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = AppPermission
        fields = ['id', 'name', 'codename', 'description',
                  'organization', 'organization_name',
                  'created_by', 'created_by_username', 'created_at']
        read_only_fields = ['created_by', 'created_at']


class RoleSerializer(serializers.ModelSerializer):
    permissions = AppPermissionSerializer(many=True, read_only=True)
    permission_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=AppPermission.objects.all(),
        source='permissions', write_only=True, required=False
    )
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    permission_count = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = [
            'id', 'name', 'description', 'organization', 'organization_name',
            'permissions', 'permission_ids', 'permission_count',
            'created_by', 'created_by_username', 'created_at'
        ]
        read_only_fields = ['created_by', 'created_at']

    def get_permission_count(self, obj):
        return obj.permissions.count()


class UserRoleSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source='role.name', read_only=True)
    role_id = serializers.IntegerField(source='role.id', read_only=True)
    assigned_by_username = serializers.CharField(source='assigned_by.username', read_only=True)

    class Meta:
        model = UserRole
        fields = ['id', 'role_id', 'role_name', 'assigned_by_username', 'assigned_at']


class MyRoleSerializer(serializers.ModelSerializer):
    role_id = serializers.IntegerField(source='role.id', read_only=True)
    role_name = serializers.CharField(source='role.name', read_only=True)
    role_description = serializers.CharField(source='role.description', read_only=True)
    assigned_by_username = serializers.CharField(source='assigned_by.username', read_only=True)
    permissions = AppPermissionSerializer(source='role.permissions', many=True, read_only=True)

    class Meta:
        model = UserRole
        fields = ['id', 'role_id', 'role_name', 'role_description',
                  'assigned_by_username', 'assigned_at', 'permissions']


class UserDirectPermissionSerializer(serializers.ModelSerializer):
    permission_name = serializers.CharField(source='permission.name', read_only=True)
    permission_codename = serializers.CharField(source='permission.codename', read_only=True)
    permission_id = serializers.IntegerField(source='permission.id', read_only=True)
    assigned_by_username = serializers.CharField(source='assigned_by.username', read_only=True)

    class Meta:
        model = UserDirectPermission
        fields = ['id', 'permission_id', 'permission_name', 'permission_codename',
                  'assigned_by_username', 'assigned_at']


class RecordingSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    pdf_url = serializers.SerializerMethodField()
    video_url = serializers.SerializerMethodField()

    class Meta:
        model = Recording
        fields = [
            'id', 'title', 'username', 'organization_name',
            'status', 'error_message', 'pdf_url', 'video_url',
            'transcript_data', 'created_at', 'updated_at',
        ]

    def get_pdf_url(self, obj):
        if obj.pdf_file:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.pdf_file.url) if request else obj.pdf_file.url
        return None

    def get_video_url(self, obj):
        if obj.video_file:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.video_file.url) if request else obj.video_file.url
        return None


class AccessRequestSerializer(serializers.ModelSerializer):
    username          = serializers.CharField(source='user.username', read_only=True)
    user_role         = serializers.CharField(source='user.role', read_only=True)
    role_name         = serializers.CharField(source='role.name', read_only=True)
    permission_name   = serializers.CharField(source='permission.name', read_only=True)
    reviewed_by_username = serializers.CharField(source='reviewed_by.username', read_only=True)

    class Meta:
        model  = AccessRequest
        fields = [
            'id', 'username', 'user_role', 'request_type',
            'role', 'role_name', 'permission', 'permission_name',
            'justification', 'status', 'ai_verdict', 'ai_reason',
            'reviewed_by_username', 'reviewed_at', 'created_at',
        ]
        read_only_fields = ['status', 'ai_verdict', 'ai_reason', 'reviewed_by', 'reviewed_at', 'created_at']
