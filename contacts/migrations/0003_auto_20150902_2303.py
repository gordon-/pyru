# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0002_auto_20150902_2302'),
    ]

    operations = [
        migrations.AlterField(
            model_name='properties',
            name='type',
            field=models.CharField(verbose_name='type', choices=[('company', 'compagnie'), ('contact', 'contact')], max_length=16),
        ),
    ]
