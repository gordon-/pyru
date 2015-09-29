# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0013_auto_20150928_1612'),
    ]

    operations = [
        migrations.AddField(
            model_name='savedsearch',
            name='display_in_menu',
            field=models.BooleanField(default=True, verbose_name='affichage dans le menu'),
        ),
    ]
