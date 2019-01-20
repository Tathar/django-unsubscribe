import os, sys

proj_path = "/home/ini/make/eclipse/unsubscribe/"
# This is so Django knows where to find stuff.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "unsubscribe.settings")
sys.path.append(proj_path)

# This is so my local_settings.py gets loaded.
os.chdir(proj_path)

# This is so models get loaded.
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from mail.models import UserMail

print (UserMail.objects.get(pk=1).server)

