import operator
from functools import reduce

from django import forms
from django.db.models import Q
from django.contrib.auth.models import Group
from django.forms import ModelChoiceField
from datetimewidget.widgets import DateWidget

from .models import ContactType, Properties


class SearchForm(forms.Form):

    def _apply_filter(self, field_name, field_value):
        filters = {}
        if field_name.endswith('_less'):
            field_name = field_name[:-5]
            filters['{}__lt'.format(field_name)] = field_value
        elif field_name.endswith('_more'):
            field_name = field_name[:-5]
            filters['{}__gt'.format(field_name)] = field_value
        elif field_name.startswith('='):
            field_name = field_name[1:]
            filters['{}__iequals'.format(field_name)] = field_value
        else:
            if isinstance(self.fields[field_name], ModelChoiceField):
                filters[field_name] = field_value
            else:
                filters['{}__icontains'.format(field_name)] = field_value
        return filters

    def search(self, qs):
        """
        Filters the given queryset with the contents of the form.
        By default, the fields names are mapped to model fields, but you can
        override this with a 'mappings' attribute in the Meta class.
        """
        self.full_clean()
        mappings = self.Meta.mappings if hasattr(self, 'Meta') and\
            hasattr(self.Meta, 'mappings') else {}
        if hasattr(self, 'cleaned_data'):
            search = self.cleaned_data
            filters = {}
            for field_name, field_value in search.items():
                if field_value is not None and field_value != '':
                    if field_name in mappings:
                        mapping = mappings[field_name]
                        field_name = mapping['target']
                        if isinstance(mapping['target'], list):
                            queries = []
                            for target in mapping['target']:
                                    filters = self._apply_filter(target,
                                                                 field_value)
                                    queries.append(Q(**filters))
                            qs = qs.filter(reduce(operator.or_, queries))
                        else:
                            filters.update(self._apply_filter(field_name,
                                                              field_value))
                            qs = qs.filter(**filters)
                    else:
                        filters.update(self._apply_filter(field_name,
                                                          field_value))
                        qs = qs.filter(**filters)
        return qs


class ContactSearchForm(SearchForm):
    name = forms.CharField(label='nom', required=False)
    company = forms.CharField(label='société', required=False)
    creation_date_less = forms.DateTimeField(
        label='ajouté avant le',
        widget=DateWidget(usel10n=True, bootstrap_version=3),
        required=False,
    )
    creation_date_more = forms.DateTimeField(
        label='ajouté après le',
        widget=DateWidget(usel10n=True, bootstrap_version=3),
        required=False,
    )

    update_date_less = forms.DateTimeField(
        label='modifié avant le',
        widget=DateWidget(usel10n=True, bootstrap_version=3),
        required=False,
    )
    update_date_more = forms.DateTimeField(
        label='modifié après le',
        widget=DateWidget(usel10n=True, bootstrap_version=3),
        required=False,
    )
    type = forms.ModelChoiceField(
        label='type',
        queryset=ContactType.objects.all(),
        required=False,
        )
    group = forms.ModelChoiceField(
        label='groupe',
        queryset=Group.objects.all(),
        required=False,
        )

    class Meta:
        mappings = {'name': {'target': ['firstname', 'lastname'],
                             'split': True},
                    }

    def __init__(self, *args, **kwargs):
        if 'request' in kwargs:
            self.request = kwargs.pop('request')
            self.base_fields['type'].queryset = \
                ContactType.get_queryset(self.request.user)

            self.base_fields['group'].queryset = \
                self.request.user.groups.all()

            self.properties = Properties.get_queryset(self.request.user)\
                .filter(type='contact')
            for prop in self.properties:
                self.base_fields['properties__{}'.format(prop.name)] = \
                    forms.CharField(required=False, label=prop.name.title())
        super().__init__(*args, **kwargs)

    # def search(self, qs):
    #     self.full_clean()
    #     if hasattr(self, 'cleaned_data'):
    #         search = self.cleaned_data
    #         if 'name' in search and search['name'] != '':
    #             qs = qs.filter(Q(firstname__icontains=search['name']) |
    #                            Q(lastname__icontains=search['name']))

    #         if 'added_before' in search and search['added_before'] is not None:
    #             qs = qs.filter(creation_date__lt=search['added_before'])

    #         if 'added_after' in search and search['added_after'] is not None:
    #             qs = qs.filter(creation_date__gt=search['added_after'])

    #         if 'updated_before' in search and \
    #                 search['updated_before'] is not None:
    #             qs = qs.filter(update_date__lt=search['updated_before'])

    #         if 'updated_after' in search and \
    #                 search['updated_after'] is not None:
    #             qs = qs.filter(update_date__gt=search['updated_after'])

    #         if 'contact_type' in search and search['contact_type'] is not None:
    #             qs = qs.filter(type=search['contact_type'])

    #         for prop in self.properties:
    #             if prop.name in search and search[prop.name] != '':
    #                 kwargs = {'properties__{}__icontains'.format(prop.name):
    #                           search[prop.name]}
    #                 qs = qs.filter(**kwargs)

    #     return qs
