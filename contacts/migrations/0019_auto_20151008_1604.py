# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0018_auto_20151006_1210'),
    ]

    operations = [
        migrations.AlterField(
            model_name='savedsearch',
            name='results_count',
            field=models.PositiveIntegerField(default=0, verbose_name='nombre de résultats'),
        ),
    ]
