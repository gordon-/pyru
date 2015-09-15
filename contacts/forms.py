from autocomplete_light.forms import ModelForm

from .models import Contact


class ContactForm(ModelForm):

    class Meta:
        model = Contact
        fields = ('firstname', 'lastname', 'company', 'group', )
