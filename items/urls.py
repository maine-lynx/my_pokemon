from django.urls import path
from . import views

urlpatterns = [
    path('', views.bag_view, name='bag_view'),
    path('use/<int:item_id>/', views.use_item, name='use_item'),
]