# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contacts', '0006_auto_20150909_1728'),
    ]

    operations = [
        migrations.AddField(
            model_name='alert',
            name='author',
            field=models.ForeignKey(default=1, related_name='added_alerts', to=settings.AUTH_USER_MODEL, verbose_name='créateur'),
            preserve_default=False,
        ),
    ]
