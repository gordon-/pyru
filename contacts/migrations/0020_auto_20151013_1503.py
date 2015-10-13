# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contacts', '0019_auto_20151008_1604'),
    ]

    operations = [
        migrations.CreateModel(
            name='DefaultGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('group', models.ForeignKey(related_name='users_with_default', to='auth.Group')),
                ('user', models.OneToOneField(related_name='default_group', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'groupe par défaut',
                'verbose_name_plural': 'groupes par défaut',
            },
        ),
        migrations.AlterUniqueTogether(
            name='defaultgroup',
            unique_together=set([('user', 'group')]),
        ),
    ]
