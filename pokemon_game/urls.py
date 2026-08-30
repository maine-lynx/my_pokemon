from django.urls import path
from . import views

app_name = 'pokemon_game'

urlpatterns = [
    path('', views.home, name='home'),
    path("new-game/", views.new_game, name='new_game'),
]