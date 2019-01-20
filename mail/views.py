#from django.shortcuts import render
#from django.urls import include
# Create your views here.

from django.http import HttpResponseRedirect, JsonResponse
#from django.http import HttpResponse
#from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.views import generic
#from django.views.generic.edit import CreateView, DeleteView, UpdateView
#from django.shortcuts import redirect

#from django.views.generic.base import TemplateView


#from django import forms


from mail.task import MailTask
from mail.models import UserMail, Included
from .forms import NewUserMail, ExcludedFormSet, EditUserMail

#from imapclient import exceptions 
from datetime import datetime, timedelta
#from gc import get_objects

from .mixin import ajaxGetMixin, ObjectFormView


"""clean Usermail and MailBox over 30 day"""
_how_many_days = 30


"""
<form action=index/ method="post">
{% csrf_token %}
<input type="hidden" name="start" value="N/A" /> </form>
<script type="text/javascript"> document.form1.submit();
"""


class IndexView(generic.ListView):
    template_name = 'mail/index.html'
    context_object_name = 'ViewAllMailAddress'

    def get_queryset(self):
        return UserMail.objects.all()
 

    def get_context_data(self, **kwargs):
        
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
#        Add in a QuerySet of all the books
#        context['excluded_list'] = self.object.excluded_set.all()
#        context['included_list'] = Included.objects.all()
#        context['spam']=  self.object.mailbox_set.filter(spam = True)
        rem = []
        pks = []
        try:
            for var in self.request.session.get('mail_address').keys() :
                try:
                    mail = UserMail.objects.get(address = var)
                    pks.append(mail.pk)
                except (KeyError, UserMail.DoesNotExist):
                    rem.append(var)

            context['pks'] = pks
            
            if len(rem) > 0:
                if len(rem) == len(self.request.session.get('mail_address').keys()) :
                    del self.request.session['mail_address']
                else:
                    mail_address = self.request.session['mail_address']
                    for var in rem :
                        del mail_address[var]
                        
            
        except:
            context['pks'] = []
            #pass
        
        """delete to old UserMail"""   
        mails = UserMail.objects.filter(lastview__lte=datetime.now()-timedelta(days=_how_many_days))
        for mail in mails:
            mail.delete()
            
        return context 

#todo  need decorate vue with vary_on_headers('X-Requested-With')
class MyDetailView(ajaxGetMixin ,generic.DetailView):
    model = MailTask
    template_name = 'mail/detail.html'
    pk_url_kwarg = 'usermail_pk'
    
    def get_context_data(self, **kwargs):
        
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        
        # Add in a QuerySet of all the books
        context['excluded_list'] = self.object.excluded_set.all()
        context['included_list'] = Included.objects.all()
        context['spam']=  self.object.mailbox_set.filter(spam = True)
        return context
        
    def ajax_load(self, request, *args, **kwargs) :
        cookie = self.request.session.get('mail_address')
        self.object = self.get_object()
        ret = self.object.get_mail_check( cookie[self.object.address] )
        return JsonResponse(ret)
    
    def ajax_get_new_mail_numbers(self, request, *args, **kwargs) :
        self.object = self.get_object()
        ret = self.object.get_mail_action_numbers()
        ret["status"] = "ok"
        return JsonResponse(ret)
  
    def ajax_action(self, request, *args, **kwargs) :
        cookie = self.request.session.get('mail_address')
        self.object = self.get_object()
        ret = self.object.get_new_spam( cookie[self.object.address] )
        return JsonResponse(ret)
        

class RemoveMail(generic.edit.DeleteView):
    model = UserMail
    success_url = reverse_lazy('mail:index')
    pk_url_kwarg = 'usermail_pk'
    
    def delete(self, request, *args, **kwargs):
        cookie = request.session.get('mail_address')
        self.object = self.get_object()
        del cookie[self.object.address]
        request.session['mail_address'] = cookie
        return super().delete(request, *args, **kwargs)


class CheckSpam(ajaxGetMixin ,generic.DetailView):
    model = MailTask
    template_name = 'mail/detail.html'
    pk_url_kwarg = 'usermail_pk'
    
    def get_context_data(self, **kwargs):
        
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        
        context['spam']=  self.object.mailbox_set.filter(spam = True)
        return context
    
    def ajax_load(self, request, *args, **kwargs) :
        self.object = self.get_object()
        nbmail = self.object.set_recheck_mail()
        ret = {"status":    "ok",
               "num":       nbmail
               }
        return JsonResponse(ret)
    
    def ajax_get_new_mail_numbers(self, request, *args, **kwargs) :
        self.object = self.get_object()
        ret = self.object.get_mail_action_numbers()
        ret["status"] = "ok"
        return JsonResponse(ret)
  
    def ajax_action(self, request, *args, **kwargs) :
        cookie = self.request.session.get('mail_address')
        self.object = self.get_object()
        ret = self.object.check_spam( cookie[self.object.address] )
        return JsonResponse(ret)
      

