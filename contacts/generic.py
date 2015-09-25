from django.http import Http404
from django.utils.http import urlencode
from django.utils.translation import ugettext as _
from django.core.exceptions import ImproperlyConfigured
from django.forms import models as model_forms
from django.contrib.auth.decorators import login_required, permission_required
from django.views import generic
from django.contrib.auth.views import redirect_to_login
from django.conf import settings
from django.shortcuts import resolve_url
from django.forms import ModelChoiceField, DateTimeField, DateField
from datetimewidget.widgets import DateTimeWidget, DateWidget
from autocomplete_light.forms import ModelForm


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
    def _get_perm(cls):
        if not hasattr(cls, 'permission_name'):
            permission_name = cls.model.__name__.lower()
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
            obj = super().get_object(self.model.filter(**filters))
        if not self.request.user.has_perm(self._get_perm(), obj):
            resolved_login_url = resolve_url(settings.LOGIN_URL)
            path = self.request.build_absolute_uri()
            raise ForceResponse(redirect_to_login(path, resolved_login_url))
        return obj

    def get_queryset(self):
        if hasattr(self.model, 'get_queryset'):
            qs = self.model.get_queryset(self.request.user)
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
        qs = super().get_queryset()
        qs = self.get_form().search(qs)
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
        search_params = {k: v for k, v in self.form.cleaned_data.items()
                         if v not in [None, '']}
        if len(search_params):
            context['querystring'] = urlencode(search_params)
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
