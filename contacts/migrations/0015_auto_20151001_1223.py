# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0014_savedsearch_display_in_menu'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='meeting',
            options={'permissions': (('view_meeting', 'Can view a meeting'),), 'ordering': ['-date'], 'get_latest_by': 'date', 'verbose_name': 'échange'},
        ),
        migrations.AlterModelOptions(
            name='meetingtype',
            options={'verbose_name_plural': 'types d’échange', 'permissions': (('view_meetingtype', 'Can view a meeting type'),), 'ordering': ['name'], 'verbose_name': 'type d’échange'},
        ),
        migrations.AlterField(
            model_name='savedsearch',
            name='type',
            field=models.CharField(max_length=32, choices=[('Contact', 'contact'), ('Company', 'société'), ('Meeting', 'échange'), ('Alert', 'alerte')], verbose_name='type'),
        ),
    ]
