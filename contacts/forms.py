import operator
from functools import reduce

from django import forms
from django.db.models import Q
from django.contrib.auth.models import Group
from django.forms import ModelChoiceField
from datetimewidget.widgets import DateWidget

from .models import (
    ContactType, Properties, MeetingType, SavedSearch, PRIORITIES
)


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

    def is_submitted(self):
        return len(self.changed_data) != 0


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
        to_field_name='name',
        )
    group = forms.ModelChoiceField(
        label='groupe',
        queryset=Group.objects.all(),
        required=False,
        to_field_name='name',
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


class CompanySearchForm(SearchForm):
    name = forms.CharField(label='nom', required=False)
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
        to_field_name='name',
        )
    group = forms.ModelChoiceField(
        label='groupe',
        queryset=Group.objects.all(),
        required=False,
        to_field_name='name',
        )

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


class MeetingSearchForm(SearchForm):
    contact = forms.CharField(label='nom du contact', required=False)
    company = forms.CharField(label='société', required=False)
    date_less = forms.DateTimeField(
        label='avant le',
        widget=DateWidget(usel10n=True, bootstrap_version=3),
        required=False,
    )
    date_more = forms.DateTimeField(
        label='après le',
        widget=DateWidget(usel10n=True, bootstrap_version=3),
        required=False,
    )
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
        queryset=MeetingType.objects.all(),
        required=False,
        to_field_name='name'
        )

    def __init__(self, *args, **kwargs):
        if 'request' in kwargs:
            self.request = kwargs.pop('request')
            self.base_fields['type'].queryset = \
                MeetingType.get_queryset(self.request.user)

        super().__init__(*args, **kwargs)

    class Meta:
        mappings = {'contact': {'target': ['contact__firstname',
                                           'contact__lastname'],
                                'split': True, 'operator': 'and'},
                    'company': {'target': 'contact__company__name'},
                    }


class AlertSearchForm(SearchForm):
    contact = forms.CharField(label='nom du contact', required=False)
    company = forms.CharField(label='société', required=False)
    date_less = forms.DateTimeField(
        label='avant le',
        widget=DateWidget(usel10n=True, bootstrap_version=3),
        required=False,
    )
    date_more = forms.DateTimeField(
        label='après le',
        widget=DateWidget(usel10n=True, bootstrap_version=3),
        required=False,
    )
    priority = forms.ChoiceField(
        label='priorité',
        choices=(('', '---------'), ) + PRIORITIES,
        required=False,
        )
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

    class Meta:
        mappings = {'contact': {'target': ['contact__firstname',
                                           'contact__lastname'],
                                'split': True, 'operator': 'and'},
                    'company': {'target': 'contact__company__name'},
                    }

    def __init__(self, *args, **kwargs):
        if 'request' in kwargs:
            self.request = kwargs.pop('request')

        super().__init__(*args, **kwargs)


class SavedSearchForm(forms.ModelForm):

    class Meta:
        model = SavedSearch
        fields = ('name', 'group', 'display_in_menu')


class ImportForm(forms.Form):
    content = forms.CharField(label='contenu CSV', widget=forms.Textarea,
                              required=False)
    file = forms.FileField(label='fichier CSV', required=False)
    group = forms.ModelChoiceField(
        label='groupe',
        queryset=Group.objects.all(),
        required=False,
        to_field_name='name',
        )

    def get_form_kwargs(self):
        """
        Returns the keyword arguments for instantiating the form.
        """
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request

        return kwargs

    def __init__(self, *args, **kwargs):
        if 'request' in kwargs:
            self.request = kwargs.pop('request')

            self.base_fields['group'].queryset = \
                self.request.user.groups.all()

        super().__init__(*args, **kwargs)


class ContactImportForm(ImportForm):
    type_field = forms.CharField(label='nom du champ « type »',
                                 initial='type')
    company_field = forms.CharField(label='nom du champ « société »',
                                    initial='company')
    firstname_field = forms.CharField(label='nom du champ « prénom »',
                                      initial='firstname')
    lastname_field = forms.CharField(label='nom du champ « nom »',
                                     initial='lastname')
    comments_field = forms.CharField(label='nom du champ « commentaires »',
                                     initial='comments')
