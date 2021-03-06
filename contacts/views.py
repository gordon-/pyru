import csv
from io import StringIO
import json
import operator
from functools import reduce

from django.http.response import HttpResponse
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect, resolve_url
from django.core.urlresolvers import reverse_lazy
from django import forms
from django.views.generic.edit import ModelFormMixin, FormView
from django.views.generic import ListView
from django.db import IntegrityError
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.models import Group
from django.forms.widgets import HiddenInput
import chardet

from . import generic
from .models import (
    Properties, Alert, Company, Contact, Meeting, SavedSearch, SEARCH_CHOICES
)
from .forms import (
    ContactSearchForm, CompanySearchForm, MeetingSearchForm, AlertSearchForm,
)


def reencode_data(reader, detection):
    """
    Iterates through a reader (a list of dicts) and re-encode each value, with
    encoding guessing.
    """
    data = []
    for row in reader:
        reencoded_row = {}
        for key, value in row.items():
            if key is not None and value is not None:
                det = chardet.detect(value.encode())
                if det['encoding'] != detection['encoding']\
                        and det['confidence'] > .5\
                        and detection['encoding'] != 'utf-8':
                    reencoded_row[key] = value.encode(
                        detection['encoding']).decode(det['encoding'])
                    # print('reencoding {} from {} to {} ({})'
                    #       .format(value, detection['encoding'],
                    #               det['encoding'], reencoded_row[key]))
                else:
                    reencoded_row[key] = value.encode(detection['encoding'])\
                        .decode()
                    # if det['encoding'] is not None:
                    #     print('No need to reencode {} (key {}) from {} ({})'
                    #           .format(value, key, det['encoding'],
                    #                   det['confidence']))
        data.append(reencoded_row)
    return data


class Home(generic.ListView):
    model = Alert
    template_name = 'contacts/home.html'

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(Q(date__gt=timezone.now(), done=False) | Q(done=False))
        return qs.order_by('date')

    def get_context_data(self):
        context = super().get_context_data()
        last_updated = []

        def creation_or_update(object):
            if int(object.creation_date.timestamp()) ==\
                    int(object.update_date.timestamp()):
                return 'creation'
            else:
                return 'update'

        if self.request.user.has_perm('contacts.view_contact'):
            last_updated += [{'date': contact.update_date, 'object': contact,
                              'type': creation_or_update(contact)}
                             for contact in Contact.get_queryset(
                                 self.request.user)
                             .order_by('-update_date')
                             .select_related('author')[:5]
                             ]

        if self.request.user.has_perm('contacts.view_company'):
            last_updated += [{'date': company.update_date, 'object': company,
                              'type': creation_or_update(company)}
                             for company in Company.get_queryset(
                                 self.request.user)
                             .order_by('-update_date')
                             .select_related('author')[:5]
                             ]

        if self.request.user.has_perm('contacts.view_meeting'):
            last_updated += [{'date': meeting.update_date, 'object': meeting,
                              'type': creation_or_update(meeting)}
                             for meeting in Meeting.get_queryset(
                                 self.request.user)
                             .order_by('-update_date')
                             .select_related('author')[:5]
                             ]

            last_updated += [{'date': meeting.date, 'object': meeting,
                              'type': 'meeting'}
                             for meeting in
                             Meeting.get_queryset(self.request.user).filter(
                                 date__lt=timezone.now()).order_by('-date')
                                 .select_related('author')[:5]
                             ]

        if self.request.user.has_perm('contacts.view_alert'):
            last_updated += [{'date': alert.update_date, 'object': alert,
                              'type': creation_or_update(alert)}
                             for alert in Alert.get_queryset(self.request.user)
                             .order_by('-update_date')
                             .select_related('author')[:5]
                             ]

        last_updated.sort(key=lambda i: i['date'], reverse=True)
        context['notifications'] = last_updated

        return context


class AlertDone(generic.UpdateView):

    model = Alert
    fields = ['done']
    success_url = reverse_lazy('contacts:home')


class CompaniesList(generic.SearchFormMixin, generic.ListView):
    model = Company
    form_class = CompanySearchForm
    paginate_by = 10

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['properties_names'] = Properties.get_displayed_names(
            self.request.user.default_group.group,
            'company')
        return context


class CompanyDetail(generic.DetailView):

    model = Company

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['properties_names'] = Properties.get_displayed_names(
            self.request.user.default_group.group,
            'contact')
        return context


