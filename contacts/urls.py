from django.conf.urls import url
from django.shortcuts import urlresolvers
from django.contrib.auth.views import (
    login, logout, password_reset, password_reset_complete,
    password_reset_confirm, password_reset_done
)

from . import views
from .models import SEARCH_CHOICES

saved_searches_types = '|'.join([c[0].lower() for c in SEARCH_CHOICES])


urlpatterns = [
    url(r'^$', views.Home.as_view(), name='home'),

    url(r'^(?P<type>(' + saved_searches_types + '))/import/?$',
        views.Import.as_view(),
        name='import'),
    url(r'^(?P<type>(' + saved_searches_types + '))/export/?$',
        views.Export.as_view(),
        name='export'),
    url(r'^/search/(?P<slug>[-\w]+)/export/?$',
        views.Export.as_view(),
        name='export'),
    url(r'^search/?$', views.ContactFastSearch.as_view(),
        name='fast-search'),

    url(r'^companies/?$', views.CompaniesList.as_view(), name='company-list'),
    url(r'^company/create/?$', views.CompanyCreation.as_view(),
        name='company-create'),
    url(r'^company/(?P<slug>[-\w]+)/?$', views.CompanyDetail.as_view(),
        name='company-detail'),
    url(r'^company/(?P<slug>[-\w]+)/update/?$', views.CompanyUpdate.as_view(),
        name='company-update'),
    url(r'^company/(?P<slug>[-\w]+)/delete/?$', views.CompanyDelete.as_view(),
        name='company-delete'),

    url(r'^contacts/?$',
        views.ContactList.as_view(),
        name='contact-list'),
    url(r'^company/(?P<company>[-\w]+)/contacts/?$',
        views.ContactList.as_view(),
        name='contact-list'),
    url(r'^company/(?P<company>[-\w]+)/contact/create/?$',
        views.ContactCreation.as_view(),
        name='contact-create'),
    url(r'^contact/(?P<slug>[-\w]+)/update/?$', views.ContactUpdate.as_view(),
        name='contact-update'),
    url(r'^contact/(?P<slug>[-\w]+)/delete/?$', views.ContactDelete.as_view(),
        name='contact-delete'),
    url(r'^contact/create/?$', views.ContactCreation.as_view(),
        name='contact-create'),
    url(r'^contact/(?P<slug>[-\w]+)/?$',
        views.ContactDetail.as_view(),
        name='contact-detail'),

    url(r'^meetings/?$',
        views.MeetingList.as_view(),
        name='meeting-list'),
    url(r'^company/(?P<company>[-\w]+)/meetings/?$',
        views.MeetingList.as_view(),
        name='meeting-list'),
    url(r'^contact/(?P<contact>[-\w]+)/meetings/?$',
        views.MeetingList.as_view(),
        name='meeting-list'),
    url(r'^company/(?P<company>[-\w]+)/meeting/create/?$',
        views.MeetingCreation.as_view(),
        name='meeting-create'),
    url(r'^contact/(?P<contact>[-\w]+)/meeting/create/?$',
        views.MeetingCreation.as_view(),
        name='meeting-create'),
    url(r'^meeting/(?P<pk>\d+)/update/?$', views.MeetingUpdate.as_view(),
        name='meeting-update'),
    url(r'^meeting/(?P<pk>\d+)/delete/?$', views.MeetingDelete.as_view(),
        name='meeting-delete'),
    url(r'^meeting/create/?$', views.MeetingCreation.as_view(),
        name='meeting-create'),
    url(r'^meeting/(?P<pk>\d+)/?$',
        views.MeetingDetail.as_view(),
        name='meeting-detail'),

    url(r'^alerts/?$',
        views.AlertList.as_view(),
        name='alert-list'),
    url(r'^company/(?P<company>[-\w]+)/alerts/?$',
        views.AlertList.as_view(),
        name='alert-list'),
    url(r'^contact/(?P<contact>[-\w]+)/alerts/?$',
        views.AlertList.as_view(),
        name='alert-list'),
    url(r'^alert/(?P<pk>\d+)/done/?$', views.AlertDone.as_view(),
        name='alert-done'),
    url(r'^company/(?P<company>[-\w]+)/alert/create/?$',
        views.AlertCreation.as_view(),
        name='alert-create'),
    url(r'^contact/(?P<contact>[-\w]+)/alert/create/?$',
        views.AlertCreation.as_view(),
        name='alert-create'),
    url(r'^alert/(?P<pk>\d+)/update/?$', views.AlertUpdate.as_view(),
        name='alert-update'),
    url(r'^alert/(?P<pk>\d+)/delete/?$', views.AlertDelete.as_view(),
        name='alert-delete'),
    url(r'^alert/create/?$', views.AlertCreation.as_view(),
        name='alert-create'),
    url(r'^alert/(?P<pk>\d+)/?$',
        views.AlertDetail.as_view(),
        name='alert-detail'),

    url(r'^search/(?P<type>\w+)/save/?$', views.SavedSearchCreation.as_view(),
        name='search-save'),
    url(r'^search/(?P<slug>[-\w]+)/?$', views.SavedSearchDetail.as_view(),
        name='search-detail'),
    url(r'^searches/(?P<type>(' + saved_searches_types + '))/?$',
        views.SavedSearchList.as_view(),
        name='search-list'),
    url(r'^searches/?$',
        views.SavedSearchList.as_view(),
        name='search-list'),
    url(r'^search/(?P<slug>[-\w]+)/update/?$',
        views.SavedSearchUpdate.as_view(),
        name='search-update'),
    url(r'^search/(?P<slug>[-\w]+)/delete/?$',
        views.SavedSearchDelete.as_view(),
        name='search-delete'),

    url(r'^group-change/(?P<pk>\d+)/?$',
        views.GroupChange.as_view(),
        name='group-change'),

    url(r'^login/?$', login, name='login'),
    url(r'^logout/?$', logout, {'template_name': 'registration/logout.html'},
        name='logout'),
    url(r'^password-reset/?$', password_reset,
        {'post_reset_redirect':
         urlresolvers.reverse_lazy('contacts:password_reset_done')},
        name='password_reset'),
    url(r'^password-reset/complete?$', password_reset_complete,
        name='password_reset_complete'),
    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/'
        '(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        password_reset_confirm,
        {'post_reset_redirect':
         urlresolvers.reverse_lazy('contacts:password_reset_complete')},
        name='password_reset_confirm'),
    url(r'^password-reset/done/?$', password_reset_done,
        name='password_reset_done'),

]
