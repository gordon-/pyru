# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0021_auto_20151013_1712'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='properties',
            unique_together=set([('name', 'group', 'type')]),
        ),
    ]
