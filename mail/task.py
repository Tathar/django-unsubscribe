from .models import UserMail, Excluded, Included, MailBox
 
from imapclient import IMAPClient, exceptions
import pyzmail
from bs4 import BeautifulSoup
import re
import email
from urllib import request
from collections import defaultdict
 
import copy
#from builtins import None
 
class MailTask(UserMail) :
    class Meta:
        proxy = True
         
    _mail_action = defaultdict(dict)
 
    def get_mail_action_numbers(self):
        return_dict = copy.deepcopy(self._mail_action[self.address])
          
        if "add" in self._mail_action[self.address].keys() :
            self._mail_action[self.address]["add"] = []
             
        if "del" in self._mail_action[self.address].keys() :
            self._mail_action[self.address]["del"] = []
 
        return return_dict
     
    def set_recheck_mail(self):
#        self._mail_action[self.address] = {}
        self._mail_action[self.address]["num"] = self.mailbox_set.count()
        return self._mail_action[self.address]["num"]
     
    def set_unsubscribe(self, selected_mail, password = None):
        if password != None :
            self.password = password
        self._mail_action[self.address]["num"] = len(selected_mail)
        self._mail_action[self.address]["unsubscribe"] = selected_mail
         
    def create(self, address ,serveur , SSL = True, password = None):
         
        usermail = super().create(address = address, serveur = serveur, SSL = SSL)
        usermail.password = password
         
        return usermail
         
         
    def get(self, address = None, pk = None, password = None):
         
        if address == None and pk == None :
            raise ValueError('need define "address" or "pk"')
         
        if (pk != None) :
            usermail = self.objects.get(pk = self.pk)
        elif (address != None) :
            usermail = self.objects.get(address = self.address)
             
        usermail.password = password
         
        return usermail
             
     
     
    def get_mail_check(self, password = None ,return_dict = None):
        """Get new mail Numbers"""
         
        if password != None :
            self.password = password
         
        if self.password == None :
            raise ValueError('Need define "Password"')
         
        if return_dict == None:
            return_dict = {"num": 0, "del": []}
             
        if not "del" in return_dict.keys() :
            return_dict["del"] = []
             
        if not "num" in return_dict.keys() :
            return_dict["num"] = 0
             
        if not self.address in self._mail_action.keys() :
            self._mail_action[self.address] = {"num": 0}

             
        server = IMAPClient(self.server, use_uid=True , ssl=self.SSL)
        try :
            server.login(self.address, password)
        except exceptions.LoginError as error :
            #print("login error")
            return_dict["status"] = "error"
            return_dict["error_message"] = str(error)
            return return_dict
 
        srv_inbox = server.select_folder('INBOX', readonly=True)
     
        UIDs = server.search([['UNSEEN'],[b'NOT', b'DELETED']])
        mailboxs = self.mailbox_set.all()
        old_UIDS = mailboxs.values("pk","UID")
     
        for old_UID in old_UIDS:
            """supression de la base de donné des mail qui ne sont plus dans la boite de reception (suprimés ou lus)"""
            if old_UID["UID"] not in UIDs:
                mailboxs.get(pk=old_UID["pk"]).delete()
                return_dict["del"].append( old_UID["pk"])
                if self._mail_action[self.address]["num"] > 0 :    
                    self._mail_action[self.address]["num"] -= 1
        #
        for UID in UIDs:
            """scrutation des mails non lu de la boite de reception"""
            nextUID = False
         
            for old_UID in old_UIDS:
                if old_UID["UID"] == UID:
                    """si le mail est deja present en base de donné il n'est pas traité"""
                    nextUID = True
                    break
            #
            if nextUID == True:
                continue
         
            self._mail_action[self.address]["num"] += 1
         
        return_dict["num"] = self._mail_action[self.address]["num"]
        return_dict["status"] = "ok"
        server.logout()
        return(return_dict)
     
     
    def get_new_spam(self, password = None ,return_dict = None):
        """Get new mail and define SPAM"""
         
        if password != None :
            self.password = password
         
        if self.password == None :
            raise ValueError('Need define "Password"')
         
        if return_dict == None:
            return_dict = {"add":[], "del":[]}
             
        if not "add" in return_dict.keys() :
            return_dict["add"] = []
             
        if not "del" in return_dict.keys() :
            return_dict["del"] = []
             
        if not self.address in self._mail_action.keys() :
            self._mail_action[self.address]["num"] = 0
             
        if not "add" in self._mail_action[self.address].keys() :
            self._mail_action[self.address]["add"] = []
             
        if not "del" in return_dict.keys() :
            self._mail_action[self.address]["del"] = []
         
        server = IMAPClient(self.server, use_uid=True , ssl=self.SSL)
        try :
            server.login(self.address, password)
        except exceptions.LoginError as error :
            #print("login error")
            return_dict["status"] = "error"
            return_dict["error_message"] = str(error)
            return return_dict
 
        srv_inbox = server.select_folder('INBOX', readonly=True)
     
        UIDs = server.search([['UNSEEN'],[b'NOT', b'DELETED']])
        mailboxs = self.mailbox_set.all()
        old_UIDS = mailboxs.values("pk","UID")
     
        for old_UID in old_UIDS:
            """supression de la base de donné des mail qui ne sont plus dans la boite de reception (suprimés ou lus)"""
            if old_UID["UID"] not in UIDs:
                mailboxs.get(pk=old_UID["pk"]).delete()
                return_dict["del"].append( old_UID["pk"])
                self._mail_action[self.address]["del"].append( old_UID["pk"])
                if self._mail_action[self.address]["num"] > 0 :    
                    self._mail_action[self.address]["num"] -= 1
                 
        #
        for UID in UIDs:
            """scrutation des mails non lu de la boite de reception"""
            nextUID = False
         
            for old_UID in old_UIDS:
                if old_UID["UID"] == UID:
                    """si le mail est deja present en base de donné il n'est pas traité"""
                    nextUID = True
                    break
            #
            if nextUID:
                continue
         
            """recuperation du corp du mail"""
            rawMessages = server.fetch(UID,['BODY[]'])
         
            message = pyzmail.PyzMessage.factory(rawMessages[UID][b'BODY[]'])
            senders = message.get_address('from')
            subject = message.get_subject()
         
            """creation de l'enregistrement dans la base de donnée"""
            tempmailbox = self.mailbox_set.create(UID= UID, sender=senders[1], subject=subject )
             
            mailbox = BoxTask.objects.get(pk=tempmailbox.pk)
             
            """verification si le mail est un spam"""
            (is_spam , url) = mailbox.set_spam( self.pk, message)
