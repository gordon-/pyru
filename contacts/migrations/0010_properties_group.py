# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
        ('contacts', '0009_auto_20150910_2158'),
    ]

    operations = [
        migrations.AddField(
            model_name='properties',
            name='group',
            field=models.ForeignKey(verbose_name='groupe', default=1, to='auth.Group', related_name='properties'),
            preserve_default=False,
        ),
    ]
