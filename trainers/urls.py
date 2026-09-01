# trainers/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.trainer_profile, name='trainer_profile'),
    path('new-game/', views.new_game, name='new_game'),
]