from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse_lazy
from django.views import generic
from django import forms
from django.views.generic.edit import ModelFormMixin
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.contrib import messages

from .mixins import LoginRequiredMixin
from .models import (
    Properties, Alert, ContactType, Company, Contact, MeetingType, Meeting
)


class Home(LoginRequiredMixin, generic.ListView):

    model = Alert

    def get_queryset(self):
        return self.model.objects.filter(user=self.request.user)\
            .order_by('-date')


class CompaniesList(LoginRequiredMixin, generic.ListView):

    model = Company

    def get_queryset(self):
        # todo: add filtering/ordering support
        return self.model\
            .objects.filter(group__in=self.request.user.groups.all())\
            .order_by('name')


class CompanyDetail(LoginRequiredMixin, generic.DetailView):

    model = Company

    def get_object(self):
        filters = {'slug': self.kwargs['slug'],
                   'group__in': self.request.user.groups.all()}
        obj = get_object_or_404(self.model, **filters)
        return obj


class CompanyCreation(LoginRequiredMixin, generic.CreateView):

    model = Company
    fields = ('name', 'group', 'type', 'comments', 'active', )

    def get_form(self, form_class):
        form = super().get_form(form_class)
        # standard filtering
        form.fields['group'].queryset = self.request.user.groups.all()

        # properties fetching
        self.properties = Properties.objects.filter(type='company')\
            .order_by('order')
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
        context['verb'] = ('Création', 'Créer')
        return context


class CompanyUpdate(LoginRequiredMixin, generic.UpdateView):

    model = Company
    fields = ('name', 'group', 'type', 'comments', 'active', )

    def get_object(self):
        filters = {'slug': self.kwargs['slug'],
                   'group__in': self.request.user.groups.all()}
        obj = get_object_or_404(self.model, **filters)
        return obj

    def get_form(self, form_class):
        form = super().get_form(form_class)
        # standard filtering
        form.fields['group'].queryset = self.request.user.groups.all()

        # properties fetching
        self.properties = Properties.objects.filter(type='company')\
            .order_by('order')
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
        context['verb'] = ('Modification', 'Modifier')
        context['object'] = self.object
        return context


class CompanyDelete(LoginRequiredMixin, generic.DeleteView):

    model = Company
    success_url = reverse_lazy('contacts:company-list')

    def get_object(self):
        filters = {'slug': self.kwargs['slug'],
                   'group__in': self.request.user.groups.all()}
        obj = get_object_or_404(self.model, **filters)
        return obj

    def delete(self, *args, **kwargs):
        messages.add_message(self.request, messages.SUCCESS,
                             'La société {} a été supprimée.'
                             .format(self.get_object()))
        return super().delete(*args, **kwargs)


class ContactCreation(LoginRequiredMixin, generic.CreateView):

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
        self.properties = Properties.objects.filter(type='contact')\
            .order_by('order')
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
        context['verb'] = ('Création', 'Créer')
        return context


class ContactList(LoginRequiredMixin, generic.ListView):

    model = Contact

    def get_queryset(self):
        # todo: add filtering/ordering support
        qs = self.model\
            .objects.filter(group__in=self.request.user.groups.all())\
            .order_by('firstname')

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


class ContactDetail(LoginRequiredMixin, generic.DetailView):

    model = Contact

    def get_object(self):
        filters = {'slug': self.kwargs['slug'],
                   'group__in': self.request.user.groups.all()}
        if 'company' in self.kwargs:
            self.company = get_object_or_404(Company,
                                             slug=self.kwargs['company'],
                                             group__in=self.request.user.groups
                                             .all())
            filters['company'] = self.company
        obj = get_object_or_404(self.model, **filters)
        return obj

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        if hasattr(self, 'company'):
            context['company'] = self.company
        return context


class ContactUpdate(LoginRequiredMixin, generic.UpdateView):

    model = Contact
    fields = ('firstname', 'lastname', 'company', 'group', 'type', 'comments',
              'active', )

    def get_object(self):
        filters = {'slug': self.kwargs['slug'],
                   'group__in': self.request.user.groups.all()}
        obj = get_object_or_404(self.model, **filters)
        return obj

    def get_form(self, form_class):
        form = super().get_form(form_class)
        # standard filtering
        form.fields['group'].queryset = self.request.user.groups.all()

        # properties fetching
        self.properties = Properties.objects.filter(type='contact')\
            .order_by('order')
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
        context['verb'] = ('Modification', 'Modifier')
        context['object'] = self.object
        return context


class ContactDelete(LoginRequiredMixin, generic.DeleteView):

    model = Contact
    success_url = reverse_lazy('contacts:contact-list')

    def get_object(self):
        filters = {'slug': self.kwargs['slug'],
                   'group__in': self.request.user.groups.all()}
        obj = get_object_or_404(self.model, **filters)
        return obj

    def delete(self, *args, **kwargs):
        messages.add_message(self.request, messages.SUCCESS,
                             'Le contact {} a été supprimé.'
                             .format(self.get_object()))
        return super().delete(*args, **kwargs)
