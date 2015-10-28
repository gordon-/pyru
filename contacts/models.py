import sys
import logging
from datetime import datetime
from collections import OrderedDict

from django.db import models, transaction
from django.db.models import Q, options
from django.utils import timezone
from django.utils.text import slugify
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User, Group
from django.contrib.postgres import fields
from markdown import markdown
import bleach
from dateutil import parser

from .decorators import method_cache, classmethod_cache


options.DEFAULT_NAMES = options.DEFAULT_NAMES + ('words', 'order_mapping',
                                                 'select_related', )

PROP_CHOICES = (('company', 'société'),
                ('contact', 'contact'),
                )

PRIORITIES = (('0', 'basse'),
              ('1', 'normale'),
              ('2', 'haute'),
              ('3', 'urgente'),
              )

SEARCH_CHOICES = (('Contact', 'contact'),
                  ('Company', 'société'),
                  ('Meeting', 'échange'),
                  ('Alert', 'alerte'),
                  )

ALLOWED_TAGS = bleach.ALLOWED_TAGS + ['p', 'pre']


def apply_mapping(row, mapping):
    mapped_row = {}
    for k, v in mapping.items():
        if v not in row:
            raise DataImportError('valeur {} absente'.format(v))

    rev_mapping = {v: k for k, v in mapping.items()}
    for k, v in row.items():
        if k in rev_mapping:
            mapped_row[rev_mapping[k]] = v
        else:
            mapped_row[k] = v
    return mapped_row


def combine_rows(data, mapping):
    """ this filter function is designed for meetings imports from Saru.
    The files generated by Saru contains “FK-rows”, which references Contact
    objects, and “meeting-rows”, which only contains Meeting data, with empty
    Contact references.
    The goal is to create a flat list ofrows, each one containing the Contact
    and the Meeting.
    """
    combined = []
    fk_row = {}
    for row in data:
        # is this row a header (FK-row)?
        if row[mapping['firstname']] + row[mapping['lastname']] != '':
            fk_row = {mapping['firstname']: row[mapping['firstname']],
                      mapping['lastname']: row[mapping['lastname']],
                      mapping['company']: row[mapping['company']],
                      }
        else:
            row.update(fk_row)
            combined.append(row)
    if len(combined) == 0:
        return data
    return combined


class DataImportError(Exception):
    pass


class ImportCache:

    def __init__(self, model, user, logger, key='name'):
        self.model = model
        self.user = user
        self.group = user.default_group.group
        self.logger = logger
        self.key = key
        self.items = {}

    def get(self, item):
        if item is None or item == '':
            return None
        if isinstance(item, dict):
            item_hash = tuple(item.items())
        else:
            item_hash = item
        if item_hash not in self.items.keys():
            # TODO: check permissions!
            try:
                if isinstance(item, dict):
                    args = item
                else:
                    args = {self.key: item}
                obj = self.model.get_queryset(self.user)\
                    .get(**args)
                self.logger.debug('Récupération de {} : {}'
                                  .format(self.model._meta.verbose_name,
                                          obj))
            except self.model.DoesNotExist:
                if isinstance(item, dict):
                    args = item.copy()
                    args.update({'author': self.user,
                                 'group': self.group})
                else:
                    args = {self.key: item,
                            'author': self.user,
                            'group': self.group}
                obj = self.model.objects.create(**args)
                self.logger.info('Création de {} : {}'
                                 .format(self.model._meta.verbose_name, obj))
            # obj = self.model.objects.get_or_create(**args)
            self.items[item_hash] = obj
        return self.items[item_hash]


class DefaultGroup(models.Model):
    user = models.OneToOneField(User, related_name='default_group')
    group = models.ForeignKey(Group, related_name='users_with_default')

    def str(self):
        return self.group.name

    class Meta:
        verbose_name = 'groupe par défaut'
        verbose_name_plural = 'groupes par défaut'
        unique_together = (('user', 'group'), )
        select_related = ('group', )