#            
         
            if is_spam :
                return_dict["add"].append({ "UID" :     UID,
                                           "sender" :  senders[1],
                                           "subject" : subject,
                                           "url" :     url,
                                           })
                 
                self._mail_action[self.address]["add"].append({ "UID" :     UID,
                                                                "sender" :  senders[1],
                                                                "subject" : subject,
                                                                "url" :     url,
                                                                })
                 
            if self._mail_action[self.address]["num"] > 0 :    
                self._mail_action[self.address]["num"] -= 1
 
 
        server.logout()
        return_dict["status"] = "ok"
        return(return_dict)
     
     
     
    def check_spam(self,password = None, return_dict = None ):
        """verification si les mail dejas présent en base de donnée sont des spam"""
        if password != None :
            self.password = password
         
        if self.password == None :
            raise ValueError('Need define "Password"')
 
             
        if return_dict == None:
            return_dict = {"add":[], "del":[]}
             
        if not "add" in return_dict.keys() :
            return_dict["add"] = []
             
        if not "del" in return_dict.keys() :
            return_dict["del"] = []
             
        server = IMAPClient(self.server, use_uid=True , ssl=self.SSL)
        try :
            server.login(self.address, self.password)
        except exceptions.LoginError as error :
            #print("login error")
            return_dict["status"] = "error"
            return_dict["error_message"] = str(error)
            return return_dict
 
        srv_inbox = server.select_folder('INBOX', readonly=True)
     
        UIDs = server.search([['UNSEEN'],[b'NOT', b'DELETED']])
        mailboxs = self.mailbox_set.all()
        old_UIDS = mailboxs.values("pk","UID")
     
        for old_UID in old_UIDS:
            if old_UID["UID"] not in UIDs:
                mailboxs.get(pk=old_UID["pk"]).delete()
                return_dict["del"].append( old_UID["pk"])
                self._mail_action[self.address]["del"].append( old_UID["pk"])
                if self._mail_action[self.address]["num"] > 0 :    
                    self._mail_action[self.address]["num"] -= 1
     
        old_UIDS = mailboxs.values("pk","UID")
        for UID in old_UIDS:
            rawMessages = server.fetch(UID["UID"],['BODY[]'])
         
            message = pyzmail.PyzMessage.factory(rawMessages[UID["UID"]][b'BODY[]'])
            senders = message.get_address('from')
            subject = message.get_subject()
         
            #mailbox = self.mailbox_set.get(pk=UID["pk"])
            mailbox = BoxTask.objects.get(pk=UID["pk"])
         
            """verification si le mail est un spam"""
            (is_spam , url) = mailbox.set_spam( self.pk, message)
             
            if is_spam :
                return_dict["add"].append({ "UID" :    UID["UID"],
                                           "sender" :  senders[1],
                                           "subject" : subject,
                                           "url" :     url
                                           })
                 
                if not "add" in self._mail_action[self.address].keys() :
                    self._mail_action[self.address]["add"]= []
                     
                self._mail_action[self.address]["add"].append({ "UID" :    UID["UID"],
                                                                "sender" :  senders[1],
                                                                "subject" : subject,
                                                                "url" :     url
                                                                })
            else :
                 
                return_dict["del"].append( UID["UID"])
                return_dict["del"].append( UID["UID"])
             
                 
            if self._mail_action[self.address]["num"] > 0 :    
                self._mail_action[self.address]["num"] -= 1
 
 
        server.logout()
        return_dict["status"] = "ok"
        return return_dict
 
    
    def unsubscribes(self, password = None , return_dict = None ):
        """desinscription et supression des spam"""
        if password != None :
            self.password = password
         
        if self.password == None :
            raise ValueError('Need define "Password"')
 
        if return_dict == None:
            return_dict = {"del":[]}
             
        if not "del" in return_dict.keys() :
            return_dict["del"] = []
             
        if not self.address in self._mail_action.keys() :
            self._mail_action[self.address] = {}
             
        if not "del" in self._mail_action[self.address].keys() :
            self._mail_action[self.address]["del"] = []
             
        if not "unsubscribe" in self._mail_action[self.address] :
            return_dict["status"] = "error"
            return_dict["error_message"] = "aucun message selectionné"
            return return_dict
             
        MBpks = self._mail_action[self.address]["unsubscribe"]
     
        server = IMAPClient(self.server, use_uid=True , ssl=self.SSL)
        server.login(self.address, self.password)
 
        srv_inbox = server.select_folder('INBOX', readonly=False)
     
        UIDs = server.search([['UNSEEN'],[b'NOT', b'DELETED']])
     
     
        for MBpk in MBpks:
            mail = BoxTask.objects.get(pk = MBpk)
            if mail.UID in UIDs:
                try:
                    req = request.urlopen(mail.url)
                except:
                    pass
             
                server.delete_messages(mail.UID)
                mail.delete()
                return_dict["del"].append(mail.UID)
                self._mail_action[self.address]["del"].append( mail.UID)
                 
                if self._mail_action[self.address]["num"] > 0 :    
                    self._mail_action[self.address]["num"] -= 1
                 
         
        return_dict["status"] = "ok"
        return return_dict
         
 
