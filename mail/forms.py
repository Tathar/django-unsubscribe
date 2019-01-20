from django import forms
from django.forms import inlineformset_factory
from .models import UserMail, Excluded

# from djangoformsetjs.utils import formset_media_js



class NewUserMail(forms.Form):
    address = forms.CharField(max_length=64, label='Adresse Mail')
    password = forms.CharField(label='Mot de passe', max_length=100,widget=forms.PasswordInput())
    server = forms.CharField(max_length=254, label='Adresse du serveur IMAP')
    SSL = forms.BooleanField(initial=True,required=False, label='connection au serveur sécurisé (SSL)')
     
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['address'].widget.attrs.update({'placeholder': 'address'})
        self.fields['password'].widget.attrs.update({'placeholder': 'password'})
        self.fields['server'].widget.attrs.update({'placeholder': 'IMAP server'})


class EditUserMail(NewUserMail):
    password = forms.CharField(required = False, label='Mot de passe', max_length=100,widget=forms.PasswordInput())
 
# ExcludedInlineFormset = inlineformset_factory(
#     UserMail,
#     model = Excluded,
#     fields=('sender', ),
#     extra=1,
#     widgets={'sender': forms.TextInput(attrs={
#             'class': 'form-control',
#             'placeholder': 'Enter exclude mail address'
#         })
#     }
# )
 
from django.forms.models import inlineformset_factory

ExcludedFormSet = inlineformset_factory(UserMail, Excluded, fields = ('sender',), extra=1, can_delete=True )
