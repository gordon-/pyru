from django.contrib.auth.decorators import login_required, permission_required
from django.views import generic
from django.contrib.auth.views import redirect_to_login
from django.conf import settings
from django.shortcuts import resolve_url


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


class ListView(LoginRequiredMixin, PermissionMixin, generic.ListView):
    permission_suffix = 'view'


class DetailView(LoginRequiredMixin, PermissionMixin, generic.DetailView):
    permission_suffix = 'view'


class CreateView(LoginRequiredMixin, PermissionMixin, generic.CreateView):
    permission_suffix = 'add'


class UpdateView(LoginRequiredMixin, PermissionMixin, generic.UpdateView):
    permission_suffix = 'change'


class DeleteView(LoginRequiredMixin, PermissionMixin, generic.DeleteView):
    permission_suffix = 'delete'
