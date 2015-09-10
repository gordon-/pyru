# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0008_auto_20150909_2001'),
    ]

    operations = [
        migrations.AddField(
            model_name='contacttype',
            name='icon',
            field=models.CharField(blank=True, max_length=16, null=True, verbose_name='glyphicone'),
        ),
        migrations.AddField(
            model_name='meetingtype',
            name='icon',
            field=models.CharField(blank=True, max_length=16, null=True, verbose_name='glyphicone'),
        ),
    ]
