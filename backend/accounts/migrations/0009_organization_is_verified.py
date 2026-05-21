from django.db import migrations, models


def verify_existing_orgs(apps, schema_editor):
    """All orgs created before this migration are platform-admin-created — mark them verified."""
    Organization = apps.get_model('accounts', 'Organization')
    Organization.objects.all().update(is_verified=True)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0008_organization_owner'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='is_verified',
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(verify_existing_orgs, migrations.RunPython.noop),
    ]
