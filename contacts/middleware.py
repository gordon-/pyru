from .models import DefaultGroup


class DefaultGroupMiddleware:

    def process_request(self, request):
        try:
            if request.user.is_authenticated():
                request.user.default_group
        except DefaultGroup.DoesNotExist:
            DefaultGroup.objects.create(
                user=request.user,
                group=request.user.groups.first())
