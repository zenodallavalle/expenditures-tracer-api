from django.contrib import admin
from .models import Database, Cash, Category, Expenditure
# Register your models here.

admin.site.register(Database)
admin.site.register(Cash)
admin.site.register(Category)
admin.site.register(Expenditure)