class BoxTask(MailBox) :
    class Meta:
        proxy = True
             
    def set_spam(self, UMPK,message):
     
     
        words_re = []
        for include_obj in Included.objects.all():
            words_re.append(re.compile(include_obj.word,re.I ))
 
        excludes_re = []
        #for exclude_obj in UserMail.objects.get(pk=UMpk).excluded_set.all():
        for exclude_obj in UserMail.objects.get(pk=UMPK).excluded_set.all():
            excludes_re.append(re.compile(exclude_obj.sender,re.I ))
 
        senders = message.get_address('from')
     
        for sender in senders:
            for exclude_re in excludes_re:
                if exclude_re.search(sender) is not None:
                    self.spam = False
                    self.save()
                    return([False, None])
 
        if message.html_part != None:
            try:
                list_u = message.get_decoded_header(name="List-Unsubscribe")
                list_u = list_u.split(",")
                for i in list_u:
                    if "http" in i:
                        try:
                            self.spam = True
                            try:
                                url = i.replace("<","").replace(">","")
                            except:
                                #print("split error")
                                pass
                            self.url = url
                            self.save()
                        except:
                            #print("mailbox error")
                            pass
                                 
                        return([True, url])
            except:
                #print("get List-Unsubscribre error ")
                pass
            try:
                content = message.html_part.get_payload().decode(message.html_part.charset)
                bsObj = BeautifulSoup(content,'html.parser')
                try:
                    links = bsObj.findAll("a")
                    for link in links:
                        for word_re in words_re:
                            if word_re.search(link.get_text()) is not None:
                                self.spam = True
                                self.url = link.attrs['href']
                                self.save()
                                return([True, url])
                                break     
                except Exception :
                    #print("Not <a>")
                    pass
            except Exception:
                #print('Not HTML')
                pass
             
        self.spam = False
        self.save()
        return([False, None])
     
 
 
 
 
 
