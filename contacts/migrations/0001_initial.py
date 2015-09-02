# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
from django.conf import settings
from django.contrib.postgres.operations import HStoreExtension
import django.contrib.postgres.fields.hstore


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('auth', '0006_require_contenttypes_0002'),
    ]

    operations = [
        HStoreExtension(),
        migrations.CreateModel(
            name='Alert',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('priority', models.CharField(verbose_name='priorité', max_length=1, choices=[('0', 'basse'), ('1', 'normale'), ('2', 'haute'), ('3', 'urgente')])),
                ('date', models.DateTimeField(verbose_name='date', default=django.utils.timezone.now)),
                ('title', models.CharField(verbose_name='titre', max_length=100)),
                ('comments', models.TextField(blank=True, verbose_name='commentaires')),
                ('done', models.BooleanField(verbose_name='achevé', default=False)),
            ],
            options={
                'verbose_name': 'alerte',
            },
        ),
        migrations.CreateModel(
            name='Company',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('name', models.CharField(verbose_name='nom', max_length=100)),
                ('slug', models.SlugField(unique=True)),
                ('comments', models.TextField(verbose_name='commentaires')),
                ('properties', django.contrib.postgres.fields.hstore.HStoreField(verbose_name='propriétés', default={})),
                ('creation_date', models.DateTimeField(verbose_name='date de création', auto_now_add=True)),
                ('update_date', models.DateTimeField(verbose_name='date de mise à jour', auto_now=True)),
                ('active', models.BooleanField(verbose_name='actif', default=True, db_index=True)),
                ('author', models.ForeignKey(verbose_name='créateur', related_name='added_companies', to=settings.AUTH_USER_MODEL)),
                ('group', models.ForeignKey(verbose_name='groupe', related_name='companies', to='auth.Group')),
            ],
            options={
                'verbose_name': 'société',
            },
        ),
        migrations.CreateModel(
            name='Contact',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('firstname', models.CharField(verbose_name='prénom', max_length=100)),
                ('lastname', models.CharField(blank=True, verbose_name='nom', max_length=100)),
                ('slug', models.SlugField(unique=True)),
                ('comments', models.TextField(verbose_name='commentaires')),
                ('properties', django.contrib.postgres.fields.hstore.HStoreField(verbose_name='propriétés', default={})),
                ('creation_date', models.DateTimeField(verbose_name='date de création', auto_now_add=True)),
                ('update_date', models.DateTimeField(verbose_name='date de mise à jour', auto_now=True)),
                ('active', models.BooleanField(verbose_name='actif', default=True, db_index=True)),
                ('author', models.ForeignKey(verbose_name='créateur', related_name='added_contacts', to=settings.AUTH_USER_MODEL)),
                ('company', models.ForeignKey(verbose_name='société', related_name='contacts', to='contacts.Company', null=True)),
                ('group', models.ForeignKey(verbose_name='groupe', related_name='contacts', to='auth.Group')),
            ],
            options={
                'verbose_name': 'contact',
            },
        ),
        migrations.CreateModel(
            name='ContactType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('name', models.CharField(unique=True, verbose_name='type', max_length=100)),
            ],
            options={
                'verbose_name_plural': 'types de contact',
                'verbose_name': 'type de contact',
            },
        ),
        migrations.CreateModel(
            name='Meeting',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('date', models.DateTimeField(verbose_name='date et heure', default=django.utils.timezone.now)),
                ('comments', models.TextField(verbose_name='commentaires')),
                ('author', models.ForeignKey(verbose_name='créateur', related_name='added_meetings', to=settings.AUTH_USER_MODEL)),
                ('contact', models.ForeignKey(verbose_name='contact', related_name='meetings', to='contacts.Contact')),
            ],
            options={
                'verbose_name': 'rencontre',
            },
        ),
        migrations.CreateModel(
            name='MeetingType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('name', models.CharField(unique=True, verbose_name='type', max_length=100)),
            ],
            options={
                'verbose_name_plural': 'types de rencontre',
                'verbose_name': 'type de rencontre',
            },
        ),
        migrations.CreateModel(
            name='Properties',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('type', models.CharField(verbose_name='type', max_length=16, choices=[('account', 'compte'), ('company', 'compagnie'), ('contact', 'contact')])),
            ],
        ),
        migrations.AddField(
            model_name='meeting',
            name='type',
            field=models.ForeignKey(verbose_name='type', to='contacts.MeetingType'),
        ),
        migrations.AddField(
            model_name='contact',
            name='type',
            field=models.ForeignKey(verbose_name='type', related_name='contacts', to='contacts.ContactType', null=True),
        ),
        migrations.AddField(
            model_name='company',
            name='type',
            field=models.ForeignKey(verbose_name='type', related_name='companies', to='contacts.ContactType', null=True),
        ),
        migrations.AddField(
            model_name='alert',
            name='contact',
            field=models.ForeignKey(verbose_name='contact', related_name='alerts', to='contacts.Contact', null=True),
        ),
        migrations.AddField(
            model_name='alert',
            name='user',
            field=models.ForeignKey(verbose_name='utilisateur', related_name='alerts', to=settings.AUTH_USER_MODEL),
        ),
    ]
