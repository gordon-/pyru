# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.postgres.fields.hstore


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
        ('contacts', '0010_properties_group'),
    ]

    operations = [
        migrations.CreateModel(
            name='SavedSearch',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('name', models.CharField(verbose_name='nom', max_length=32)),
                ('slug', models.SlugField(unique=True)),
                ('type', models.CharField(verbose_name='type', max_length=32, choices=[('Contact', 'contact'), ('Company', 'société'), ('Meeting', 'rencontre'), ('Alert', 'alerte')])),
                ('data', django.contrib.postgres.fields.hstore.HStoreField(default={}, verbose_name='données de recherche')),
                ('group', models.ForeignKey(verbose_name='groupe', to='auth.Group', related_name='searches')),
            ],
        ),
        migrations.AlterField(
            model_name='properties',
            name='type',
            field=models.CharField(verbose_name='type', max_length=16, choices=[('company', 'société'), ('contact', 'contact')]),
        ),
    ]
