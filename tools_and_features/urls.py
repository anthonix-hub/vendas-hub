from django.urls import path
from subscription.views import *
from .views import *
from . import views



app_name = 'tools_andfeatures'

urlpatterns = [
    path('remove_bg', views.remove_bg, name='remove_bg'),
    path('useful_tools/', views.useful_tools, name='useful_tools'),    
    path("track_exit/", track_exit, name="track_exit"),
    # path("track_event/", track_event, name="track_event"),
    path('price_calculator/', views.price_calculator, name='price_calculator'),
]

