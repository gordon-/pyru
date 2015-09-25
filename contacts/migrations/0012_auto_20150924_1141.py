# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0011_auto_20150923_1641'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='savedsearch',
            options={'verbose_name_plural': 'recherches sauvegardées', 'verbose_name': 'recherche sauvegardée', 'ordering': ['name'], 'permissions': (('view_savedsearch', 'Can view a saved search'),)},
        ),
        migrations.AddField(
            model_name='alert',
            name='creation_date',
            field=models.DateTimeField(verbose_name='date de création', auto_now_add=True, default=datetime.datetime(2015, 9, 24, 9, 41, 30, 944159, tzinfo=utc)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='alert',
            name='update_date',
            field=models.DateTimeField(verbose_name='date de mise à jour', default=datetime.datetime(2015, 9, 24, 9, 41, 36, 135, tzinfo=utc), auto_now=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='meeting',
            name='creation_date',
            field=models.DateTimeField(verbose_name='date de création', auto_now_add=True, default=datetime.datetime(2015, 9, 24, 9, 41, 40, 687772, tzinfo=utc)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='meeting',
            name='update_date',
            field=models.DateTimeField(verbose_name='date de mise à jour', default=datetime.datetime(2015, 9, 24, 9, 41, 45, 59091, tzinfo=utc), auto_now=True),
            preserve_default=False,
        ),
    ]
