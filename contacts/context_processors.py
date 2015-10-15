from .models import SavedSearch


def saved_searches(request):
    context = {}
    if request.user.is_authenticated():
        searches = SavedSearch.get_queryset(request.user)\
            .filter(display_in_menu=True)
        context['companies_displayed_searches'] = searches.filter(
            type='Company')
        context['contacts_displayed_searches'] = searches.filter(
            type='Contact')
        context['meetings_displayed_searches'] = searches.filter(
            type='Meeting')
        context['alerts_displayed_searches'] = searches.filter(type='Alert')
    return context


def default_group(request):
    context = {}
    if request.user.is_authenticated():
        default_group = request.user.default_group
        context['default_group'] = default_group.group
    return context