class Properties(models.Model):
    name = models.CharField('nom', max_length=100)
    order = models.PositiveIntegerField('ordre', default=1)
    active = models.BooleanField('actif', default=True, db_index=True)
    type = models.CharField('type', max_length=16, choices=PROP_CHOICES)
    group = models.ForeignKey(Group, verbose_name='groupe',
                              related_name='properties')
    display_on_list = models.BooleanField('afficher dans les listes',
                                          default=False)
    author = models.ForeignKey(User, verbose_name='créateur',
                               related_name='added_properties')
    creation_date = models.DateTimeField('date de création', auto_now_add=True)
    update_date = models.DateTimeField('date de mise à jour', auto_now=True)

    def __str__(self):
        return self.name

    def is_owned(self, user, perm=None):
        return self.contact.group.id == user.default_group.group_id

    @classmethod
    def get_queryset(cls, user, qs=None):
        if qs is None:
            qs = cls.objects
        return qs.filter(group_id=user.default_group.group_id)

    @classmethod_cache(60)
    def get_displayed_names(cls, group, type):
        displayed = [p.name for p in
                     Properties.objects.filter(type=type,
                                               group=group,
                                               display_on_list=True)
                     .order_by('order')]
        return displayed

    class Meta:
        verbose_name = 'propriété'
        words = {'of': 'de ',
                 'of_a': 'd’une ',
                 'of_the': 'de la ',
                 'an': 'une',
                 }
        unique_together = (('name', 'group', 'type'), )
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
    creation_date = models.DateTimeField('date de création', auto_now_add=True)
    update_date = models.DateTimeField('date de mise à jour', auto_now=True)

    def __str__(self):
        return self.title

    def get_comments(self):
        return bleach.clean(bleach.linkify(markdown(self.comments)),
                            ALLOWED_TAGS)

    def get_glyphicon(self):
        return 'bell'

    def get_absolute_url(self):
        return reverse('contacts:alert-detail', kwargs={'pk': self.pk})

    @classmethod
    def get_queryset(cls, user, qs=None):
        if qs is None:
            qs = cls.objects
        return qs.filter((Q(user=user) | Q(author=user)) &
                         Q(contact__group_id=user.default_group.group_id))

    @classmethod
    def import_data(cls, data, mapping, format, user):
        logger = logging.getLogger('import.alert')
        logger.debug('Début de l’import d’alertes')
        company_cache = ImportCache(Company, user, logger)
        contact_cache = ImportCache(Contact, user, logger)
        imported_objects = {}
        errors = 0
        data = combine_rows(data, mapping)
        for row in data:
            try:
                with transaction.atomic():
                    row = apply_mapping(row, mapping)
                    args = {}
                    company = company_cache.get(row.pop('company'))
                    firstname = row.pop('firstname')
                    lastname = row.pop('lastname')
                    contact = contact_cache.get({'company': company,
                                                 'firstname': firstname,
                                                 'lastname': lastname})
                    args['contact'] = contact
                    args['title'] = row.pop('title', '')
                    args['comments'] = row.pop('comments')
                    args['priority'] = row.pop('priority', 0)
                    args['done'] = row.pop('done', 0)
                    date_str = row.pop('date')
                    try:
                        date = timezone.make_aware(
                            datetime.strptime(date_str, format))
                    except ValueError:
                        date = parser.parse(date_str)
                    args['date'] = date
                    args['author'] = user
                    args['user'] = user
                    alert = cls.objects.create(**args)
                    logger.info('Création d’alerte : {}'
                                .format(alert))
                    imported_objects[alert.pk] = alert
            except DataImportError as e:
                logger.error('Erreur lors de l’import de l’alerte : {}'
                             .format(e))
                errors += 1
            except Exception as e:
                logger.error('Erreur inattendue ({}) : {}'
                             .format(e.__class__.__name__, e))
                errors += 1
        logger.debug('Fin de l’import d’alertes ({} créés, '
                     '{} erreurs)'
                     .format(len(imported_objects),
                             errors))
        return (list(imported_objects.values()), [], errors)

    @classmethod
    def export_data(self, qs):
        export = []
        fields = {'title': None,
                  'firstname': 'contact__firstname',
                  'lastname': 'contact__lastname',
                  'company': 'contact__company__name',
                  'date': None,
                  'priority': None,
                  'done': None,
                  'comments': None,
                  }
        logger = logging.getLogger('export.alert')
        for obj in qs:
            logger.debug('Beginning export of alert {}'.format(obj))
            row = OrderedDict()
            for key, mapping in fields.items():
                if mapping is None:
                    row[key] = getattr(obj, key)
                else:
                    remaining_fields = mapping.split('__')
                    value = obj
                    while len(remaining_fields) >= 1:
                        try:
                            value = getattr(value, remaining_fields.pop(0))
                        except AttributeError:
                            value = ''
                    row[key] = value
                if isinstance(row[key], bool):
                    row[key] = int(row[key])
                elif hasattr(row[key], 'isoformat'):
                    row[key] = row[key].isoformat()
            export.append(row)

        return export

    def is_owned(self, user, perm=None):
        return self.user == user or self.author == user

    def is_near(self):
        now = timezone.now()
        return (self.date < now and not self.done) or\
            (self.date > now and (self.date - now).days < 1)

    class Meta:
        verbose_name = 'alerte'
        words = {'of': 'd’',
                 'of_a': 'd’une ',
                 'of_the': 'de l’',
                 'an': 'une',
                 }
        get_latest_by = 'date'
        ordering = ['-date']
        permissions = (('view_alert', 'Can view an alert'), )
        select_related = ('user', 'contact', 'contact__company', 'author', )


