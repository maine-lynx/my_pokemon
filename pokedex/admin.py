from django.contrib import admin

from .models import Move, Pokemon, Type

# Register your models here.

admin.site.register(Type)
admin.site.register(Move)
admin.site.register(Pokemon)
