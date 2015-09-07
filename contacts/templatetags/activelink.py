from django.template import Library
from django.templatetags.future import url

from activelink.templatetags import activelink


register = Library()


class ActiveLinkStartsWithNode(activelink.ActiveLinkNodeBase):

    def is_active(self, request, path_to_check):
        path = request.resolver_match.view_name
        return path.startswith(path_to_check)


@register.tag
def ifactive(parser, token):
    return activelink.ifactive(parser, token)


@register.tag
def ifstartswith(parser, token):
    urlnode = url(parser, token)
    var, nodelist_true, nodelist_false = activelink.parse(parser, token,
                                                          'endifstartswith')
    return ActiveLinkStartsWithNode(urlnode, var, nodelist_true,
                                    nodelist_false)


@register.tag
def ifcontains(parser, token):
    return activelink.contains(parser, token)
