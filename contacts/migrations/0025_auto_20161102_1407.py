# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from django.core.management import call_command

fixture = 'group_permissions'


def load_fixture(apps, schema_editor):
    call_command('loaddata', fixture, app_label='contacts')


def unload_fixture(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0024_auto_20151020_1632'),
    ]

    operations = [
        migrations.RunPython(load_fixture, reverse_code=unload_fixture),
    ]
