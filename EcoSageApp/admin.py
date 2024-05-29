from django.contrib import admin

# Register your models here.
from .models import UserAccount, Transaction

admin.site.register(UserAccount)
admin.site.register(Transaction)