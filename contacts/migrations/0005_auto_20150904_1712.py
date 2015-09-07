# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0004_auto_20150903_1726'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='alert',
            options={'ordering': ['-date'], 'permissions': (('view_alert', 'Can view an alert'),), 'verbose_name': 'alerte', 'get_latest_by': 'date'},
        ),
        migrations.AlterModelOptions(
            name='company',
            options={'ordering': ['name'], 'permissions': (('view_company', 'Can view a company'),), 'verbose_name': 'société', 'get_latest_by': 'update_date'},
        ),
        migrations.AlterModelOptions(
            name='contact',
            options={'ordering': ['firstname', 'lastname'], 'permissions': (('view_contact', 'Can view a contact'),), 'verbose_name': 'contact', 'get_latest_by': 'update_date'},
        ),
        migrations.AlterModelOptions(
            name='contacttype',
            options={'verbose_name_plural': 'types de contact', 'permissions': (('view_contacttype', 'Can view a contact type'),), 'verbose_name': 'type de contact', 'ordering': ['name']},
        ),
        migrations.AlterModelOptions(
            name='meeting',
            options={'ordering': ['-date'], 'permissions': (('view_meeting', 'Can view a meeting'),), 'verbose_name': 'rencontre', 'get_latest_by': 'date'},
        ),
        migrations.AlterModelOptions(
            name='meetingtype',
            options={'verbose_name_plural': 'types de rencontre', 'permissions': (('view_meetingtype', 'Can view a meeting type'),), 'verbose_name': 'type de rencontre', 'ordering': ['name']},
        ),
        migrations.AlterModelOptions(
            name='properties',
            options={'ordering': ['order'], 'permissions': (('view_property', 'Can view a property'),), 'verbose_name': 'propriété'},
        ),
    ]
