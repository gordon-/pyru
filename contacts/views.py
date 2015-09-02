from django.views import generic

from .mixins import LoginRequiredMixin
from .models import (
    Properties, Alert, ContactType, Company, Contact, MeetingType, Meeting
)


class Home(LoginRequiredMixin, generic.ListView):

    model = Alert

    def get_queryset(self):
        return self.model.objects.filter(user=self.request.user)\
            .order_by('-date')


class CompaniesList(LoginRequiredMixin, generic.ListView):

    model = Company

    def get_queryset(self):
        # todo: add filtering/ordering support
        return self.model.filter(group__in=self.request.user.groups.all())\
            .order_by('name')


class CompanyDetail(LoginRequiredMixin, generic.DetailView):

    model = Company


class CompanyCreation(LoginRequiredMixin, generic.CreateView):

    model = Company
    fields = ('name', )

    def get_form(self, form_class):
        pass
