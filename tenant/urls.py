from django.urls import path
from . import views

from django.contrib.auth import views as auth_views
from tools_and_features.views import *
from .views import *



app_name = 'tenant'

urlpatterns = [
    # path('signup/', views.tenant_signup, name='tenant_signup'),
    
    
    path('', views.landing_page, name='landing_page'),
    path('index', views.landing_page2, name='landing_page2'),
    path('store', views.store, name='store'),
    path('cart', views.cart, name='cart'),
    # path("update_cart/", views.update_cart, name="update_cart"),
    path('checkout/', views.checkout, name='checkout'),
    path("order_confirmation/<int:order_id>/", views.order_confirmation, name="order_confirmation"),
    path('add_to_cart/', views.add_to_cart, name='add_to_cart'),
    path('order_history/', views.order_history, name='order_history'),
    path('mark_received/<int:order_id>/', views.mark_received, name='mark_received'),
    path('mark_received/<int:order_id>/', views.mark_received, name='mark_received'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/orders_chart_data/', views.orders_chart_data, name='orders_chart_data'),
    path('error/', views.error, name='error'),
    
    path('shipping_adddressCheck/', views.shipping_adddressCheck, name='shipping_adddressCheck'),
    path("add-shipping-address/", views.add_shipping_address, name="add_shipping_address"),
    path('update-shipping-address/', UpdateShippingAddress.as_view(), name='update_shipping_address'),
    
    # path('user_payment/', user_payment.as_view(), name='user_payment'),
    path('user_payment/<int:order_id>/', views.user_payment, name='user_payment'),
    path("bank_payment/<int:order_id>/", views.bank_payment, name="bank_payment"),
    path('check-payment-status/<str:order_id>/', views.check_payment_status, name='check_payment_status'),
    
    path("paystack_callback/<int:order_id>/", views.paystack_callback, name="paystack_callback"),
    
    
    # path('accounts/login/', views.login_view, name='login'),
    # path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    
    path('remove_bg', remove_bg, name='remove_bg'),
    
    path('export/csv/', views.export_users_csv, name='export_users_csv'),
    # path('export/pdf/', views.export_users_pdf, name='export_users_pdf'),   
    
    path('dashboard/products/', views.product_list, name='admin_product_list'),
    path('dashboard/products/create/', views.product_create, name='admin_product_create'),
    path('dashboard/products/<int:product_id>/update/', views.product_update, name='admin_product_update'),
    path('dashboard/products/<int:product_id>/delete/', views.product_delete, name='admin_product_delete'),
    path('dashboard/customers/', customer_list_view, name='customer_list_view'),
    path('dashboard/infograph/', infograph, name='infograph'),
    path('dashboard/analytics/', analytics, name='analytics'),
    
    path('dashboard/inventory/', inventory_view, name='inventory'),
    path('adjust-stock/<int:product_id>/', views.adjust_stock, name='adjust_stock'),
    
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/<int:invoice_id>/', views.invoice_detail, name='invoice_detail'),
    path('invoices/create/', views.create_manual_invoice, name='create_manual_invoice'),
    path('invoices/<int:invoice_id>/download/', views.download_invoice, name='download_invoice'),

    # path("track_exit/", track_exit, name="track_exit"),
    path("track_event/", track_event, name="track_event"),
    
    path('search/', views.search_products, name='search_products'),
    
    path('create_customer/', create_customer, name='create_customer'),
    path('login/', user_login, name='user_login'),
    
]