class ContactType(models.Model):
    name = models.CharField('type', max_length=100)
    active = models.BooleanField('actif', default=True, db_index=True)
    group = models.ForeignKey(Group, verbose_name='groupe',
                              related_name='contacttypes')
    icon = models.CharField('glyphicone', max_length=16, blank=True, null=True)
    author = models.ForeignKey(User, verbose_name='créateur',
                               related_name='added_contact_types')
    creation_date = models.DateTimeField('date de création', auto_now_add=True)
    update_date = models.DateTimeField('date de mise à jour', auto_now=True)

    def __str__(self):
        return self.name

    def is_owned(self, user, perm=None):
        return self.group.id == user.default_group.group_id

    @classmethod
    def get_queryset(cls, user, qs=None):
        if qs is None:
            qs = cls.objects
        return qs.filter(group_id=user.default_group.group_id)

    class Meta:
        verbose_name = 'type de contact'
        words = {'of': 'de ',
                 'of_a': 'd’un ',
                 'of_the': 'du ',
                 'an': 'un',
                 }
        verbose_name_plural = 'types de contact'
        ordering = ['name']
        permissions = (('view_contacttype', 'Can view a contact type'), )
        unique_together = (('name', 'group'), )


class Company(models.Model):
    name = models.CharField('nom', max_length=100)
    slug = models.SlugField()
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

    def get_comments(self):
        return bleach.clean(bleach.linkify(markdown(self.comments)),
                            ALLOWED_TAGS)

    @method_cache(60)
    def get_properties(self):
        props = Properties.objects.filter(type='company', group=self.group)\
            .only('name', 'order')
        props_order = {}
        for p in props:
            props_order[p.name] = p.order
        return {k: bleach.linkify(v, parse_email=True) for k, v in
                sorted(self.properties.items(),
                       key=lambda i: props_order.get(i, 0))}

    @method_cache(60)
    def get_displayed_properties(self):
        displayed = OrderedDict()
        props = Properties.objects.filter(type='company', group=self.group,
                                          display_on_list=True)\
            .only('name', 'order')
        props_order = {}
        for p in props:
            displayed[p.name] = ''
            props_order[p.name] = p.order
        for k, v in sorted(self.properties.items(),
                           key=lambda i: props_order.get(i, 0)):
            if k in displayed:
                displayed[k] = bleach.linkify(v, parse_email=True)
        return displayed

    def get_glyphicon(self):
        return 'briefcase'

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
            self.slug = slugify('{} {}'.format(self.group.pk, self.name))
        return super().save(*args, **kwargs)

    @classmethod
    def import_data(cls, data, mapping, properties, user):
        logger = logging.getLogger('import.company')
        logger.debug('Début de l’import de sociétés')
        type_cache = ImportCache(ContactType, user, logger)
        prop_cache = ImportCache(Properties, user, logger)
        imported_objects = {}
        updated_objects = {}
        errors = 0
        for row in data:
            try:
                with transaction.atomic():
                    row = apply_mapping(row, mapping)
                    if row['name'] != '':
                        args = {}
                        args['type'] = type_cache.get(row.pop('type'))
                        args['name'] = row.pop('name')
                        args['comments'] = row.pop('comments')
                        args['properties'] = {}
                        args['author'] = user
                        args['group'] = user.default_group.group
                        for prop, prop_value in row.items():
                            if prop is not None and\
                                    (properties is None or prop in properties):
                                prop_cache.get({'type': 'company',
                                                'name': prop})
                                args['properties'][prop] = prop_value
                        # do we have to create an object, or is there an
                        # existing one to update?
                        try:
                            contact = cls.get_queryset(user).get(
                                name=args['name'])
                            contact.properties.update(args['properties'])
                            contact.type = args['type']
                            contact.comments = args['comments']
                            contact.save()
                            updated_objects[contact.pk] = contact
                            logger.info('Modification de société : {}'
                                        .format(contact))
                        except cls.DoesNotExist:
                            contact = cls.objects.create(**args)
                            logger.info('Création de société : {}'
                                        .format(contact))
                            imported_objects[contact.pk] = contact
                    else:
                        logger.info('Société sans nom : on passe')
            except DataImportError as e:
                logger.error('Erreur lors de l’import de la société : {}'
                             .format(e))
                errors += 1
            except Exception as e:
                logger.error('Erreur inattendue ({}) : {}'
                             .format(e.__class__.__name__, e))
                errors += 1
        logger.debug('Fin de l’import de sociétés ({} créées, {} modifiées, '
                     '{} erreurs)'
                     .format(len(imported_objects), len(updated_objects),
                             errors))
        return (list(imported_objects.values()),
                list(updated_objects.values()), errors)

    @classmethod
    def export_data(self, qs):
        export = []
        fields = {'name': None,
                  'type': 'type__name',
                  'comments': None,
                  }
        logger = logging.getLogger('export.company')
        for obj in qs:
            logger.debug('Beginning export of company {}'.format(obj))
            row = OrderedDict()
            for key, mapping in fields.items():
                if mapping is None:
                    row[key] = getattr(obj, key)
                else:
                    remaining_fields = mapping.split('__')
                    value = obj
                    while len(remaining_fields) >= 1:
                        try:
                            value = getattr(value, remaining_fields.pop(0))
                        except AttributeError:
                            value = ''
                    row[key] = value
                if isinstance(row[key], bool):
                    row[key] = int(row[key])
                elif hasattr(row[key], 'isoformat'):
                    row[key] = row[key].isoformat()
            # properties fetch
            row.update(obj.properties)
            export.append(row)

        return export

    @classmethod
    def get_queryset(cls, user, qs=None):
        if qs is None:
            qs = cls.objects
        return qs.filter(group_id=user.default_group.group_id)

    def is_owned(self, user, perm=None):
        return self.group.id == user.default_group.group_id

    class Meta:
        verbose_name = 'société'
        words = {'of': 'de ',
                 'of_a': 'd’une ',
                 'of_the': 'de la ',
                 'an': 'une',
                 }
        get_latest_by = 'update_date'
        ordering = ['name']
        unique_together = (('slug', 'group'), )
        permissions = (('view_company', 'Can view a company'), )
        select_related = ('type', 'author', )


