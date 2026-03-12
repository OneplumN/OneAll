from __future__ import annotations

import uuid

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('probes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DetectionTask',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('target', models.CharField(max_length=512)),
                ('protocol', models.CharField(choices=[('HTTP', 'HTTP'), ('HTTPS', 'HTTPS'), ('Telnet', 'Telnet'), ('WSS', 'WebSocket Secure'), ('TCP', 'TCP'), ('CERTIFICATE', 'Certificate')], max_length=16)),
                ('status', models.CharField(choices=[('scheduled', 'Scheduled'), ('running', 'Running'), ('succeeded', 'Succeeded'), ('failed', 'Failed'), ('timeout', 'Timeout')], default='scheduled', max_length=32)),
                ('response_time_ms', models.PositiveIntegerField(blank=True, null=True)),
                ('status_code', models.CharField(blank=True, max_length=32)),
                ('error_message', models.TextField(blank=True)),
                ('result_payload', models.JSONField(blank=True, default=dict)),
                ('executed_at', models.DateTimeField(blank=True, null=True)),
                ('requested_by', models.UUIDField(blank=True, null=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name='detectiontask_created', to=settings.AUTH_USER_MODEL)),
                ('probe', models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name='detection_tasks', to='probes.probenode')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name='detectiontask_updated', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Detection Task',
                'verbose_name_plural': 'Detection Tasks',
                'db_table': 'monitoring_detection_task',
                'ordering': ('-created_at',),
            },
        ),
    ]
