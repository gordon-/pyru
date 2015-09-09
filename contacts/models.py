from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User, Group
from django.contrib.postgres import fields


PROP_CHOICES = (('company', 'compagnie'),
                ('contact', 'contact'),
                )

PRIORITIES = (('0', 'basse'),
              ('1', 'normale'),
              ('2', 'haute'),
              ('3', 'urgente'),
              )


class Properties(models.Model):
    name = models.CharField('nom', max_length=100)
    order = models.PositiveIntegerField('ordre', default=1)
    active = models.BooleanField('actif', default=True, db_index=True)
    type = models.CharField('type', max_length=16, choices=PROP_CHOICES)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'propriété'
        unique_together = (('name', 'type'), )
        ordering = ['order']
        permissions = (('view_property', 'Can view a property'), )


class Alert(models.Model):
    user = models.ForeignKey(User, verbose_name='utilisateur',
                             related_name='alerts')
    contact = models.ForeignKey('Contact', verbose_name='contact', null=True,
                                related_name='alerts')
    priority = models.CharField('priorité', max_length=1, choices=PRIORITIES,
                                default=PRIORITIES[0][0])
    date = models.DateTimeField('date', default=timezone.now)
    title = models.CharField('titre', max_length=100)
    comments = models.TextField('commentaires', blank=True)
    done = models.BooleanField('achevé', default=False, db_index=True)
    author = models.ForeignKey(User, verbose_name='créateur',
                               related_name='added_alerts')

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('contacts:alert-detail', kwargs={'pk': self.pk})

    @classmethod
    def get_queryset(cls, user):
        return cls.objects.filter(user=user)

    def is_owned(self, user, perm=None):
        return self.user == user or self.author == user

    class Meta:
        verbose_name = 'alerte'
        get_latest_by = 'date'
        ordering = ['-date']
        permissions = (('view_alert', 'Can view an alert'), )


class ContactType(models.Model):
    name = models.CharField('type', max_length=100, unique=True)
    active = models.BooleanField('actif', default=True, db_index=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'type de contact'
        verbose_name_plural = 'types de contact'
        ordering = ['name']
        permissions = (('view_contacttype', 'Can view a contact type'), )


class Company(models.Model):
    name = models.CharField('nom', max_length=100)
    slug = models.SlugField(unique=True)
    group = models.ForeignKey(Group, verbose_name='groupe',
                              related_name='companies')
    type = models.ForeignKey(ContactType, verbose_name='type', null=True,
                             related_name='companies')
    comments = models.TextField('commentaires', blank=True)
    properties = fields.HStoreField('propriétés', default={})
    creation_date = models.DateTimeField('date de création', auto_now_add=True)
    update_date = models.DateTimeField('date de mise à jour', auto_now=True)
    active = models.BooleanField('actif', default=True, db_index=True)
    author = models.ForeignKey(User, verbose_name='créateur',
                               related_name='added_companies')

    def __str__(self):
        return self.name

    def meetings(self):
        return Meeting.objects.filter(contact__company=self)

    def last_meetings(self):
        return Meeting.objects.filter(contact__company=self)[:5]

    def active_alerts(self):
        return Alert.objects.filter(contact__company=self, done=False,
                                    date__gt=timezone.now())

    def get_absolute_url(self):
        return reverse('contacts:company-detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        return super().save(*args, **kwargs)

    @classmethod
    def get_queryset(cls, user):
        return cls.objects.filter(group__in=user.groups.all())

    def is_owned(self, user, perm=None):
        return self.group in user.groups.all()

    class Meta:
        verbose_name = 'société'
        get_latest_by = 'update_date'
        ordering = ['name']
        permissions = (('view_company', 'Can view a company'), )


class Contact(models.Model):
    firstname = models.CharField('prénom', max_length=100)
    lastname = models.CharField('nom', max_length=100, blank=True)
    slug = models.SlugField(unique=True)
    company = models.ForeignKey(Company, verbose_name='société', null=True,
                                related_name='contacts')
    group = models.ForeignKey(Group, verbose_name='groupe',
                              related_name='contacts')
    type = models.ForeignKey(ContactType, verbose_name='type', null=True,
                             related_name='contacts')
    comments = models.TextField('commentaires', blank=True)
    properties = fields.HStoreField('propriétés', default={})
    creation_date = models.DateTimeField('date de création', auto_now_add=True)
    update_date = models.DateTimeField('date de mise à jour', auto_now=True)
    active = models.BooleanField('actif', default=True, db_index=True)
    author = models.ForeignKey(User, verbose_name='créateur',
                               related_name='added_contacts')

    def __str__(self):
        return '{} {}'.format(self.firstname, self.lastname)

    def get_absolute_url(self):
        return reverse('contacts:contact-detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify('{} {}'.format(self.firstname, self.lastname))
        return super().save(*args, **kwargs)

    @classmethod
    def get_queryset(cls, user):
        return cls.objects.filter(group__in=user.groups.all())

    def is_owned(self, user, perm=None):
        return self.group in user.groups.all()

    class Meta:
        verbose_name = 'contact'
        get_latest_by = 'update_date'
        ordering = ['firstname', 'lastname']
        permissions = (('view_contact', 'Can view a contact'), )


class MeetingType(models.Model):
    name = models.CharField('type', max_length=100, unique=True)
    active = models.BooleanField('actif', default=True, db_index=True),

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'type de rencontre'
        verbose_name_plural = 'types de rencontre'
        ordering = ['name']
        permissions = (('view_meetingtype', 'Can view a meeting type'), )


class Meeting(models.Model):
    contact = models.ForeignKey(Contact, verbose_name='contact',
                                related_name='meetings')
    type = models.ForeignKey(MeetingType, verbose_name='type')
    date = models.DateTimeField('date et heure', default=timezone.now)
    comments = models.TextField('commentaires', blank=True)
    author = models.ForeignKey(User, verbose_name='créateur',
                               related_name='added_meetings')

    def __str__(self):
        return 'Rencontre avec {contact}'.format(contact=self.contact)

    def get_absolute_url(self):
        return reverse('contacts:meeting-detail', kwargs={'pk': self.pk})

    @classmethod
    def get_queryset(cls, user):
        return cls.objects.filter(contact__group__in=user.groups.all())

    def is_owned(self, user, perm=None):
        return self.contact.group in user.groups.all()

    class Meta:
        verbose_name = 'rencontre'
        get_latest_by = 'date'
        ordering = ['-date']
        permissions = (('view_meeting', 'Can view a meeting'), )
