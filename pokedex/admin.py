from django.contrib import admin

from django.contrib import admin
from .models import Type, Move, Pokemon
# Register your models here.

admin.site.register(Type)
admin.site.register(Move)
admin.site.register(Pokemon)