from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres import fields


PROP_CHOICES = (('account', 'compte'),
                ('company', 'compagnie'),
                ('contact', 'contact'),
                )


class Account(models.Model):
    user = models.ForeignKey(User, verbose_name='utilisateur')
    properties = fields.HStoreField('propriétés', default={})


class Properties(models.Model):
    type = models.CharField('type', max_length=16, choices=PROP_CHOICES)


class Alert(models.Model):
    pass


class Company(models.Model):
    name = models.CharField()


class CompanyMeta(models.Model):
    pass


class Contact(models.Model):
    pass


class ContactMeta(models.Model):
    pass


class ContactType(models.Model):
    pass


class Meeting(models.Model):
    pass


class MeetingType(models.Model):
    pass
