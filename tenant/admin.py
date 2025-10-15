from django.contrib import admin
from django_tenants.admin import TenantAdminMixin

from tenant.models import *


admin.site.site_header = "Vendas_hub"
admin.site.site_title = " "
admin.site.index_title = "Vendas_hub Dashboard"

class DomainInline(admin.TabularInline):

    model = Domain
    max_num = 1

@admin.register(Orders)
class OrdersAdmin(TenantAdminMixin, admin.ModelAdmin):
        list_display = (
        "tenant",
        "customer",
        "id",
        "ordered_date",
        "payment_made",
        "shipped",
        )
        
@admin.register(uncompleted_order)
class uncompleted_orderAdmin(TenantAdminMixin, admin.ModelAdmin):
        list_display = (
        "tenant",
        "customer",
        "order_id",
        "ordered_date",
        "payment_made",
        "total_amount",
        "quantity",
        "complete",
        )
        
@admin.register(OrderItem)
class OrderItemsAdmin(TenantAdminMixin, admin.ModelAdmin):
        list_display = (
        "order",
        "product",
        "quantity",
        "date_added",
        "id",
        )
        
@admin.register(CartItem)
class CartItemAdmin(TenantAdminMixin, admin.ModelAdmin):
        list_display = (
        "user",
        "product",
        "quantity",
        "price",
        "payment_made",
        )
#         inlines = [DomainInline]
        
@admin.register(Domain)
class DomainAdmin(TenantAdminMixin, admin.ModelAdmin):
        pass
        # list_display = (
        # "id",
        # )

        
@admin.register(Tenant)
class TenantAdmin(TenantAdminMixin, admin.ModelAdmin):
        list_display = (
        "name",
        "schema_name",
        "created_on",
        "is_active",
        )
        inlines = [DomainInline]
        
@admin.register(Product)
class ProductAdmin(TenantAdminMixin, admin.ModelAdmin):
        list_display = (
        "name",
        "tenant",
        "stock",
        "image",
        "digital",
        "created_at",
        )
        
@admin.register(ShippingAddress)
class ShippingAddressAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ('customer','city','state','date_added' )
    
@admin.register(Invoice)
class InvoiceAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ('invoice_number','created_at','total_amount','is_paid' )
    
    

# admin.site.register(Orders)
# admin.site.register(OrderItem)
admin.site.register(UploadImage)
admin.site.register(Customer)