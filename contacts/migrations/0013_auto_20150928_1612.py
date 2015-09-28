# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.utils.timezone import utc
import datetime
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contacts', '0012_auto_20150924_1141'),
    ]

    operations = [
        migrations.AddField(
            model_name='savedsearch',
            name='author',
            field=models.ForeignKey(verbose_name='créateur', related_name='saved_searches', default=1, to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='savedsearch',
            name='creation_date',
            field=models.DateTimeField(default=datetime.datetime(2015, 9, 28, 14, 12, 53, 839397, tzinfo=utc), verbose_name='date de création', auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='savedsearch',
            name='update_date',
            field=models.DateTimeField(default=datetime.datetime(2015, 9, 28, 14, 12, 59, 297499, tzinfo=utc), verbose_name='date de mise à jour', auto_now=True),
            preserve_default=False,
        ),
    ]
