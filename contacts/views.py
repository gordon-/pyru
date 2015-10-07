import csv
from io import StringIO

from django.utils import timezone
from django.shortcuts import get_object_or_404, render
from django.core.urlresolvers import reverse_lazy
from django import forms
from django.views.generic.edit import ModelFormMixin, FormView
from django.db import IntegrityError
from django.contrib import messages
from django.contrib.auth.models import User
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
        qs = qs.filter(date__gt=timezone.now(), done=False)
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
                             .order_by('-update_date')[:5]
                             ]

        if self.request.user.has_perm('contacts.view_company'):
            last_updated += [{'date': company.update_date, 'object': company,
                              'type': creation_or_update(company)}
                             for company in Company.get_queryset(
                                 self.request.user)
                             .order_by('-update_date')[:5]
                             ]

        if self.request.user.has_perm('contacts.view_meeting'):
            last_updated += [{'date': meeting.update_date, 'object': meeting,
                              'type': creation_or_update(meeting)}
                             for meeting in Meeting.get_queryset(
                                 self.request.user)
                             .order_by('-update_date')[:5]
                             ]

            last_updated += [{'date': meeting.date, 'object': meeting,
                              'type': 'meeting'}
                             for meeting in
                             Meeting.get_queryset(self.request.user).filter(
                                 date__lt=timezone.now()).order_by('-date')[:5]
                             ]

        if self.request.user.has_perm('contacts.view_alert'):
            last_updated += [{'date': alert.update_date, 'object': alert,
                              'type': creation_or_update(alert)}
                             for alert in Alert.get_queryset(self.request.user)
                             .order_by('-update_date')[:5]
                             ]

        last_updated.sort(key=lambda i: i['date'], reverse=True)
        context['notifications'] = last_updated

        return context


class CompaniesList(generic.SearchFormMixin, generic.ListView):
    model = Company
    form_class = CompanySearchForm
    paginate_by = 10


class CompanyDetail(generic.DetailView):

    model = Company


class CompanyCreation(generic.CreateView):
    model = Company
    fields = ('name', 'group', 'type', 'comments', 'active', )

    def get_form(self, form_class):
        form = super().get_form(form_class)
        # standard filtering
        form.fields['group'].queryset = self.request.user.groups.all()

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
    fields = ('name', 'group', 'type', 'comments', 'active', )

    def get_form(self, form_class):
        form = super().get_form(form_class)
        # standard filtering
        form.fields['group'].queryset = self.request.user.groups.all()

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
                group__in=self.request.user.groups.all()
            )
            form.fields['contact'].queryset = form.fields['contact'].queryset\
                .filter(company=company)
            self.company = company

        if 'contact' in self.kwargs:
            contact = get_object_or_404(
                Contact, slug=self.kwargs['contact'],
                group__in=self.request.user.groups.all()
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
            self.company = get_object_or_404(Company,
                                             slug=self.kwargs['company'],
                                             group__in=self.request.user.groups
                                             .all())
            qs = qs.filter(contact__company=self.company)

        if 'contact' in self.kwargs:
            self.contact = get_object_or_404(Contact,
                                             slug=self.kwargs['contact'],
                                             group__in=self.request.user.groups
                                             .all())
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
    fields = ('firstname', 'lastname', 'company', 'group', 'type', 'comments',
              'active', )

    def get_form(self, form_class):
        form = super().get_form(form_class)
        # standard filtering
        form.fields['group'].queryset = self.request.user.groups.all()

        if 'company' in self.kwargs:
            company = get_object_or_404(
                Company, slug=self.kwargs['company'],
                group__in=self.request.user.groups.all()
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
            self.company = get_object_or_404(Company,
                                             slug=self.kwargs['company'],
                                             group__in=self.request.user.groups
                                             .all())
            qs = qs.filter(company=self.company)
        return qs

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        if hasattr(self, 'company'):
            context['company'] = self.company
        return context


class ContactDetail(generic.DetailView):
    model = Contact


class ContactUpdate(generic.UpdateView):
    model = Contact
    fields = ('firstname', 'lastname', 'company', 'group', 'type', 'comments',
              'active', )

    def get_form(self, form_class):
        form = super().get_form(form_class)
        # standard filtering
        form.fields['group'].queryset = self.request.user.groups.all()

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

        form.fields['user'].queryset = User.objects.filter(
            groups__in=self.request.user.groups.all()
        ).distinct()
        form.fields['user'].initial = self.request.user

        if 'company' in self.kwargs:
            company = get_object_or_404(
                Company, slug=self.kwargs['company'],
                group__in=self.request.user.groups.all()
            )
            form.fields['contact'].queryset = form.fields['contact'].queryset\
                .filter(company=company)
            self.company = company

        if 'contact' in self.kwargs:
            contact = get_object_or_404(
                Contact, slug=self.kwargs['contact'],
                group__in=self.request.user.groups.all()
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
            self.company = get_object_or_404(Company,
                                             slug=self.kwargs['company'],
                                             group__in=self.request.user.groups
                                             .all())
            qs = qs.filter(contact__company=self.company)

        if 'contact' in self.kwargs:
            self.contact = get_object_or_404(Contact,
                                             slug=self.kwargs['contact'],
                                             group__in=self.request.user.groups
                                             .all())
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
    fields = ('name', 'group', 'display_in_menu', 'type', 'data')

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
    fields = ('name', 'display_in_menu', 'group')

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


class Export(generic.ListView):
    model = Contact


class Import(FormView):
    template_name = 'contacts/import.html'

    def get_form_class(self):
        types = {c[0].lower(): c for c in SEARCH_CHOICES}
        form_class_name = '{}ImportForm'.format(types[self.kwargs['type']][0])
        from . import forms
        return getattr(forms, form_class_name)

    def get_model_class(self):
        types = {c[0].lower(): c for c in SEARCH_CHOICES}
        class_name = types[self.kwargs['type']][0]
        from . import models
        return getattr(models, class_name)

    def post(self, request, *args, **kwargs):
        form = self.get_form()
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
                content = form.cleaned_data['file'].read()
                detection = chardet.detect(content)
                if detection['confidence'] < .5:
                    form.errors['file'] = ['Encodage non reconnu']
                    return self.form_invalid(form)
                content = content.decode(detection['encoding'])
            else:  # we parse the inline content
                try:
                    content = form.cleaned_data['content'].encode('latin-1')
                except UnicodeEncodeError:
                    content = form.cleaned_data['content'].encode()
                detection = chardet.detect(content)
                content = content.decode(detection['encoding'])
            dialect = csv.Sniffer().sniff(content)
            reader = csv.DictReader(StringIO(content), dialect=dialect)

            # mapping extraction
            mapping = {k[:-6]: v for k, v in form.cleaned_data.items()
                       if k.endswith('_field') and v != ''}

            # values charset detection
            data = reencode_data(reader, detection)

            properties = None
            if 'properties_list' in form.cleaned_data:
                properties = [p.strip() for p in
                              form.cleaned_data['properties_list'].split(',')
                              ]
            inserted, updated, errors = self.get_model_class()\
                .import_data(data, mapping, properties,
                             self.request.user, form.cleaned_data['group'])

            context = {'object_list': sorted(inserted + updated,
                                             key=lambda i: i.update_date),
                       'errors': errors}

            return render(self.request,
                          'contacts/{}_import.html'
                          .format(self.kwargs['type']),
                          context)
        else:
            return self.form_invalid(form)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        types = {c[0].lower(): c for c in SEARCH_CHOICES}
        context['import_type'] = types[self.kwargs['type']][0].lower()
        context['import_type_name'] = types[self.kwargs['type']][1]
        return context
