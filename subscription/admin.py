from django.contrib import admin
from subscription.models import SubscriptionPlan, Subscription, SubscriptionHistory, PaymentOption, Payment


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'duration', 'created_at', 'updated_at')
    list_filter = ('name',)
    search_fields = ('name',)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('tenant', 'plan', 'start_date', 'end_date', 'is_active', 'auto_renew')
    list_filter = ('plan', 'is_active', 'auto_renew')
    search_fields = ('tenant__name', 'plan__name')
    readonly_fields = ('end_date',)


@admin.register(SubscriptionHistory)
class SubscriptionHistoryAdmin(admin.ModelAdmin):
    list_display = ('tenant', 'plan', 'start_date', 'end_date', 'is_active', 'auto_renew')
    list_filter = ('plan', 'is_active', 'auto_renew')
    search_fields = ('tenant__name', 'plan__name')


@admin.register(PaymentOption)
class PaymentOptionAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('tenant', 'subscription', 'payment_option', 'amount', 'is_successful', 'created_at')
    list_filter = ('is_successful', 'payment_option')
    search_fields = ('transaction_reference',)
