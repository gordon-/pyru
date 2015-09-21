import operator
from functools import reduce

from django import forms
from django.db.models import Q
from django.contrib.auth.models import Group
from django.forms import ModelChoiceField
from datetimewidget.widgets import DateWidget

from .models import ContactType, Properties


class SearchForm(forms.Form):
    bound_css_class = ''  # for django-bootstrap3 enhancement

    def _process_multiple_targets(self, field_name, field_value, mapping):
        queries = []
        split_mode = False
        if 'split' in mapping and mapping['split'] and ' ' in field_value:
            split_mode = True
            field_value = field_value.split(' ')
        else:
            field_value = [field_value]
        for value in field_value:
            subqueries = []
            for target in mapping['target']:
                filters = self._apply_filter(target, value)
                subqueries.append(Q(**filters))

                subquery = reduce(operator.or_, subqueries)
            queries.append(subquery)
        if 'operator' in mapping \
                and mapping['operator'] == 'and' \
                and split_mode:
            query = reduce(operator.and_, queries)
        else:
            query = reduce(operator.or_, queries)
        return query

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
            if field_name in self.fields \
                    and isinstance(self.fields[field_name], ModelChoiceField):
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
                            qs = qs.filter(self._process_multiple_targets(
                                field_name, field_value, mapping))
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
                    'split': True, 'operator': 'and'},
                    'company': {'target': ['company__name']},
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
