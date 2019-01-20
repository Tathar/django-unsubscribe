from django.contrib import admin


from .models import UserMail, Excluded, Included, MailBox


class IncludedAdmin(admin.ModelAdmin):
    model = Included

class ExcludedAdmin(admin.TabularInline):
    model = Excluded

class MailBoxAdmin(admin.ModelAdmin):
    model = MailBox
    
class UserMailAdmin(admin.ModelAdmin):
    inlines = [
        ExcludedAdmin,
    ]



admin.site.register(UserMail, UserMailAdmin)
admin.site.register(Included, IncludedAdmin)
admin.site.register(MailBox, MailBoxAdmin)
