# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0017_auto_20151005_1557'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contacttype',
            name='name',
            field=models.CharField(max_length=100, verbose_name='type'),
        ),
        migrations.AlterField(
            model_name='meetingtype',
            name='name',
            field=models.CharField(max_length=100, verbose_name='type'),
        ),
        migrations.AlterUniqueTogether(
            name='contacttype',
            unique_together=set([('name', 'group')]),
        ),
        migrations.AlterUniqueTogether(
            name='meetingtype',
            unique_together=set([('name', 'group')]),
        ),
    ]
