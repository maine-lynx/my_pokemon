# battles/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('<int:wild_pokemon_id>/', views.start_battle, name='start_battle'),        # GET /battle/
    path('fight/', views.battle_view, name='battle_view'),    # GET /battle/fight/
    path('move/<int:move_id>/', views.use_move, name='use_move'),  # POST /battle/move/1/
]