# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0020_auto_20151013_1503'),
    ]

    operations = [
        migrations.AlterField(
            model_name='company',
            name='slug',
            field=models.SlugField(),
        ),
        migrations.AlterField(
            model_name='contact',
            name='slug',
            field=models.SlugField(),
        ),
        migrations.AlterField(
            model_name='savedsearch',
            name='slug',
            field=models.SlugField(),
        ),
        migrations.AlterUniqueTogether(
            name='company',
            unique_together=set([('slug', 'group')]),
        ),
        migrations.AlterUniqueTogether(
            name='contact',
            unique_together=set([('slug', 'group')]),
        ),
        migrations.AlterUniqueTogether(
            name='savedsearch',
            unique_together=set([('slug', 'group')]),
        ),
    ]
