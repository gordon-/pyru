# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0003_auto_20150902_2303'),
    ]

    operations = [
        migrations.AlterField(
            model_name='company',
            name='comments',
            field=models.TextField(verbose_name='commentaires', blank=True),
        ),
        migrations.AlterField(
            model_name='contact',
            name='comments',
            field=models.TextField(verbose_name='commentaires', blank=True),
        ),
        migrations.AlterField(
            model_name='meeting',
            name='comments',
            field=models.TextField(verbose_name='commentaires', blank=True),
        ),
    ]
