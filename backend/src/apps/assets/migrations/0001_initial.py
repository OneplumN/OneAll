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
            name='AssetRecord',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                (
                    'source',
                    models.CharField(
                        choices=[('CMDB', 'CMDB'), ('Zabbix', 'Zabbix'), ('Prometheus', 'Prometheus'), ('IPMP', 'IPMP'), ('Manual', 'Manual')],
                        max_length=32,
                    ),
                ),
                ('external_id', models.CharField(max_length=128)),
                ('name', models.CharField(max_length=256)),
                ('system_name', models.CharField(blank=True, max_length=128)),
                ('owners', models.JSONField(blank=True, default=list)),
                ('contacts', models.JSONField(blank=True, default=list)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('synced_at', models.DateTimeField(auto_now=True)),
                ('sync_status', models.CharField(default='unknown', max_length=32)),
                (
                    'created_by',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name='assetrecord_created',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    'updated_by',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name='assetrecord_updated',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'verbose_name': 'Asset Record',
                'verbose_name_plural': 'Asset Records',
                'db_table': 'assets_asset_record',
                'ordering': ('-synced_at',),
                'unique_together': {('source', 'external_id')},
            },
        ),
    ]
