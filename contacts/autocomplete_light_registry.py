import autocomplete_light

from .models import Company, Contact


class ContactAutocomplete(autocomplete_light.AutocompleteModelBase):
    model = Contact
    search_fields = ['^firstname', 'lastname']
    attrs = {
        # This will set the input placeholder attribute:
        'placeholder': 'Nom du contact',
        # This will set the yourlabs.Autocomplete.minimumCharacters
        # options, the naming conversion is handled by jQuery
        'data-autocomplete-minimum-characters': 1,
    }
    # This will set the data-widget-maximum-values attribute on the
    # widget container element, and will be set to
    # yourlabs.Widget.maximumValues (jQuery handles the naming
    # conversion).
    widget_attrs = {
        'data-widget-maximum-values': 10,
        # Enable modern-style widget !
        'class': 'modern-style',
    }

    def choices_for_request(self):
        if not self.request.user.is_staff:
            self.choices = self.model.get_queryset(self.request.user,
                                                   self.choices)

        return super().choices_for_request()


class CompanyAutocomplete(autocomplete_light.AutocompleteModelBase):
    model = Company
    search_fields = ['^name']
    attrs = {
        'placeholder': 'Nom de la société',
        'data-autocomplete-minimum-characters': 1,
    }
    widget_attrs = {
        'data-widget-maximum-values': 10,
        'class': 'modern-style',
    }

    def choices_for_request(self):
        if not self.request.user.is_staff:
            self.choices = self.model.get_queryset(self.request.user,
                                                   self.choices)

        return super().choices_for_request()


autocomplete_light.register(ContactAutocomplete)
autocomplete_light.register(CompanyAutocomplete)
