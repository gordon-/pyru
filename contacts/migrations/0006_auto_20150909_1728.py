# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0005_auto_20150904_1712'),
    ]

    operations = [
        migrations.AlterField(
            model_name='alert',
            name='priority',
            field=models.CharField(verbose_name='priorité', choices=[('0', 'basse'), ('1', 'normale'), ('2', 'haute'), ('3', 'urgente')], default='0', max_length=1),
        ),
    ]
