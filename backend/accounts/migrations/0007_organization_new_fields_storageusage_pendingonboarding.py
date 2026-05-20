from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_organization_can_use_recording_recording'),
    ]

    operations = [
        # ── Organization new fields ──────────────────────────────────────────
        migrations.AddField(
            model_name='organization',
            name='org_type',
            field=models.CharField(
                choices=[
                    ('technology', 'Technology'), ('healthcare', 'Healthcare'),
                    ('education', 'Education'), ('finance', 'Finance'),
                    ('government', 'Government'), ('retail', 'Retail'),
                    ('manufacturing', 'Manufacturing'), ('nonprofit', 'Non-Profit'),
                    ('other', 'Other'),
                ],
                default='other', max_length=50,
            ),
        ),
        migrations.AddField(
            model_name='organization',
            name='org_size',
            field=models.CharField(
                blank=True,
                choices=[
                    ('small', 'Small (1–50)'), ('medium', 'Medium (51–200)'),
                    ('large', 'Large (201–1000)'), ('enterprise', 'Enterprise (1000+)'),
                ],
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='organization',
            name='plan',
            field=models.CharField(
                choices=[
                    ('basic', 'Basic'), ('professional', 'Professional'), ('premium', 'Premium'),
                ],
                default='basic', max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='organization',
            name='billing_cycle',
            field=models.CharField(
                choices=[('monthly', 'Monthly'), ('annual', 'Annual')],
                default='monthly', max_length=10,
            ),
        ),
        migrations.AddField(
            model_name='organization',
            name='stripe_customer_id',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='organization',
            name='stripe_subscription_id',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='organization',
            name='stripe_metered_item_id',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='organization',
            name='storage_included_mb',
            field=models.FloatField(default=5120),
        ),
        migrations.AddField(
            model_name='organization',
            name='storage_used_mb',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='organization',
            name='billing_period_start',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='organization',
            name='billing_period_end',
            field=models.DateTimeField(blank=True, null=True),
        ),

        # ── StorageUsage model ───────────────────────────────────────────────
        migrations.CreateModel(
            name='StorageUsage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('file_size_mb', models.FloatField()),
                ('file_type', models.CharField(
                    choices=[('recording', 'Recording'), ('transcript', 'Transcript')],
                    max_length=20,
                )),
                ('recorded_at', models.DateTimeField(auto_now_add=True)),
                ('reported_to_stripe', models.BooleanField(default=False)),
                ('organization', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='storage_usages',
                    to='accounts.organization',
                )),
                ('recording', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='storage_usages',
                    to='accounts.recording',
                )),
            ],
        ),

        # ── PendingOnboarding model ──────────────────────────────────────────
        migrations.CreateModel(
            name='PendingOnboarding',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('token', models.UUIDField(default=uuid.uuid4, unique=True)),
                ('org_name', models.CharField(max_length=255)),
                ('org_type', models.CharField(max_length=50)),
                ('org_size', models.CharField(blank=True, max_length=20)),
                ('plan', models.CharField(max_length=20)),
                ('billing_cycle', models.CharField(max_length=10)),
                ('username', models.CharField(max_length=150)),
                ('email', models.EmailField()),
                ('password_hash', models.CharField(max_length=255)),
                ('stripe_session_id', models.CharField(blank=True, max_length=300)),
                ('is_completed', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