class CompanyCreation(generic.CreateView):
    model = Company
    fields = ('name', 'type', 'comments', 'active', )

    def get_form(self, form_class):
        form = super().get_form(form_class)

        # properties fetching
        self.properties = Properties.get_queryset(self.request.user)\
            .filter(type='company')
        for prop in self.properties:
            form.fields[prop.name] = forms.CharField(required=False,
                                                     label=prop.name.title())
        return form

    def form_valid(self, form):
        company = form.save(commit=False)
        company.properties = {p.name: form.cleaned_data[p.name] for p in
                              self.properties}
        company.author = self.request.user
        company.group = self.request.user.default_group.group
        self.object = company
        try:
            company.save()
            messages.add_message(self.request, messages.SUCCESS,
                                 'Compagnie {} créée avec succès.'
                                 .format(company))
        except IntegrityError:
            form.add_error('name', 'Une société de ce nom existe déjà.')
            return super().form_invalid(form)
        return super(ModelFormMixin, self).form_valid(form)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['verb'] = ('Création', 'Créer', 'plus')
        return context


class CompanyUpdate(generic.UpdateView):
    model = Company
    fields = ('name', 'type', 'comments', 'active', )

    def get_form(self, form_class):
        form = super().get_form(form_class)

        # properties fetching
        self.properties = Properties.get_queryset(self.request.user)\
            .filter(type='company')
        props = self.object.properties
        for prop in self.properties:
            form.fields[prop.name] = forms.CharField(
                required=False,
                label=prop.name.title(),
                initial=props.get(prop.name, ''),
            )
        return form

    def form_valid(self, form):
        company = form.save(commit=False)
        company.properties = {p.name: form.cleaned_data[p.name] for p in
                              self.properties}
        self.object = company
        try:
            company.save()
            messages.add_message(self.request, messages.SUCCESS,
                                 'Compagnie {} modifiée avec succès.'
                                 .format(company))
        except IntegrityError:
            form.add_error('name', 'Une société de ce nom existe déjà.')
            return super().form_invalid(form)
        return super(ModelFormMixin, self).form_valid(form)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['verb'] = ('Modification', 'Modifier', 'pencil')
        context['object'] = self.object
        return context


class CompanyDelete(generic.DeleteView):
    model = Company
    success_url = reverse_lazy('contacts:company-list')

    def delete(self, *args, **kwargs):
        messages.add_message(self.request, messages.SUCCESS,
                             'La société {} a été supprimée.'
                             .format(self.get_object()))
        return super().delete(*args, **kwargs)


class MeetingCreation(generic.CreateView):
    model = Meeting
    fields = ('contact', 'type', 'date', 'comments', )

    def get_form(self, form_class):
        form = super().get_form(form_class)

        if 'company' in self.kwargs:
            company = get_object_or_404(
                Company, slug=self.kwargs['company'],
                group=self.request.user.default_group.group
            )
            form.fields['contact'].queryset = form.fields['contact'].queryset\
                .filter(company=company)
            self.company = company

        if 'contact' in self.kwargs:
            contact = get_object_or_404(
                Contact, slug=self.kwargs['contact'],
                group=self.request.user.default_group.group
            )
            self.contact = contact
            del(form.fields['contact'])

        return form

    def form_valid(self, form):
        meeting = form.save(commit=False)
        meeting.author = self.request.user
        if hasattr(self, 'contact'):
            meeting.contact = self.contact
        self.object = meeting
        meeting.save()
        messages.add_message(self.request, messages.SUCCESS,
                             'Échange avec {} créé avec succès.'
                             .format(meeting))
        return super(ModelFormMixin, self).form_valid(form)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['verb'] = ('Création', 'Créer', 'plus')
        if hasattr(self, 'company'):
            context['company'] = self.company
        if hasattr(self, 'contact'):
            context['contact'] = self.contact
        return context


class MeetingList(generic.SearchFormMixin, generic.ListView):
    model = Meeting
    paginate_by = 10
    form_class = MeetingSearchForm

    def get_queryset(self):
        # todo: add ordering support
        qs = super().get_queryset()

        if 'company' in self.kwargs:
            self.company = get_object_or_404(
                Company,
                slug=self.kwargs['company'],
                group=self.request.user.default_group.group)
            qs = qs.filter(contact__company=self.company)

        if 'contact' in self.kwargs:
            self.contact = get_object_or_404(
                Contact,
                slug=self.kwargs['contact'],
                group=self.request.user.default_group.group)
            qs = qs.filter(contact=self.contact)
        return qs

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        if hasattr(self, 'company'):
            context['company'] = self.company
        if hasattr(self, 'contact'):
            context['contact'] = self.contact
        return context


