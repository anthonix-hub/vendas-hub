from django.urls import path
from subscription.views import *
from django.contrib.auth import views as auth_views

from . import views

app_name = 'subscription'

urlpatterns = [
    path('plans/', views.plan_view, name='plan_view'),
    path('select-plan/', views.select_plan, name='select_plan'),
    path('payment-options/<int:subscription_id>/', views.payment_options, name='payment_options'),
    path('payment/<int:plan_id>/', views.payment_page, name='payment_page'),
    
    # path('payment-pending/<int:payment_id>/', views.payment_pending, name='payment_pending'),
    path('payment_pending/', views.payment_pending, name='payment_pending'),
    
    # path('payment/', views.initialize_payment, name='initialize_payment'),
    path('initialize-payment/<int:subscription_id>/', views.initialize_payment, name='initialize_payment'),
    path('check-confirmation/<int:subscription_id>/', views.check_confirmation, name='check_confirmation'),
    path('free-plan-trial/', views.free_plan_trial, name='free_plan_trial'),    

    path('select-payment/', select_payment, name='select_payment'),
    path('bank-payment-pending/<str:transaction_reference>/', views.bank_payment_pending, name='bank_payment_pending'),
    path('check-payment-status/<str:transaction_reference>/', views.check_payment_status, name='check_payment_status'),

    # path('initialize-payment/', views.initialize_payment, name='initialize_payment'),
    path('verify-payment/', views.verify_payment, name='verify_payment'),
    
]