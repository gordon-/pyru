from django.http import Http404
from django.utils.http import urlencode
from django.utils.translation import ugettext as _
from django.utils.text import slugify
from django.core.exceptions import ImproperlyConfigured
from django.forms import models as model_forms
from django.contrib.auth.decorators import login_required, permission_required
from django.views import generic
from django.contrib.auth.views import redirect_to_login
from django.conf import settings
from django.shortcuts import resolve_url
from django.forms import ModelChoiceField, DateTimeField, DateField
from django.utils.six.moves.urllib.parse import urlparse
from django.db.models import Count
from django.db.models.fields.related import (
    ForeignKey, ManyToManyRel, ManyToOneRel)
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.postgres.fields import HStoreField
from datetimewidget.widgets import DateTimeWidget, DateWidget
from autocomplete_light.forms import ModelForm

from .forms import SavedSearchForm


class ForceResponse(Exception):
    def __init__(self, response):
        self.response = response


def response_from_exception(fn):
    """
    Returns an HTTP response contained in a special type of exception.
    """
    def forced_response(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except ForceResponse as e:
            return e.response

    return forced_response


class LoginRequiredMixin():
    @classmethod
    def as_view(cls, **initkwargs):
        view = super(LoginRequiredMixin, cls).as_view(**initkwargs)
        return login_required(view)


class PermissionMixin():

    @classmethod
    def get_model(cls):
        if hasattr(cls, 'model'):
            return cls.model
        else:
            return super().get_model()

    @classmethod
    def _get_perm(cls):
        if not hasattr(cls, 'permission_name'):
            permission_name = cls.get_model().__name__.lower()
            if hasattr(cls, 'permission_suffix'):
                permission_name = 'contacts.{permission}_{model}'.format(
                    model=permission_name,
                    permission=cls.permission_suffix,
                )
        return permission_name

    @classmethod
    def as_view(cls, *args, **kwargs):
        view = permission_required(cls._get_perm())(
            super().as_view(*args, **kwargs)
        )
        return view
        # if not request.user.has_perm(cls._get_perm()):
        #     raise PermissionDenied()
        # return super().dispatch(request, *args, **kwargs)

    @response_from_exception
    def get(self, *args, **kwargs):
        return super().get(*args, **kwargs)

    @response_from_exception
    def post(self, *args, **kwargs):
        return super().post(*args, **kwargs)

    @response_from_exception
    def delete(self, *args, **kwargs):
        return super().delete(*args, **kwargs)

    def get_object(self, **filters):
        if len(filters) == 0:
            obj = super().get_object()
        else:
            obj = super().get_object(self.get_model().filter(**filters))
        if not self.request.user.has_perm(self._get_perm(), obj):
            resolved_login_url = resolve_url(settings.LOGIN_URL)
            path = self.request.build_absolute_uri()
            raise ForceResponse(redirect_to_login(path, resolved_login_url))
        return obj

    def get_queryset(self):
        model = self.get_model()
        if hasattr(model, 'get_queryset'):
            qs = model.get_queryset(self.request.user)
        else:
            qs = model.objects.all()
        return qs


class LatePermissionMixin():

    def get_model(self):
        if hasattr(self, 'model'):
            return self.model
        else:
            return super().get_model()

    def _get_perm(self):
        if not hasattr(self, 'permission_name'):
            permission_name = self.get_model().__name__.lower()
            if hasattr(self, 'permission_suffix'):
                permission_name = 'contacts.{permission}_{model}'.format(
                    model=permission_name,
                    permission=self.permission_suffix,
                )
        return permission_name

    def dispatch(self, request, *args, **kwargs):
        perm = self._get_perm()

        if not isinstance(perm, (list, tuple)):
            perms = (perm, )
        else:
            perms = perm
        # First check if the user has the permission (even anon users)
        if request.user.has_perms(perms):
            return super().dispatch(request, *args, **kwargs)
        # As the last resort, show the login form
        path = request.build_absolute_uri()
        resolved_login_url = resolve_url(settings.LOGIN_URL)
        # If the login url is the same scheme and net location then just
        # use the path as the "next" url.
        login_scheme, login_netloc = urlparse(resolved_login_url)[:2]
        current_scheme, current_netloc = urlparse(path)[:2]
        if ((not login_scheme or login_scheme == current_scheme) and
                (not login_netloc or login_netloc == current_netloc)):
            path = request.get_full_path()
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(
            path, resolved_login_url, REDIRECT_FIELD_NAME)

    def get_object(self, **filters):
        if len(filters) == 0:
            obj = super().get_object()
        else:
            obj = super().get_object(self.get_model().filter(**filters))
        if not self.request.user.has_perm(self._get_perm(), obj):
            resolved_login_url = resolve_url(settings.LOGIN_URL)
            path = self.request.build_absolute_uri()
            raise ForceResponse(redirect_to_login(path, resolved_login_url))
        return obj

    def get_queryset(self):
        model = self.get_model()
        if hasattr(model, 'get_queryset'):
            qs = model.get_queryset(self.request.user)
        return qs


class FormMixin():

    def get_form_class(self):
        """
        Returns the form class to use in this view.
        """
        if self.fields is not None and self.form_class:
            raise ImproperlyConfigured(
                "Specifying both 'fields' and 'form_class' is not permitted."
            )
        if self.form_class:
            return self.form_class
        else:
            if self.model is not None:
                # If a model has been explicitly provided, use it
                model = self.model
            elif hasattr(self, 'object') and self.object is not None:
                # If this view is operating on a single object, use
                # the class of that object
                model = self.object.__class__
            else:
                # Try to get a queryset and extract the model class
                # from that
                model = self.get_queryset().model

            if self.fields is None:
                raise ImproperlyConfigured(
                    "Using ModelFormMixin (base class of %s) without "
                    "the 'fields' attribute is prohibited."
                    % self.__class__.__name__
                )

            return model_forms.modelform_factory(model,
                                                 form=ModelForm,
                                                 fields=self.fields)

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        for field in form.fields.values():
            if isinstance(field, ModelChoiceField):
                if hasattr(field.queryset.model, 'get_queryset'):
                    field.queryset = field.queryset.model\
                        .get_queryset(self.request.user)
            elif isinstance(field, DateTimeField):
                field.widget = DateTimeWidget(usel10n=True,
                                              bootstrap_version=3)
            elif isinstance(field, DateField):
                field.widget = DateWidget(usel10n=True,
                                          bootstrap_version=3)
        return form


class SearchFormMixin(generic.edit.FormMixin):

    def get_form_kwargs(self):
        """
        Returns the keyword arguments for instantiating the form.
        """
        kwargs = {
            'initial': self.get_initial(),
            'prefix': self.get_prefix(),
            'request': self.request,
            'data': self.request.GET
        }

        return kwargs

    def get_queryset(self):
        model = self.get_model()
        qs = super().get_queryset()
        qs = self.get_form().search(qs)
        if 'order' in self.request.GET:
            order = self.request.GET['order']
            if order[0] == '-':
                order = order[1:]
            if '__' in order:
                order = order[:order.find('__')]
            if order in model._meta.get_all_field_names():
                self.order = self.request.GET['order']
                field = model._meta.get_field(order)
                if isinstance(field, ForeignKey):
                    if hasattr(field.rel.to._meta, 'ordering') and\
                            len(field.rel.to._meta.ordering) > 0:
                        qs = qs.order_by('{}__{}'.format(self.order,
                                         field.rel.to._meta.ordering[0]))
                    elif 'name' in field.rel.to._meta.get_all_field_names():
                        qs = qs.order_by('{}__name'.format(self.order))
                    else:
                        qs = qs.order_by(self.order)
                elif isinstance(field, ManyToManyRel) or\
                        isinstance(field, ManyToOneRel):
                    sign = self.order[0] if self.order[0] == '-' else ''
                    qs = qs.annotate(count_order=Count(order))\
                        .order_by('{}count_order'.format(sign))
                    pass
                elif isinstance(field, HStoreField):
                    try:
                        if self.order[0] == '-':
                            order = self.order[1:]
                            minus = '-'
                        else:
                            order = self.order
                            minus = ''
                        field, name = order.split('__')
                        field_name = '{}_{}'.format(field,
                                                    slugify(name)
                                                    .replace('-', '_'))
                        select = {field_name:
                                  "{}->'{}'".format(field, name)}
                        qs = qs.extra(select=select).order_by(
                            '{}{}'.format(minus, field_name))
                    except Exception as e:
                        import ipdb
                        ipdb.set_trace()
                else:
                    qs = qs.order_by(self.order)
        return qs

    def get(self, request, *args, **kwargs):
        # From ProcessFormMixin
        form_class = self.get_form_class()
        self.form = self.get_form(form_class)

        # From BaseListView
        self.object_list = self.get_queryset()
        allow_empty = self.get_allow_empty()
        if not allow_empty and len(self.object_list) == 0:
            raise Http404(
                _(u"Empty list and '%(class_name)s.allow_empty' is False.")
                % {'class_name': self.__class__.__name__})

        context = self.get_context_data(object_list=self.object_list,
                                        form=self.form)
        return self.render_to_response(context)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        self.form.full_clean()
        search_params = {k: self.form.data[k] for k, v in
                         self.form.cleaned_data.items()
                         if v not in [None, '']}
        if hasattr(self, 'order'):
            search_params['order'] = self.order
            context['order'] = self.order
        else:
            context['order'] = self.get_model()._meta.ordering[0]
        if len(search_params):
            context['querystring'] = urlencode(search_params)
            try:
                search_params.pop('order')
            except Exception:
                pass
            context['querystring_without_order'] = urlencode(search_params)
            if len(context['querystring_without_order']) > 0:
                context['querystring_without_order'] += '&'
        else:
            context['querystring_without_order'] = ''
        if self.form.is_submitted():
            context['add_search_form'] = SavedSearchForm()
            context['saved_search_url'] = resolve_url(
                'contacts:search-save',
                type=self.model._meta.model_name,
            ) + '?' + context['querystring']
        return context


class ListView(LoginRequiredMixin, PermissionMixin, generic.ListView):
    permission_suffix = 'view'


class DetailView(LoginRequiredMixin, PermissionMixin, generic.DetailView):
    permission_suffix = 'view'


class CreateView(LoginRequiredMixin, PermissionMixin, FormMixin,
                 generic.CreateView):
    permission_suffix = 'add'


class UpdateView(LoginRequiredMixin, PermissionMixin, FormMixin,
                 generic.UpdateView):
    permission_suffix = 'change'


class DeleteView(LoginRequiredMixin, PermissionMixin, generic.DeleteView):
    permission_suffix = 'delete'
