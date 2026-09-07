# battles/urls.py
from django.urls import path

from . import views

urlpatterns = [
    path("<int:wild_pokemon_id>/", views.start_battle, name="start_battle"),
    path("fight/", views.battle_view, name="battle_view"),
    path("move/<int:move_id>/", views.use_move, name="use_move"),
    path("switch/<int:pokemon_id>/", views.switch_pokemon, name="switch_pokemon"),
]
