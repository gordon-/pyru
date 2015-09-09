# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
        ('contacts', '0007_alert_author'),
    ]

    operations = [
        migrations.AddField(
            model_name='contacttype',
            name='group',
            field=models.ForeignKey(to='auth.Group', default=1, related_name='contacttypes', verbose_name='groupe'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='meetingtype',
            name='group',
            field=models.ForeignKey(to='auth.Group', default=1, related_name='meetingtypes', verbose_name='groupe'),
            preserve_default=False,
        ),
    ]