class MeetingDetail(generic.DetailView):
    model = Meeting


class MeetingUpdate(generic.UpdateView):
    model = Meeting
    fields = ('contact', 'type', 'date', 'comments', )

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS,
                             'Échange avec {} modifié avec succès.'
                             .format(self.object))
        return super().form_valid(form)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['verb'] = ('Modification', 'Modifier', 'pencil')
        context['object'] = self.object
        return context


class MeetingDelete(generic.DeleteView):
    model = Meeting
    success_url = reverse_lazy('contacts:meeting-list')

    def delete(self, *args, **kwargs):
        messages.add_message(self.request, messages.SUCCESS,
                             'L’échange avec {} a été supprimé.'
                             .format(self.get_object()))
        return super().delete(*args, **kwargs)


class ContactCreation(generic.CreateView):
    model = Contact
    fields = ('firstname', 'lastname', 'company', 'type', 'comments',
              'active', )

    def get_form(self, form_class):
        form = super().get_form(form_class)

        if 'company' in self.kwargs:
            company = get_object_or_404(
                Company, slug=self.kwargs['company'],
                group=self.request.user.default_group.group
            )
            self.company = company
            del(form.fields['company'])

        # properties fetching
        self.properties = Properties.get_queryset(self.request.user)\
            .filter(type='contact')
        for prop in self.properties:
            form.fields[prop.name] = forms.CharField(required=False,
                                                     label=prop.name.title())
        return form

    def form_valid(self, form):
        contact = form.save(commit=False)
        if hasattr(self, 'company'):
            contact.company = self.company
        contact.properties = {p.name: form.cleaned_data[p.name] for p in
                              self.properties}
        contact.author = self.request.user
        contact.group = self.request.user.default_group.group
        self.object = contact
        try:
            contact.save()
            messages.add_message(self.request, messages.SUCCESS,
                                 'Contact {} créé avec succès.'
                                 .format(contact))
        except IntegrityError:
            form.add_error('firstname', 'Un contact de ce nom existe déjà.')
            return super().form_invalid(form)
        return super(ModelFormMixin, self).form_valid(form)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['verb'] = ('Création', 'Créer', 'plus')
        if hasattr(self, 'company'):
            context['company'] = self.company
        return context


class ContactList(generic.SearchFormMixin, generic.ListView):
    model = Contact
    form_class = ContactSearchForm
    paginate_by = 10

    def get_queryset(self):
        # todo: add ordering support
        qs = super().get_queryset()

        if 'company' in self.kwargs:
            self.company = get_object_or_404(
                Company,
                slug=self.kwargs['company'],
                group=self.request.user.default_group.group)
            qs = qs.filter(company=self.company)
        return qs

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        if hasattr(self, 'company'):
            context['company'] = self.company
        context['properties_names'] = Properties.get_displayed_names(
            self.request.user.default_group.group,
            'contact')
        return context


class ContactDetail(generic.DetailView):
    model = Contact


class ContactUpdate(generic.UpdateView):
    model = Contact
    fields = ('firstname', 'lastname', 'company', 'type', 'comments',
              'active', )

    def get_form(self, form_class):
        form = super().get_form(form_class)

        # properties fetching
        self.properties = Properties.get_queryset(self.request.user)\
            .filter(type='contact')
        props = self.object.properties
        for prop in self.properties:
            form.fields[prop.name] = forms.CharField(
                required=False,
                label=prop.name.title(),
                initial=props.get(prop.name, ''),
            )
        return form

    def form_valid(self, form):
        contact = form.save(commit=False)
        contact.properties = {p.name: form.cleaned_data[p.name] for p in
                              self.properties}
        self.object = contact
        try:
            contact.save()
            messages.add_message(self.request, messages.SUCCESS,
                                 'Contact {} modifié avec succès.'
                                 .format(contact))
        except IntegrityError:
            form.add_error('name', 'Un contact de ce nom existe déjà.')
            return super().form_invalid(form)
        return super(ModelFormMixin, self).form_valid(form)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['verb'] = ('Modification', 'Modifier', 'pencil')
        context['object'] = self.object
        return context


class ContactDelete(generic.DeleteView):
    model = Contact
    success_url = reverse_lazy('contacts:contact-list')

    def delete(self, *args, **kwargs):
        messages.add_message(self.request, messages.SUCCESS,
                             'Le contact {} a été supprimé.'
                             .format(self.get_object()))
        return super().delete(*args, **kwargs)


