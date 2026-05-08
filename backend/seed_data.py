"""
Run this once after migrations to create initial super admin and sample data.
Usage: python seed_data.py
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from accounts.models import User, Organization

print("Seeding database...")

# Create Super Admin
if not User.objects.filter(username='superadmin').exists():
    User.objects.create_superuser(
        username='superadmin',
        email='superadmin@example.com',
        password='Admin@1234',
        role='super_admin'
    )
    print("✓ Super Admin created: superadmin / Admin@1234")

# Create Organizations
org1, _ = Organization.objects.get_or_create(name='Tech Corp', defaults={'description': 'Technology company'})
org2, _ = Organization.objects.get_or_create(name='Health Plus', defaults={'description': 'Healthcare organization'})
print(f"✓ Organizations created: {org1.name}, {org2.name}")

# Create Admin for org1
if not User.objects.filter(username='admin_tech').exists():
    u = User.objects.create_user(
        username='admin_tech', email='admin@techcorp.com',
        password='Admin@1234', role='admin', organization=org1
    )
    print(f"✓ Admin created: admin_tech / Admin@1234 (org: {org1.name})")

# Create Member
if not User.objects.filter(username='john_member').exists():
    u = User.objects.create_user(
        username='john_member', email='john@example.com',
        password='Admin@1234', role='member'
    )
    print(f"✓ Member created: john_member / Admin@1234")

print("\nSeeding complete!")
print("Login at http://localhost:5173 with above credentials")
