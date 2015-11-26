from django.contrib.auth.models import Group

from .models import DefaultGroup


class DefaultGroupMiddleware:

    def process_request(self, request):
        try:
            if request.user.is_authenticated():
                request.user.default_group
        except DefaultGroup.DoesNotExist:
            if request.user.groups.count() == 0:
                group = Group(name=request.user.username)
                group.save()
                request.user.groups.add(group)
            DefaultGroup.objects.create(
                user=request.user,
                group=request.user.groups.first())