class AlertCreation(generic.CreateView):
    model = Alert
    fields = ('user', 'contact', 'priority', 'date', 'title', 'comments',
              'done', )

    def get_form(self, form_class):
        form = super().get_form(form_class)

        form.fields['user'].queryset = self.request.user.default_group.group\
            .user_set
        form.fields['user'].initial = self.request.user

        if 'company' in self.kwargs:
            company = get_object_or_404(
                Company, slug=self.kwargs['company'],
                group=self.request.user.default_group.group
            )
            form.fields['contact'].queryset = form.fields['contact'].queryset\
                .filter(company=company)
            self.company = company

        if 'contact' in self.kwargs:
            contact = get_object_or_404(
                Contact, slug=self.kwargs['contact'],
                group=self.request.user.default_group.group
            )
            self.contact = contact
            del(form.fields['contact'])

        return form

    def form_valid(self, form):
        alert = form.save(commit=False)
        alert.author = self.request.user
        if hasattr(self, 'contact'):
            alert.contact = self.contact
        self.object = alert
        alert.save()
        messages.add_message(self.request, messages.SUCCESS,
                             'Échange avec {} créé avec succès.'
                             .format(alert))
        return super(ModelFormMixin, self).form_valid(form)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['verb'] = ('Création', 'Créer', 'plus')
        if hasattr(self, 'company'):
            context['company'] = self.company
        if hasattr(self, 'contact'):
            context['contact'] = self.contact
        return context


class AlertList(generic.SearchFormMixin, generic.ListView):
    model = Alert
    paginate_by = 10
    form_class = AlertSearchForm

    def get_queryset(self):
        # todo: add filtering/ordering support
        qs = super().get_queryset()

        if 'company' in self.kwargs:
            self.company = get_object_or_404(
                Company,
                slug=self.kwargs['company'],
                group=self.request.user.default_group.group)
            qs = qs.filter(contact__company=self.company)

        if 'contact' in self.kwargs:
            self.contact = get_object_or_404(
                Contact,
                slug=self.kwargs['contact'],
                group=self.request.user.default_group.group)
            qs = qs.filter(contact=self.contact)
        return qs

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        if hasattr(self, 'company'):
            context['company'] = self.company
        if hasattr(self, 'contact'):
            context['contact'] = self.contact
        return context


class AlertDetail(generic.DetailView):
    model = Alert


class AlertUpdate(generic.UpdateView):
    model = Alert
    fields = ('contact', 'priority', 'date', 'title', 'comments', 'done', )

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS,
                             'Alerte {} modifiée avec succès.'
                             .format(self.object))
        return super().form_valid(form)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['verb'] = ('Modification', 'Modifier', 'pencil')
        context['object'] = self.object
        return context


class AlertDelete(generic.DeleteView):
    model = Alert
    success_url = reverse_lazy('contacts:alert-list')

    def delete(self, *args, **kwargs):
        messages.add_message(self.request, messages.SUCCESS,
                             'L’alerte {} a été supprimée.'
                             .format(self.get_object()))
        return super().delete(*args, **kwargs)


class SavedSearchCreation(generic.CreateView):
    model = SavedSearch
    fields = ('name', 'display_in_menu', 'type', 'data')

    def get_form_kwargs(self):
        """
        Returns the keyword arguments for instantiating the form.
        """
        kwargs = {
            'initial': self.get_initial(),
            'prefix': self.get_prefix(),
        }

        if self.request.method in ('POST', 'PUT'):
            kwargs.update({
                'data': self.request.POST.copy(),
                'files': self.request.FILES,
            })
            kwargs['data'].update({'data':
                                   {k: v for k, v in self.request.GET.items()},
                                   'type': self.kwargs['type'].title(),
                                   })
        return kwargs

    def get_form(self):
        form = super().get_form()
        form.fields['type'].widget = HiddenInput()
        form.fields['data'].widget = HiddenInput()
        return form

    def form_valid(self, form):
        search = form.save(commit=False)
        search.author = self.request.user
        search.group = self.request.user.default_group.group
        self.object = search
        try:
            search.save()
            messages.add_message(self.request, messages.SUCCESS,
                                 'Recherche {} sauvegardée avec succès.'
                                 .format(search))
            return super(ModelFormMixin, self).form_valid(form)
        except IntegrityError:
            form.add_error('name', 'Une recherche de ce nom existe déjà.')
            return super().form_invalid(form)
        return super(ModelFormMixin, self).form_valid(form)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['verb'] = ('Sauvegarde', 'sauvegarder', 'plus')
        return context