class Unsubscribe(ajaxGetMixin ,generic.DetailView):
    model = MailTask
    template_name = 'mail/detail.html'
    pk_url_kwarg = 'usermail_pk'
    
    def get_context_data(self, **kwargs):
        
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        
        # Add in a QuerySet of all the books
        context['excluded_list'] = self.object.excluded_set.all()
        context['included_list'] = Included.objects.all()
        context['spam']=  self.object.mailbox_set.filter(spam = True)
        return context
    
    def post(self, request, *args, **kwargs):
        """ unsubscribe selected mail"""
        self.object = self.get_object()
        self.object.save() #mise a jour du champ lastview
        
        selected_mail = request.POST.getlist('mail')
        if not selected_mail :
        # Redisplay the question voting form.
            context = self.get_context_data()
            context['question'] = "mail"
            context['error_message'] = "You didn't select a choice."
            return HttpResponseRedirect(reverse('mail:detail', args=(self.object.pk,)))
            
        cookie = request.session.get('mail_address')
        self.object.set_unsubscribe(selected_mail)
        return HttpResponseRedirect(reverse('mail:unsubscribe', args=(self.object.pk,)))

    def ajax_load(self, request, *args, **kwargs) :
        cookie = self.request.session.get('mail_address')
        self.object = self.get_object()
        ret = self.object.get_mail_check( cookie[self.object.address] )
            
        return JsonResponse(ret)
    
    def ajax_get_new_mail_numbers(self, request, *args, **kwargs) :
        self.object = self.get_object()
        ret = self.object.get_mail_action_numbers()
        ret["status"] = "ok"
        return JsonResponse(ret)
  
    def ajax_action(self, request, *args, **kwargs) :
        cookie = self.request.session.get('mail_address')
        self.object = self.get_object()
        ret = self.object.unsubscribes(cookie[self.object.address])
        return JsonResponse(ret)


class NewServerView(ObjectFormView):
    
    form_class = NewUserMail
    template_name = "mail/usermail_form.html"
    success_url = reverse_lazy('mail:index')
    
    model = MailTask
    pk_url_kwarg = 'usermail_pk'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
#         if self.request.POST:
#             context['excluded_formset'] = ExcludedFormSet(self.request.POST)
#         else:
#             context['excluded_formset'] = ExcludedFormSet()
            
            
        return context
    
    def form_valid(self, form):
        
        context = self.get_context_data()
        formset = context['excluded_formset']
        
        if formset.is_valid():

            mail_address =  form.cleaned_data['address']
            password =      form.cleaned_data['password']
            server_address =form.cleaned_data['server']
            SSL =           form.cleaned_data['SSL']
               
            address = None
           
            self.object = self.get_object()
           
            if self.object :
                """mise a jour d'un serveur (formulaire d'edition)"""
                self.object.address = mail_address
                self.object.server = server_address
                self.object.SSL = SSL
               
                if password != "" :
                    self.request.session['mail_address'][mail_address] = password
               
                return super().form_valid(form)
           
            else :   
               
                mail, created = UserMail.objects.get_or_create(address = mail_address, defaults={"server": server_address, "SSL": SSL} )
        
                if 'mail_address' in self.request.session :
                    session_mail_address = self.request.session['mail_address']
                else :
                    session_mail_address = None
        
                if created and password == "" :
                    form.fields["password"].required = True
                    return self.form_invalid(form)
                                  
                elif session_mail_address == None and password != "" :
                    """no session, create it"""
                    session_mail_address = {mail_address : password}
                    self.request.session['mail_address'] = session_mail_address
                   
                elif password != "" :
                    """have session , password is defined, update it"""
                    session_mail_address[mail_address] = password
                    self.request.session['mail_address'] = session_mail_address
                    
                formset.instance = mail
                formset.save()
                       
                return super().form_valid(form)
        else :
            return self.form_invalid(form)
            
    def form_invalid(self, form):
        """If the form is invalid, render the invalid form."""
        self.object = self.get_object()
        return self.render_to_response(self.get_context_data(form=form))       

    def get(self, request, *args, **kwargs):
        
        self.object = self.get_object()
        
        if (self.object) :
            self.initial["address"] = self.object.address
            self.initial["server"] = self.object.server
            self.initial["SSL"] = self.object.SSL      
            if 'form' not in kwargs:
                kwargs['form'] = self.get_form()
            kwargs['form'].fields["password"].required = False
        else :
            self.initial = {}
            if 'form' not in kwargs:
                kwargs['form'] = self.get_form()
            kwargs['form'].fields["password"].required = True
            
        
        return self.render_to_response(self.get_context_data(**kwargs))
    
class EditServerView(ObjectFormView):
    form_class = EditUserMail
    template_name = "mail/usermail_form.html"
    success_url = reverse_lazy('mail:index')
    
    model = MailTask
    pk_url_kwarg = 'usermail_pk'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
#         if self.request.POST:
#             context['excluded_formset'] = ExcludedFormSet(self.request.POST, instance=self.object)
#             context['excluded_formset'].full_clean()
#         else:
#             context['excluded_formset'] = ExcludedFormSet(instance=self.object)
        return context
    
    def form_valid(self, form):
        
        self.object = self.get_object()
        context = self.get_context_data()
        formset = context['excluded_formset']
        
        if formset.is_valid():

            mail_address =  form.cleaned_data['address']
            password =      form.cleaned_data['password']
            server_address =form.cleaned_data['server']
            SSL =           form.cleaned_data['SSL']
               
            address = None
           
            self.object = self.get_object()
            if self.object :
                """mise a jour d'un serveur (formulaire d'edition)"""
                self.object.address = mail_address
                self.object.server = server_address
                self.object.SSL = SSL
                               
                if password != "" :
                    cookie = self.request.session['mail_address']
                    cookie[mail_address] = password
                    self.request.session['mail_address'] = cookie
                    
                formset.instance = self.object
                formset.save()
               
                return super().form_valid(form)
           
            else :
                return super().form_invalid(form)

        else :
            return self.form_invalid(form)
            
    def form_invalid(self, form):
        """If the form is invalid, render the invalid form."""
        self.object = self.get_object()
        return self.render_to_response(self.get_context_data(form=form))       

    def get(self, request, *args, **kwargs):
        
        self.object = self.get_object()
        
        if (self.object) :
            self.initial["address"] = self.object.address
            self.initial["server"] = self.object.server
            self.initial["SSL"] = self.object.SSL      
            
        
        return self.render_to_response(self.get_context_data(**kwargs))
