# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0022_auto_20151013_1719'),
    ]

    operations = [
        migrations.AddField(
            model_name='properties',
            name='display_on_list',
            field=models.BooleanField(verbose_name='afficher dans les listes', default=False),
        ),
    ]
