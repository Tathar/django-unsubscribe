from django.urls import path

from . import views

app_name = 'mail'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
#    path('addserver/', views.add_MailServer, name='addserver'),
#    path('addserver/', views.EditServerView.as_view(), name='addserver'),
    path('addserver/', views.NewServerView.as_view(), name='addserver'),
    path('<int:usermail_pk>/edit/', views.EditServerView.as_view(), name='editserver'),
    path('<int:usermail_pk>/', views.MyDetailView.as_view(), name='detail'),
    path('<int:usermail_pk>/detail/', views.MyDetailView.as_view(), name='detail'),
    path('<int:usermail_pk>/remmail/', views.RemoveMail.as_view(), name='remmail'),
    path('<int:usermail_pk>/checkspam/', views.CheckSpam.as_view(), name='checkspam'),
    path('<int:usermail_pk>/unsubscribe/', views.Unsubscribe.as_view(), name='unsubscribe'),
]


from sitetree.sitetreeapp import register_dynamic_trees, compose_dynamic_tree
from sitetree.utils import tree, item
  
  
register_dynamic_trees(
  
    # or even define a tree right at the process of registration.
    compose_dynamic_tree((
        tree("maintree", title='A bas le SPAM !', items=(
            item('Home', 'mail:index', url_as_pattern=True, children=(
                item('Add Server', 'mail:addserver'),
                item('Mail Detail', 'mail:detail mailtask.pk', url_as_pattern=True, in_menu=False, children=(
                    item('Check all spam', 'mail:checkspam mailtask.pk', url_as_pattern=True),
                    item('Unsubscribe', 'mail:unsubscribe mailtask.pk', in_menu=False, url_as_pattern=True),
                    item('Edit Mail Server', 'mail:editserver mailtask.pk', url_as_pattern=True),
                    item(' Remove Mail Address', 'mail:remmail usermail.pk', url_as_pattern=True)
                )),
            )),
        )),
    )),
  
    # Line below tells sitetree to drop and recreate cache, so that all newly registered
    # dynamic trees are rendered immediately.
    reset_cache=True
)