class Contact(models.Model):
    firstname = models.CharField('prénom', max_length=100)
    lastname = models.CharField('nom', max_length=100, blank=True)
    slug = models.SlugField()
    company = models.ForeignKey(Company, verbose_name='société', null=True,
                                blank=True, related_name='contacts')
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

    def get_comments(self):
        return bleach.clean(bleach.linkify(markdown(self.comments)),
                            ALLOWED_TAGS)

    @method_cache(60)
    def get_properties(self):
        props = Properties.objects.filter(type='contact', group=self.group)\
            .only('name', 'order')
        props_order = {}
        for p in props:
            props_order[p.name] = p.order
        return {k: bleach.linkify(v, parse_email=True) for k, v in
                sorted(self.properties.items(),
                       key=lambda i: props_order.get(i, 0))}

    @method_cache(60)
    def get_displayed_properties(self):
        displayed = OrderedDict()
        props = Properties.objects.filter(type='contact', group=self.group,
                                          display_on_list=True)\
            .only('name', 'order')
        props_order = {}
        for p in props:
            displayed[p.name] = ''
            props_order[p.name] = p.order
        for k, v in sorted(self.properties.items(),
                           key=lambda i: props_order.get(i, 0)):
            if k in displayed:
                displayed[k] = bleach.linkify(v, parse_email=True)
        return displayed

    def active_alerts(self):
        return Alert.objects.filter(contact=self, done=False,
                                    date__gt=timezone.now())

    def get_glyphicon(self):
        return 'user'

    def get_absolute_url(self):
        return reverse('contacts:contact-detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            company = '{} '.format(self.company) if self.company else ''
            self.slug = slugify('{}{} {}'.format(company, self.firstname,
                                                 self.lastname))
        return super().save(*args, **kwargs)

    @classmethod
    def import_data(cls, data, mapping, properties, user):
        logger = logging.getLogger('import.contact')
        logger.debug('Début de l’import de contacts')
        company_cache = ImportCache(Company, user, logger)
        type_cache = ImportCache(ContactType, user, logger)
        prop_cache = ImportCache(Properties, user, logger)
        imported_objects = {}
        updated_objects = {}
        errors = 0
        for row in data:
            try:
                with transaction.atomic():
                    row = apply_mapping(row, mapping)
                    if row['firstname'] != '' or row['lastname'] != '':
                        args = {}
                        args['company'] = company_cache.get(row.pop('company'))
                        args['type'] = type_cache.get(row.pop('type'))
                        args['firstname'] = row.pop('firstname')
                        args['lastname'] = row.pop('lastname')
                        args['comments'] = row.pop('comments')
                        args['properties'] = {}
                        args['author'] = user
                        args['group'] = user.default_group.group
                        for prop, prop_value in row.items():
                            if prop is not None and\
                                    (properties is None or prop in properties):
                                prop_cache.get({'type': 'contact',
                                                'name': prop})
                                args['properties'][prop] = prop_value
                        # do we have to create an object, or is there an
                        # existing one to update?
                        try:
                            contact = cls.get_queryset(user).get(
                                company=args['company'],
                                firstname=args['firstname'],
                                lastname=args['lastname'])
                            contact.properties.update(args['properties'])
                            contact.type = args['type']
                            contact.comments = args['comments']
                            contact.save()
                            updated_objects[contact.pk] = contact
                            logger.info('Modification de contact : {}'
                                        .format(contact))
                        except cls.DoesNotExist:
                            contact = cls.objects.create(**args)
                            logger.info('Création de contact : {}'
                                        .format(contact))
                            imported_objects[contact.pk] = contact
                        else:
                            logger.info('Contact sans nom : on passe')
            except DataImportError as e:
                logger.error('Erreur lors de l’import du contact : {}'
                             .format(e))
                errors += 1
            except Exception as e:
                logger.error('Erreur inattendue ({}) : {}'
                             .format(e.__class__.__name__, e))
                errors += 1
        logger.debug('Fin de l’import de contacts ({} créés, {} modifiés, '
                     '{} erreurs)'
                     .format(len(imported_objects), len(updated_objects),
                             errors))
        return (list(imported_objects.values()),
                list(updated_objects.values()), errors)

    @classmethod
    def export_data(self, qs):
        export = []
        fields = {'firstname': None,
                  'lastname': None,
                  'company': 'company__name',
                  'type': 'type__name',
                  'comments': None,
                  }
        logger = logging.getLogger('export.contact')
        for obj in qs:
            logger.debug('Beginning export of contact {}'.format(obj))
            row = OrderedDict()
            for key, mapping in fields.items():
                if mapping is None:
                    row[key] = getattr(obj, key)
                else:
                    remaining_fields = mapping.split('__')
                    value = obj
                    while len(remaining_fields) >= 1:
                        try:
                            value = getattr(value, remaining_fields.pop(0))
                        except AttributeError:
                            value = ''
                    row[key] = value
                if isinstance(row[key], bool):
                    row[key] = int(row[key])
                elif hasattr(row[key], 'isoformat'):
                    row[key] = row[key].isoformat()
            # properties fetch
            row.update(obj.properties)
            export.append(row)

        return export

    @classmethod
    def get_queryset(cls, user, qs=None):
        if qs is None:
            qs = cls.objects
        return qs.filter(group_id=user.default_group.group_id)

    def is_owned(self, user, perm=None):
        return self.group.id == user.default_group.group_id

    class Meta:
        verbose_name = 'contact'
        words = {'of': 'de ',
                 'of_a': 'd’un ',
                 'of_the': 'du ',
                 'an': 'un',
                 }
        get_latest_by = 'update_date'
        ordering = ['firstname', 'lastname']
        unique_together = (('slug', 'group'), )
        permissions = (('view_contact', 'Can view a contact'), )
        select_related = ('company', 'type', 'author', )


class MeetingType(models.Model):
    name = models.CharField('type', max_length=100)
    active = models.BooleanField('actif', default=True, db_index=True),
    group = models.ForeignKey(Group, verbose_name='groupe',
                              related_name='meetingtypes')
    icon = models.CharField('glyphicone', max_length=16, blank=True, null=True)
    author = models.ForeignKey(User, verbose_name='créateur',
                               related_name='added_meeting_types')
    creation_date = models.DateTimeField('date de création', auto_now_add=True)
    update_date = models.DateTimeField('date de mise à jour', auto_now=True)

    def __str__(self):
        return self.name

    def is_owned(self, user, perm=None):
        return self.group.id == user.default_group.group_id

    @classmethod
    def get_queryset(cls, user, qs=None):
        if qs is None:
            qs = cls.objects
        return qs.filter(group_id=user.default_group.group_id)

    class Meta:
        verbose_name = 'type d’échange'
        words = {'of': 'de ',
                 'of_a': 'd’un ',
                 'of_the': 'du ',
                 'an': 'un',
                 }
        verbose_name_plural = 'types d’échange'
        ordering = ['name']
        permissions = (('view_meetingtype', 'Can view a meeting type'), )
        unique_together = (('name', 'group'), )


class Meeting(models.Model):
    contact = models.ForeignKey(Contact, verbose_name='contact',
                                related_name='meetings')
    type = models.ForeignKey(MeetingType, verbose_name='type')
    date = models.DateTimeField('date et heure', default=timezone.now)
    comments = models.TextField('commentaires', blank=True)
    author = models.ForeignKey(User, verbose_name='créateur',
                               related_name='added_meetings')
    creation_date = models.DateTimeField('date de création', auto_now_add=True)
    update_date = models.DateTimeField('date de mise à jour', auto_now=True)

    def __str__(self):
        return str(self.contact)

    def get_comments(self):
        return bleach.clean(bleach.linkify(markdown(self.comments)),
                            ALLOWED_TAGS)

    def get_glyphicon(self):
        return self.type.icon

    def get_absolute_url(self):
        return reverse('contacts:meeting-detail', kwargs={'pk': self.pk})

    @classmethod
    def get_queryset(cls, user, qs=None):
        if qs is None:
            qs = cls.objects
        return qs.filter(contact__group_id=user.default_group.group_id)

    def is_owned(self, user, perm=None):
        return self.contact.group.id == user.default_group.group_id

    @classmethod
    def import_data(cls, data, mapping, format, user):
        logger = logging.getLogger('import.meeting')
        logger.debug('Début de l’import d’échanges')
        company_cache = ImportCache(Company, user, logger)
        contact_cache = ImportCache(Contact, user, logger)
        type_cache = ImportCache(MeetingType, user, logger)
        imported_objects = {}
        errors = 0
        data = combine_rows(data, mapping)
        for row in data:
            try:
                with transaction.atomic():
                    row = apply_mapping(row, mapping)
                    args = {}
                    company = company_cache.get(row.pop('company'))
                    args['type'] = type_cache.get(row.pop('type'))
                    firstname = row.pop('firstname')
                    lastname = row.pop('lastname')
                    contact = contact_cache.get({'company': company,
                                                 'firstname': firstname,
                                                 'lastname': lastname})
                    args['contact'] = contact
                    args['comments'] = row.pop('comments')
                    date_str = row.pop('date')
                    try:
                        date = timezone.make_aware(
                            datetime.strptime(date_str, format))
                    except ValueError:
                        date = parser.parse(date_str)
                    args['date'] = date
                    args['author'] = user
                    meeting = cls.objects.create(**args)
                    logger.info('Création d’échange : {}'
                                .format(meeting))
                    imported_objects[meeting.pk] = meeting
            except DataImportError as e:
                logger.error('Erreur lors de l’import de l’échange : {}'
                             .format(e))
                errors += 1
            except Exception as e:
                logger.error('Erreur inattendue ({}) : {}'
                             .format(e.__class__.__name__, e))
                errors += 1
        logger.debug('Fin de l’import d’échanges ({} créés, '
                     '{} erreurs)'
                     .format(len(imported_objects),
                             errors))
        return (list(imported_objects.values()), [], errors)

    @classmethod
    def export_data(self, qs):
        export = []
        fields = {'firstname': 'contact__firstname',
                  'lastname': 'contact__lastname',
                  'company': 'contact__company__name',
                  'type': 'type__name',
                  'date': None,
                  'comments': None,
                  }
        logger = logging.getLogger('export.meeting')
        for obj in qs:
            logger.debug('Beginning export of meeting {}'.format(obj))
            row = OrderedDict()
            for key, mapping in fields.items():
                if mapping is None:
                    row[key] = getattr(obj, key)
                else:
                    remaining_fields = mapping.split('__')
                    value = obj
                    while len(remaining_fields) >= 1:
                        try:
                            value = getattr(value, remaining_fields.pop(0))
                        except AttributeError:
                            value = ''
                    row[key] = value
                if isinstance(row[key], bool):
                    row[key] = int(row[key])
                elif hasattr(row[key], 'isoformat'):
                    row[key] = row[key].isoformat()
            export.append(row)

        return export

    class Meta:
        verbose_name = 'échange'
        words = {'of': 'd’',
                 'of_a': 'd’un ',
                 'of_the': 'de l’',
                 'an': 'un',
                 }
        get_latest_by = 'date'
        ordering = ['-date']
        order_mapping = {'company': 'contact__company__name'}
        permissions = (('view_meeting', 'Can view a meeting'), )
        select_related = ('contact', 'contact__company', 'type', 'author', )


class SavedSearch(models.Model):
    group = models.ForeignKey(Group, verbose_name='groupe',
                              related_name='searches')
    name = models.CharField('nom', max_length=32)
    slug = models.SlugField()
    type = models.CharField('type', max_length=32, choices=SEARCH_CHOICES)
    display_in_menu = models.BooleanField('affichage dans le menu',
                                          default=True)
    data = fields.HStoreField('données de recherche', default={})
    author = models.ForeignKey(User, verbose_name='créateur',
                               related_name='saved_searches')
    results_count = models.PositiveIntegerField('nombre de résultats',
                                                default=0)
    creation_date = models.DateTimeField('date de création', auto_now_add=True)
    update_date = models.DateTimeField('date de mise à jour', auto_now=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('contacts:search-detail',
                       kwargs={'slug': self.slug})

    def get_search_model(self):
        return getattr(sys.modules[__name__], self.type)

    @classmethod
    def get_queryset(cls, user, qs=None):
        if qs is None:
            qs = cls.objects
        return qs.filter(group_id=user.default_group.group_id)

    def is_owned(self, user, perm=None):
        return self.group.id == user.default_group.group_id

    def get_search_queryset(self, user):
        from . import forms
        model = self.get_search_model()
        if hasattr(model, 'get_queryset'):
            qs = model.get_queryset(user)
        else:
            qs = model.objects.all()
        form_class = getattr(forms, '{}SearchForm'.format(self.type))
        form = form_class(data=self.data)
        qs = form.search(qs)
        self.results_count = qs.count()
        self.save()
        return qs

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        return super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'recherche sauvegardée'
        words = {'of': 'de ',
                 'of_a': 'd’une ',
                 'of_the': 'de la ',
                 'an': 'une',
                 }
        verbose_name_plural = 'recherches sauvegardées'
        ordering = ['name']
        unique_together = (('slug', 'group'), )
        permissions = (('view_savedsearch', 'Can view a saved search'), )