class SavedSearchDetail(generic.DetailView):
    model = SavedSearch

    def get_template_names(self):
        return ['contacts/{}_search_detail.html'
                .format(self.get_object().type.lower())]

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['object_list'] = \
            context['object'].get_search_queryset(self.request.user)
        context['search_type'] = context['object'].type.lower()
        return context


class SavedSearchList(generic.ListView):
    model = SavedSearch
    paginate_by = 10

    def get_queryset(self):
        qs = super().get_queryset()
        if 'type' in self.kwargs:
            types = {c[0].lower(): c for c in SEARCH_CHOICES}
            qs = qs.filter(type=types[self.kwargs['type']][0])
        return qs

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        if 'type' in self.kwargs:
            types = {c[0].lower(): c for c in SEARCH_CHOICES}
            context['search_type'] = types[self.kwargs['type']][0].lower()
            context['search_type_name'] = types[self.kwargs['type']][1]
        return context


class SavedSearchUpdate(generic.UpdateView):
    model = SavedSearch
    fields = ('name', 'display_in_menu')

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS,
                             'Recherche {} modifiée avec succès.'
                             .format(self.object))
        return super().form_valid(form)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['verb'] = ('Modification', 'Modifier', 'pencil')
        context['object'] = self.object
        context['search_type'] = context['object'].type.lower()
        return context


class SavedSearchDelete(generic.DeleteView):
    model = SavedSearch
    success_url = reverse_lazy('contacts:search-list')

    def delete(self, *args, **kwargs):
        messages.add_message(self.request, messages.SUCCESS,
                             'La recherche {} a été supprimée.'
                             .format(self.get_object()))
        return super().delete(*args, **kwargs)


class Import(generic.LoginRequiredMixin, generic.LatePermissionMixin,
             FormView):
    permission_suffix = 'add'
    template_name = 'contacts/import.html'

    def get_form_class(self):
        types = {c[0].lower(): c for c in SEARCH_CHOICES}
        form_class_name = '{}ImportForm'.format(types[self.kwargs['type']][0])
        from . import forms
        form = getattr(forms, form_class_name)
        # default attributes
        if 'properties_list' in form.base_fields:
            form.base_fields['properties_list'].initial = ','\
                .join(Properties.get_displayed_names(
                      self.request.user.default_group.group,
                      self.kwargs['type']))
        return form

    def get_model(self):
        types = {c[0].lower(): c for c in SEARCH_CHOICES}
        class_name = types[self.kwargs['type']][0]
        from . import models
        return getattr(models, class_name)

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        model = self.get_model()
        if form.is_valid():
            if ('file' not in form.changed_data
                and 'content' not in form.changed_data)\
                    or ('file' in form.changed_data
                        and 'content' in form.changed_data):
                form.errors['content'] = ['Vous devez remplir un seul de ces '
                                          'champs']
                form.errors['file'] = ['Vous devez remplir un seul de ces '
                                       'champs']
                return self.form_invalid(form)

            # parsing the CSV
            if 'file' in form.changed_data:  # upload
                field = 'file'
                content = form.cleaned_data['file'].read()
                detection = chardet.detect(content)
                if detection['confidence'] < .5:
                    form.errors['file'] = ['Encodage non reconnu']
                    return self.form_invalid(form)
                content = content.decode(detection['encoding'])
            else:  # we parse the inline content
                field = 'content'
                try:
                    content = form.cleaned_data['content'].encode('latin-1')
                except UnicodeEncodeError:
                    content = form.cleaned_data['content'].encode()
                detection = chardet.detect(content)
                content = content.decode(detection['encoding'])
            dialect = csv.Sniffer().sniff(content)
            if dialect.escapechar is None:
                dialect.escapechar = '\\'  # hack
            reader = csv.DictReader(StringIO(content), dialect=dialect)

            # mapping extraction
            mapping = {k[:-6]: v for k, v in form.cleaned_data.items()
                       if k.endswith('_field') and v != ''}

            # values charset detection
            data = reencode_data(reader, detection)

            properties = None
            if 'properties_list' in form.cleaned_data and\
                    form.cleaned_data['properties_list'] != '':
                properties = [p.strip() for p in
                              form.cleaned_data['properties_list'].split(',')
                              ]
            if 'date_format' in form.cleaned_data:
                properties = form.cleaned_data['date_format']  # urk!
            try:
                inserted, updated, errors = model\
                    .import_data(data, mapping, properties,
                                 self.request.user)
            except (UnicodeEncodeError, UnicodeDecodeError):
                form.errors[field] = ['Encodage incorrect']
                return self.form_invalid(form)

            context = {'object_list': set(sorted(inserted + updated,
                                                 key=lambda i: i.update_date)),
                       'errors': errors}

            if len(inserted + updated) > 0:
                model_name_plural = model._meta.verbose_name_plural\
                    if len(inserted + updated) > 0\
                    else model._meta.verbose_name
                messages.add_message(self.request, messages.SUCCESS,
                                     'Import de {} {} effectué.'
                                     .format(len(inserted + updated),
                                             model_name_plural))

            if errors > 0:
                plural = 's' if errors > 0 else ''
                messages.add_message(self.request, messages.ERROR,
                                     'Import de {} : {} erreur{}.'
                                     .format(model._meta.verbose_name_plural,
                                             errors,
                                             plural))

            return redirect(
                resolve_url('contacts:{}-list'.format(self.kwargs['type']))
                + '?id=' + ','.join([str(o.pk) for o in
                                     context['object_list']]))
            # return render(self.request,
            #               'contacts/{}_import.html'
            #               .format(self.kwargs['type']),
            #               context)
        else:
            return self.form_invalid(form)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        types = {c[0].lower(): c for c in SEARCH_CHOICES}
        context['import_type'] = types[self.kwargs['type']][0].lower()
        context['import_type_name'] = types[self.kwargs['type']][1]
        context['search_type'] = self.kwargs['type']
        context['words'] = self.get_model()._meta.words
        return context


