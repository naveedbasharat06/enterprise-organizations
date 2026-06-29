from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0010_accessrequest'),
    ]

    operations = [
        migrations.CreateModel(
            name='OffboardingLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username_snapshot', models.CharField(max_length=150)),
                ('email_snapshot', models.CharField(blank=True, max_length=254)),
                ('roles_removed', models.JSONField(default=list)),
                ('permissions_removed', models.JSONField(default=list)),
                ('ai_summary', models.TextField(blank=True)),
                ('account_deactivated', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('offboarded_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='conducted_offboardings', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='offboarding_logs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
