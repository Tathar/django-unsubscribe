from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django import forms

import re


# Create your models here.
class UserMail(models.Model):
    address = models.CharField(max_length=64,blank=False, unique = True) #AA:BB:CC:DD:EE:FF
    server = models.CharField(max_length=254)
    SSL = models.BooleanField()
    lastview = models.DateField(auto_now = True)
    
    def __str__(self):
        return self.address
    
    def get_absolute_url(self):
        return reverse('mail:detail', kwargs={'pk': self.pk})

class Excluded(models.Model):
    userMail = models.ForeignKey(UserMail, on_delete=models.CASCADE)
    sender = models.CharField(max_length=64,blank=False,verbose_name="Adresse", help_text="adresse mail a exclure")
    def __str__(self):
        return self.sender
        
class Included(models.Model):
    word = models.CharField(max_length=64,blank=False)
    def __str__(self):
        return self.word
    
    def clean(self):
        
        words_re = []
        for include_obj in Included.objects.all():
            words_re.append(re.compile(include_obj.word,re.I |re.A))
        
        for word_re in words_re:
            if word_re.search(self.word) is not None:
                raise ValidationError(_('ce mot est deja defini'))
            
        
        word_re = re.compile(self.word,re.I|re.A)
        
        for var in Included.objects.all():
            if word_re.search(var.word) is not None:
                var.delete()
         
    
class MailBox(models.Model):
    userMail = models.ForeignKey(UserMail, on_delete=models.CASCADE)
    UID = models.IntegerField()
    sender = models.CharField(max_length=64) #IPv4 or IPv6
    subject = models.CharField(max_length=68)
    spam = models.BooleanField(blank=True, null=True)
    url = models.CharField(max_length=256,blank=True, null=True)
    def __str__(self):
        return str(self.UID) + "(" + self.sender + ")"
    
