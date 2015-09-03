from django.shortcuts import get_object_or_404
from django.views import generic
from django import forms
from django.views.generic.edit import ModelFormMixin
from django.db import IntegrityError
from django.core.exceptions import ValidationError

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
        except IntegrityError:
            form.add_error('name', 'Une compagnie de ce nom existe déjà.')
            return super().form_invalid(form)
        return super(ModelFormMixin, self).form_valid(form)


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
        except IntegrityError:
            form.add_error('firstname', 'Un contact de ce nom existe déjà.')
            return super().form_invalid(form)
        return super(ModelFormMixin, self).form_valid(form)


class ContactList(LoginRequiredMixin, generic.ListView):

    model = Contact

    def get_queryset(self):
        # todo: add filtering/ordering support
        qs = self.model\
            .objects.filter(group__in=self.request.user.groups.all())\
            .order_by('firstname')

        if 'company' in self.kwargs:
            company = get_object_or_404(Company, slug=self.kwargs['company'],
                                        group__in=self.request.user.groups
                                        .all())
            qs = qs.filter(company=company)
        return qs


class ContactDetail(LoginRequiredMixin, generic.DetailView):

    model = Contact

    def get_object(self):
        filters = {'slug': self.kwargs['slug'],
                   'group__in': self.request.user.groups.all()}
        if 'company' in self.kwargs:
            company = get_object_or_404(Company, slug=self.kwargs['company'],
                                        group__in=self.request.user.groups
                                        .all())
            filters['company'] = company
        obj = get_object_or_404(Contact, **filters)
        return obj