#------------------------------------------------------------------------------
def check_spam(UMpk,password, usermail = None ):
    """verification si les mail dejas présent en base de donnée sont des spam"""
    if not usermail :
        usermail = UserMail.objects.get(pk=UMpk)
     
    server = IMAPClient(usermail.server, use_uid=True , ssl=usermail.SSL)
    server.login(usermail.address, password)
 
    srv_inbox = server.select_folder('INBOX', readonly=True)
     
    UIDs = server.search([['UNSEEN'],[b'NOT', b'DELETED']])
    mailboxs = usermail.mailbox_set.all()
    old_UIDS = mailboxs.values("pk","UID")
     
    for old_UID in old_UIDS:
        if old_UID["UID"] not in UIDs:
            mailboxs.get(pk=old_UID["pk"]).delete()
     
    old_UIDS = mailboxs.values("pk","UID")
    for UID in old_UIDS:
        rawMessages = server.fetch(UID["UID"],['BODY[]'])
         
        message = pyzmail.PyzMessage.factory(rawMessages[UID["UID"]][b'BODY[]'])
         
        mailbox = usermail.mailbox_set.get(pk=UID["pk"])
         
        set_spam(UMpk, mailbox, message)
         
         
    server.logout()
 
 
# todo
def get_spam(mypk, account, pwd, usermail = None):
#words = ["unsubscribe","désinscrire"]
#exludes = ["paypal","facebook","linkedin"]
    if not usermail :
        usermail = UserMail.objects.get(pk=mypk)
     
    words_re = []
    for include_obj in Included.objects.all():
        words_re.append(re.compile(include_obj.word,re.I ))
 
    excludes_re = []
    for exclude_obj in usermail.excluded_set.all():
        excludes_re.append(re.compile(exclude_obj.sender,re.I ))
 
#account = input('adresse：')
#pw = input('password：')
#account = "pe.douet@free.fr"
#pwd = "fj4rgxg6"
 
    imapObj = imapclient.IMAPClient(usermail.server, use_uid=True ,ssl=True)
    imapObj.login(account, pwd)
    imapObj.select_folder('INBOX', readonly=True)
 
    UIDs = imapObj.search(['UNSEEN'])
    rawMessages = imapObj.fetch(UIDs,['BODY[]'])
 
    sends = []
 
    for UID in UIDs:
        message = pyzmail.PyzMessage.factory(rawMessages[UID][b'BODY[]'])
        senders = message.get_address('from')
        next = False
        next_link = False
     
 
        for sender in senders:
            for exclude_re in excludes_re:
                if exclude_re.search(sender) is not None:
                    next = True 
                    break
            if next:
                break
             
        if next:
            continue
         
        if message.html_part != None:
            try:
                content = message.html_part.get_payload().decode(message.html_part.charset)
                bsObj = BeautifulSoup(content,'html.parser')
                try:
                    links = bsObj.findAll("a")
                    for link in links:
                        for word_re in words_re:
                            if word_re.search(link.get_text()) is not None:
                                url = link.attrs['href']
                                sends.append({"sender": sender, "subject": message.get_subject(),"url": url})
                                next_link = True
                                break 
                        if next_link: 
                            break     
                except Exception :
                    #print("Oups 1")
                    pass
                else:
                    pass
            except Exception:
                #print('Oups 2')
                pass
            else:
                pass
            finally:
                pass
             
     
 
    imapObj.logout() 
    #print(urls)
    return(sends)
 
def unsubscribes( UMpk, MBpks, password, usermail = None ):
     
    if not usermail :
        usermail = UserMail.objects.get(pk=UMpk)
     
    server = IMAPClient(usermail.server, use_uid=True , ssl=usermail.SSL)
    server.login(usermail.address, password)
 
    srv_inbox = server.select_folder('INBOX', readonly=False)
     
    UIDs = server.search([['UNSEEN'],[b'NOT', b'DELETED']])
     
     
    for MBpk in MBpks:
        mail = MailBox.objects.get(pk = MBpk)
        if mail.UID in UIDs:
            try:
                req = request.urlopen(mail.url)
            except:
                #print("resiliation impossible")
                pass
             
            server.delete_messages(mail.UID)
            mail.delete()
                 
     
#for url in urls:
#    webbrowser.open(url)
