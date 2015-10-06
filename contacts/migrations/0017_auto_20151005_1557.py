# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contacts', '0016_savedsearch_results_count'),
    ]

    operations = [
        migrations.AddField(
            model_name='contacttype',
            name='author',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='added_contact_types', default=1, verbose_name='créateur'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='contacttype',
            name='creation_date',
            field=models.DateTimeField(verbose_name='date de création', default=datetime.datetime(2015, 10, 5, 13, 56, 51, 315688, tzinfo=utc), auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='contacttype',
            name='update_date',
            field=models.DateTimeField(verbose_name='date de mise à jour', default=datetime.datetime(2015, 10, 5, 13, 56, 55, 293106, tzinfo=utc), auto_now=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='meetingtype',
            name='author',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='added_meeting_types', default=1, verbose_name='créateur'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='meetingtype',
            name='creation_date',
            field=models.DateTimeField(verbose_name='date de création', default=datetime.datetime(2015, 10, 5, 13, 57, 3, 807727, tzinfo=utc), auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='meetingtype',
            name='update_date',
            field=models.DateTimeField(verbose_name='date de mise à jour', default=datetime.datetime(2015, 10, 5, 13, 57, 9, 428479, tzinfo=utc), auto_now=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='properties',
            name='author',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='added_properties', default=1, verbose_name='créateur'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='properties',
            name='creation_date',
            field=models.DateTimeField(verbose_name='date de création', default=datetime.datetime(2015, 10, 5, 13, 57, 17, 244882, tzinfo=utc), auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='properties',
            name='update_date',
            field=models.DateTimeField(verbose_name='date de mise à jour', default=datetime.datetime(2015, 10, 5, 13, 57, 20, 736172, tzinfo=utc), auto_now=True),
            preserve_default=False,
        ),
    ]
