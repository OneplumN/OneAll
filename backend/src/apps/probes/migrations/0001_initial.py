from __future__ import annotations

import uuid

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ProxyMapping',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('name', models.CharField(max_length=128, unique=True)),
                ('ip', models.GenericIPAddressField()),
                ('port', models.PositiveIntegerField(default=80)),
                ('heartbeat_interval_seconds', models.PositiveIntegerField(default=60)),
                ('status', models.CharField(default='active', max_length=32)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name='proxymapping_created', to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name='proxymapping_updated', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Proxy Mapping',
                'verbose_name_plural': 'Proxy Mappings',
                'db_table': 'probes_proxy_mapping',
                'ordering': ('-created_at',),
            },
        ),
        migrations.CreateModel(
            name='ProbeNode',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('name', models.CharField(max_length=128, unique=True)),
                ('location', models.CharField(max_length=128)),
                ('network_type', models.CharField(choices=[('internal', '内网'), ('external', '外网')], max_length=32)),
                ('supported_protocols', models.JSONField(blank=True, default=list)),
                ('status', models.CharField(choices=[('online', '在线'), ('offline', '离线'), ('maintenance', '维护')], default='offline', max_length=32)),
                ('last_heartbeat_at', models.DateTimeField(blank=True, null=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name='probenode_created', to=settings.AUTH_USER_MODEL)),
                ('proxy', models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name='probe_nodes', to='probes.proxymapping')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name='probenode_updated', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Probe Node',
                'verbose_name_plural': 'Probe Nodes',
                'db_table': 'probes_probe_node',
                'ordering': ('-created_at',),
            },
        ),
    ]
