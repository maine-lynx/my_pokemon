from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Trainer, OwnedPokemon

admin.site.register(Trainer)
admin.site.register(OwnedPokemon)