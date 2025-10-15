from django.contrib import admin
from django_tenants.admin import TenantAdminMixin
from .models import *


@admin.register(UploadImage)
class ShippingAddressAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ('image','processed_image')
    
@admin.register(UserEvent)
class ShippingAddressAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ('city', 'country_code' , 'region_name' ,'product_id', 'product_name', 'click_time', 'ip_address' ,'event_type','session_id',)
    
@admin.register(StoreVisit)
class ShippingAddressAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ('city','ip_address','session_id',)
    
    