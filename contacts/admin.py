from django.contrib import admin

from .models import (
    Properties, Alert, ContactType, Company, Contact, MeetingType, Meeting,
    SavedSearch
)


@admin.register(Properties)
class PropertiesAdmin(admin.ModelAdmin):
    list_display = ('name', 'group', 'type', 'order', 'display_on_list')
    list_filter = ('group', 'type', 'display_on_list')
    search_fields = ('name', )


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('user', 'group', 'contact', 'priority', 'date',
                    'done')
    list_filter = ('user', 'priority', 'done', 'date')
    search_fields = ('contact__firstname', 'contact__lastname',
                     'user__username')

    def group(self, object):
        return object.contact.group
    group.short_description = 'Groupe'


@admin.register(ContactType)
class ContactTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'group')
    list_filter = ('group', )
    search_fields = ('name', )


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'group', 'type')
    list_filter = ('group', 'type')
    search_fields = ('name', )


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('firstname', 'lastname', 'company', 'group', 'type')
    list_filter = ('group', 'type')
    search_fields = ('firstname', 'lastname', 'company')


@admin.register(MeetingType)
class MeetingTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'group')
    list_filter = ('group', )
    search_fields = ('name', )


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ('author', 'group', 'contact', 'type', 'date')
    list_filter = ('author', 'type', 'date')
    search_fields = ('contact__firstname', 'contact__lastname',
                     'author__username')

    def group(self, object):
        return object.contact.group
    group.short_description = 'Groupe'


@admin.register(SavedSearch)
class SavedSearchAdmin(admin.ModelAdmin):
    list_display = ('name', 'group', 'type', 'results_count')
    list_filter = ('group', 'type')
    search_fields = ('name', )
