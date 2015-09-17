from django import forms
from django.db.models import Q
from datetimewidget.widgets import DateWidget

from .models import ContactType, Properties


class ContactSearchForm(forms.Form):
    name = forms.CharField(label='nom', required=False)
    added_before = forms.DateTimeField(
        label='ajouté avant le',
        widget=DateWidget(usel10n=True, bootstrap_version=3),
        required=False,
    )
    added_after = forms.DateTimeField(
        label='ajouté après le',
        widget=DateWidget(usel10n=True, bootstrap_version=3),
        required=False,
    )

    updated_before = forms.DateTimeField(
        label='modifié avant le',
        widget=DateWidget(usel10n=True, bootstrap_version=3),
        required=False,
    )
    updated_after = forms.DateTimeField(
        label='modifié après le',
        widget=DateWidget(usel10n=True, bootstrap_version=3),
        required=False,
    )
    contact_type = forms.ModelChoiceField(
        label='type',
        queryset=ContactType.objects.all(),
        required=False,
        )

    def __init__(self, *args, **kwargs):
        if 'request' in kwargs:
            self.request = kwargs.pop('request')
            self.base_fields['contact_type'].queryset = \
                ContactType.get_queryset(self.request.user)

            self.properties = Properties.get_queryset(self.request.user)\
                .filter(type='contact')
            for prop in self.properties:
                self.base_fields[prop.name] = forms.CharField(
                    required=False,
                    label=prop.name.title()
                )
        super().__init__(*args, **kwargs)

    def search(self, qs):
        self.full_clean()
        if hasattr(self, 'cleaned_data'):
            search = self.cleaned_data
            if 'name' in search and search['name'] != '':
                qs = qs.filter(Q(firstname__icontains=search['name']) |
                               Q(lastname__icontains=search['name']))

            if 'added_before' in search and search['added_before'] is not None:
                qs = qs.filter(creation_date__lt=search['added_before'])

            if 'added_after' in search and search['added_after'] is not None:
                qs = qs.filter(creation_date__gt=search['added_after'])

            if 'updated_before' in search and \
                    search['updated_before'] is not None:
                qs = qs.filter(update_date__lt=search['updated_before'])

            if 'updated_after' in search and \
                    search['updated_after'] is not None:
                qs = qs.filter(update_date__gt=search['updated_after'])

            if 'contact_type' in search and search['contact_type'] is not None:
                qs = qs.filter(type=search['contact_type'])

            for prop in self.properties:
                if prop.name in search and search[prop.name] != '':
                    kwargs = {'properties__{}__icontains'.format(prop.name):
                              search[prop.name]}
                    qs = qs.filter(**kwargs)

        return qs
