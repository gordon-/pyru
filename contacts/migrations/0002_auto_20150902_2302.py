# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='properties',
            options={'verbose_name': 'propriété'},
        ),
        migrations.AddField(
            model_name='contacttype',
            name='active',
            field=models.BooleanField(verbose_name='actif', default=True, db_index=True),
        ),
        migrations.AddField(
            model_name='properties',
            name='active',
            field=models.BooleanField(verbose_name='actif', default=True, db_index=True),
        ),
        migrations.AddField(
            model_name='properties',
            name='name',
            field=models.CharField(verbose_name='nom', max_length=100, default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='properties',
            name='order',
            field=models.PositiveIntegerField(verbose_name='ordre', default=1),
        ),
        migrations.AlterField(
            model_name='alert',
            name='done',
            field=models.BooleanField(verbose_name='achevé', default=False, db_index=True),
        ),
        migrations.AlterUniqueTogether(
            name='properties',
            unique_together=set([('name', 'type')]),
        ),
    ]
