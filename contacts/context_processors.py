from .models import SavedSearch


def saved_searches(request):
    searches = SavedSearch.get_queryset(request.user)\
        .filter(display_in_menu=True)
    context = {}
    context['companies_displayed_searches'] = searches.filter(type='Company')
    context['contacts_displayed_searches'] = searches.filter(type='Contact')
    context['meetings_displayed_searches'] = searches.filter(type='Meeting')
    context['alerts_displayed_searches'] = searches.filter(type='Alert')
    return context


def default_group(request):
    context = {}
    default_group = request.user.default_group
    context['default_group'] = default_group.group
    return context