class GroupChange(generic.DetailView):
    model = Group
    permission_name = 'auth.view_group'

    def get(self, request, pk):
        group = self.get_object()
        request.user.default_group.group = group
        request.user.default_group.save()
        messages.add_message(self.request, messages.INFO,
                             'Groupe changé : {}'.format(group))
        return redirect('contacts:home')

    def get_queryset(self):
        return self.request.user.groups


class Export(generic.SearchFormMixin, generic.LoginRequiredMixin,
             generic.LatePermissionMixin, ListView):

    def get_model(self):
        types = {c[0].lower(): c for c in SEARCH_CHOICES}
        class_name = types[self.kwargs['type']][0]
        from . import models
        self.model = getattr(models, class_name)
        return self.model

    def get_form_class(self):
        types = {c[0].lower(): c for c in SEARCH_CHOICES}
        if 'type' in self.kwargs:
            form_class_name = '{}SearchForm'.format(
                types[self.kwargs['type']][0])
        else:
            obj = self.get_object()
            form_class_name = '{}SearchForm'.format(
                obj._meta.model_name)
        from . import forms
        return getattr(forms, form_class_name)

    def get(self, request, *args, **kwargs):
        model = self.get_model()
        super().get(request, *args, **kwargs)
        qs = self.object_list
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; '\
            'filename="pyru_{}_{}.csv"'.format(self.kwargs['type'],
                                               timezone.now()
                                               .strftime('%Y%m%d%H%M%S'))
        export = model.export_data(qs)
        if len(export):
            writer = csv.DictWriter(response, fieldnames=export[0].keys(),
                                    escapechar='\\', doublequote=False)
            writer.writeheader()
            for row in export:
                writer.writerow(row)
        return response


class ContactFastSearch(generic.ListView):
    model = Contact

    def get_queryset(self):
        qs = super().get_queryset()
        if 'q' in self.request.GET:
            query_words = self.request.GET['q'].split(' ')
            filters = []
            for word in query_words:
                filters.append(Q(firstname__icontains=word)
                               | Q(lastname__icontains=word)
                               | Q(company__name__icontains=word))
            query = reduce(operator.and_, filters)
            qs = qs.filter(query)

        qs = qs.distinct()[:10]
        return qs

    def get(self, *args, **kwargs):
        super().get(*args, **kwargs)
        response = HttpResponse(content_type='application/json')
        content = []
        for obj in self.object_list:
            company = '' if obj.company is None else\
                ' ({})'.format(obj.company)
            row = {'name': '{}{}'.format(obj, company),
                   'url': obj.get_absolute_url()}
            content.append(row)
        response.write(json.dumps(content))
        return response
