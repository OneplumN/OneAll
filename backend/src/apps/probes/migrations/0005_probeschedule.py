from __future__ import annotations

import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('monitoring', '0003_alter_detectiontask_created_by_and_more'),
        ('probes', '0004_probenode_agent_config'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProbeSchedule',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('name', models.CharField(max_length=128)),
                ('description', models.TextField(blank=True)),
                ('target', models.CharField(max_length=512)),
                ('protocol', models.CharField(choices=[('HTTP', 'HTTP'), ('HTTPS', 'HTTPS'), ('Telnet', 'Telnet'), ('WSS', 'WebSocket Secure'), ('TCP', 'TCP'), ('CERTIFICATE', 'Certificate')], max_length=16)),
                ('frequency_minutes', models.PositiveIntegerField(default=5)),
                ('start_at', models.DateTimeField(blank=True, null=True)),
                ('end_at', models.DateTimeField(blank=True, null=True)),
                ('status', models.CharField(choices=[('active', 'Active'), ('paused', 'Paused'), ('archived', 'Archived')], default='active', max_length=16)),
                ('status_reason', models.CharField(blank=True, max_length=255)),
                ('source_type', models.CharField(choices=[('manual', 'Manual'), ('monitoring_request', 'Monitoring Request')], default='manual', max_length=32)),
                ('source_id', models.UUIDField(blank=True, null=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('last_run_at', models.DateTimeField(blank=True, null=True)),
                ('next_run_at', models.DateTimeField(blank=True, null=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='probeschedule_created', to=settings.AUTH_USER_MODEL)),
                ('monitoring_job', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='probe_schedule', to='monitoring.monitoringjob')),
                ('monitoring_request', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='probe_schedule', to='monitoring.monitoringrequest')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='probeschedule_updated', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Probe Schedule',
                'verbose_name_plural': 'Probe Schedules',
                'db_table': 'probes_probe_schedule',
                'ordering': ('name',),
            },
        ),
        migrations.AddField(
            model_name='probeschedule',
            name='probes',
            field=models.ManyToManyField(blank=True, related_name='schedules', to='probes.probenode'),
        ),
    ]
