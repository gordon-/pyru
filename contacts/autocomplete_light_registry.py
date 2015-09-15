import autocomplete_light.shortcuts as al
from .models import Company, Contact

al.register(
    Contact,
    search_fields=['^firstname', 'lastname'],
    attrs={
        # This will set the input placeholder attribute:
        'placeholder': 'Nom du contact',
        # This will set the yourlabs.Autocomplete.minimumCharacters
        # options, the naming conversion is handled by jQuery
        'data-autocomplete-minimum-characters': 1,
    },
    # This will set the data-widget-maximum-values attribute on the
    # widget container element, and will be set to
    # yourlabs.Widget.maximumValues (jQuery handles the naming
    # conversion).
    widget_attrs={
        'data-widget-maximum-values': 10,
        # Enable modern-style widget !
        'class': 'modern-style',
    },
)

al.register(
    Company,
    search_fields=['^name'],
    attrs={
        # This will set the input placeholder attribute:
        'placeholder': 'Nom de la société',
        # This will set the yourlabs.Autocomplete.minimumCharacters
        # options, the naming conversion is handled by jQuery
        'data-autocomplete-minimum-characters': 1,
    },
    # This will set the data-widget-maximum-values attribute on the
    # widget container element, and will be set to
    # yourlabs.Widget.maximumValues (jQuery handles the naming
    # conversion).
    widget_attrs={
        'data-widget-maximum-values': 10,
        # Enable modern-style widget !
        'class': 'modern-style',
    },
)

al.register(Company)
# al.register(Contact)
