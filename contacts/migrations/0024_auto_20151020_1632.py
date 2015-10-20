# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0023_properties_display_on_list'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contact',
            name='company',
            field=models.ForeignKey(verbose_name='société', to='contacts.Company', null=True, blank=True, related_name='contacts'),
        ),
    ]
