from django.contrib import admin

# Register your models here.
from .models import OwnedPokemon, Trainer

admin.site.register(Trainer)
admin.site.register(OwnedPokemon)
