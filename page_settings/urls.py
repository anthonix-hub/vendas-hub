from django.urls import path
from .views import *
from . import views


app_name = 'page_settings'

urlpatterns = [
    path('settings_page', views.settings_page, name='settings_page'),
    path('delivery_methods/', views.delivery_methods_list, name='delivery_methods_list'),
    path('delivery_methods/new/', views.delivery_method_create, name='delivery_method_create'),
    path('delivery_methods/edit/<int:id>/', views.delivery_method_edit, name='delivery_method_edit'),
    path('delivery_methods/delete/<int:id>/', views.delivery_method_delete, name='delivery_method_delete'),
    
    
    path('settings/', views.settings, name='settings'),
 

]

