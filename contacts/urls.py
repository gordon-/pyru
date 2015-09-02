from django.conf.urls import url
from django.contrib.auth.views import (
    login, logout, password_reset, password_reset_complete,
    password_reset_confirm, password_reset_done
)

from . import views


urlpatterns = [
    url(r'^$', views.Home.as_view(), name='home'),
    url(r'^companies/?$', views.CompaniesList.as_view(), name='company-list'),
    url(r'^company/create?$', views.CompanyCreation.as_view(),
        name='company-create'),
    url(r'^company/(?P<slug>[a-z-]+)/?$', views.CompanyDetail.as_view(),
        name='company-detail'),
    url(r'^login/?$', login, name='login'),
    url(r'^logout/?$', logout, name='logout'),
    url(r'^password-reset/?$', password_reset, name='password_reset'),
    url(r'^password-reset/complete?$', password_reset_complete,
        name='password_reset_complete'),
    url(r'^password-reset/confirm?$', password_reset_confirm,
        name='password_reset_confirm'),
    url(r'^password-reset/done?$', password_reset_done,
        name='password_reset_done'),
]
