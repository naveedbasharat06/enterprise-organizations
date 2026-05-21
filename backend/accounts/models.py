import random
import uuid
from datetime import timedelta
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class Organization(models.Model):
    # Industry / sector
    ORG_TYPE_TECHNOLOGY    = 'technology'
    ORG_TYPE_HEALTHCARE    = 'healthcare'
    ORG_TYPE_EDUCATION     = 'education'
    ORG_TYPE_FINANCE       = 'finance'
    ORG_TYPE_GOVERNMENT    = 'government'
    ORG_TYPE_RETAIL        = 'retail'
    ORG_TYPE_MANUFACTURING = 'manufacturing'
    ORG_TYPE_NONPROFIT     = 'nonprofit'
    ORG_TYPE_OTHER         = 'other'
    ORG_TYPE_CHOICES = [
        (ORG_TYPE_TECHNOLOGY,    'Technology'),
        (ORG_TYPE_HEALTHCARE,    'Healthcare'),
        (ORG_TYPE_EDUCATION,     'Education'),
        (ORG_TYPE_FINANCE,       'Finance'),
        (ORG_TYPE_GOVERNMENT,    'Government'),
        (ORG_TYPE_RETAIL,        'Retail'),
        (ORG_TYPE_MANUFACTURING, 'Manufacturing'),
        (ORG_TYPE_NONPROFIT,     'Non-Profit'),
        (ORG_TYPE_OTHER,         'Other'),
    ]

    # Organization size
    SIZE_SMALL      = 'small'
    SIZE_MEDIUM     = 'medium'
    SIZE_LARGE      = 'large'
    SIZE_ENTERPRISE = 'enterprise'
    ORG_SIZE_CHOICES = [
        (SIZE_SMALL,      'Small (1–50)'),
        (SIZE_MEDIUM,     'Medium (51–200)'),
        (SIZE_LARGE,      'Large (201–1000)'),
        (SIZE_ENTERPRISE, 'Enterprise (1000+)'),
    ]

    # Subscription plan
    PLAN_BASIC         = 'basic'
    PLAN_PROFESSIONAL  = 'professional'
    PLAN_PREMIUM       = 'premium'
    PLAN_CHOICES = [
        (PLAN_BASIC,        'Basic'),
        (PLAN_PROFESSIONAL, 'Professional'),
        (PLAN_PREMIUM,      'Premium'),
    ]

    # Billing cycle
    BILLING_MONTHLY = 'monthly'
    BILLING_ANNUAL  = 'annual'
    BILLING_CHOICES = [
        (BILLING_MONTHLY, 'Monthly'),
        (BILLING_ANNUAL,  'Annual'),
    ]

    # Storage included per plan (in MB)
    STORAGE_BY_PLAN = {
        PLAN_BASIC:        5 * 1024,    # 5 GB
        PLAN_PROFESSIONAL: 20 * 1024,   # 20 GB
        PLAN_PREMIUM:      50 * 1024,   # 50 GB
    }

    name              = models.CharField(max_length=255, unique=True)
    description       = models.TextField(blank=True)
    created_at        = models.DateTimeField(auto_now_add=True)
    is_active         = models.BooleanField(default=True)
    can_use_recording = models.BooleanField(default=False)

    # The admin user who created this org via Stripe onboarding
    owner = models.ForeignKey(
        'User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='owned_organizations'
    )

    # Classification
    org_type = models.CharField(max_length=50, choices=ORG_TYPE_CHOICES, default=ORG_TYPE_OTHER)
    org_size = models.CharField(max_length=20, choices=ORG_SIZE_CHOICES, blank=True)

    # Subscription
    plan          = models.CharField(max_length=20, choices=PLAN_CHOICES, default=PLAN_BASIC)
    billing_cycle = models.CharField(max_length=10, choices=BILLING_CHOICES, default=BILLING_MONTHLY)

    # Stripe references
    stripe_customer_id     = models.CharField(max_length=200, blank=True)
    stripe_subscription_id = models.CharField(max_length=200, blank=True)
    stripe_metered_item_id = models.CharField(max_length=200, blank=True)

    # Storage tracking
    storage_included_mb  = models.FloatField(default=5120)   # 5 GB default
    storage_used_mb      = models.FloatField(default=0)
    billing_period_start = models.DateTimeField(null=True, blank=True)
    billing_period_end   = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name

    def get_storage_included_mb(self):
        return self.STORAGE_BY_PLAN.get(self.plan, 5120)

    def storage_used_gb(self):
        return round(self.storage_used_mb / 1024, 2)

    def storage_included_gb(self):
        return round(self.storage_included_mb / 1024, 2)

    def storage_overage_gb(self):
        overage_mb = max(0, self.storage_used_mb - self.storage_included_mb)
        return round(overage_mb / 1024, 2)


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


class UserInvitation(models.Model):
    email = models.EmailField()
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    role = models.CharField(max_length=20, choices=User.ROLE_CHOICES, default=User.ROLE_MEMBER)
    organization = models.ForeignKey(
        Organization, on_delete=models.SET_NULL, null=True, blank=True
    )
    invited_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='sent_invitations'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_valid(self):
        return not self.is_used and timezone.now() < self.created_at + timedelta(days=7)

    def __str__(self):
        return f"Invitation for {self.email} ({self.role})"


class Recording(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_PROCESSING = 'processing'
    STATUS_DONE = 'done'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_PROCESSING, 'Processing'),
        (STATUS_DONE, 'Done'),
        (STATUS_FAILED, 'Failed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recordings')
    organization = models.ForeignKey(
        Organization, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='recordings'
    )
    title = models.CharField(max_length=255, blank=True)
    video_file = models.FileField(upload_to='recordings/')
    transcript_data = models.JSONField(null=True, blank=True)
    pdf_file = models.FileField(upload_to='transcripts/', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.title or 'Recording'}"


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


class StorageUsage(models.Model):
    FILE_RECORDING  = 'recording'
    FILE_TRANSCRIPT = 'transcript'
    FILE_TYPE_CHOICES = [
        (FILE_RECORDING,  'Recording'),
        (FILE_TRANSCRIPT, 'Transcript'),
    ]

    organization       = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='storage_usages')
    recording          = models.ForeignKey(Recording, on_delete=models.SET_NULL, null=True, blank=True, related_name='storage_usages')
    file_size_mb       = models.FloatField()
    file_type          = models.CharField(max_length=20, choices=FILE_TYPE_CHOICES)
    recorded_at        = models.DateTimeField(auto_now_add=True)
    reported_to_stripe = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.organization.name} — {self.file_size_mb:.2f} MB ({self.file_type})"


class PendingOnboarding(models.Model):
    token         = models.UUIDField(default=uuid.uuid4, unique=True)
    org_name      = models.CharField(max_length=255)
    org_type      = models.CharField(max_length=50)
    org_size      = models.CharField(max_length=20, blank=True)
    plan          = models.CharField(max_length=20)
    billing_cycle = models.CharField(max_length=10)
    username      = models.CharField(max_length=150)
    email         = models.EmailField()
    password_hash = models.CharField(max_length=255)
    stripe_session_id = models.CharField(max_length=300, blank=True)
    is_completed  = models.BooleanField(default=False)
    created_at    = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(hours=24)

    def __str__(self):
        return f"Pending: {self.org_name} ({self.email})"
