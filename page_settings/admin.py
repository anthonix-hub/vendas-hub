from django.contrib import admin
from .models import *
from django.utils.html import format_html
from django.urls import reverse    
from django.shortcuts import redirect
    
    

@admin.register(SetUpPage)
class SetUpPageAdmin(admin.ModelAdmin):
    list_display = (
        'tenant',
        'font_type',
        'header_footer_color',
        'header_footer_color_shade',
        'background_color',
        'background_color_shade',
        'button_color',
        'button_color_shade',
        'created_at',
        'updated_at',
    )
    list_filter = ('font_type', 'header_footer_color', 'background_color', 'button_color')
    search_fields = ('tenant__name',)
    
    actions = ["reset_to_default_action"]

    @admin.action(description="Reset selected pages to default settings")
    def reset_to_default_action(self, request, queryset):
        for setup in queryset:
            setup.reset_to_default()
        self.message_user(request, "Selected pages have been reset to default.")
    readonly_fields = ["reset_button"]

    def reset_button(self, obj):
        if obj.pk:
            return format_html(
                '<a class="button" href="{}" style="color: white; background: red; padding: 5px 10px; border-radius: 5px;">Reset to Default</a>',
                reverse("admin:reset_setup_page", args=[obj.pk])
            )
        return "Save the object first to enable reset."

    reset_button.short_description = "Reset Page"

    def get_urls(self):
        from django.urls import path

        urls = super().get_urls()
        custom_urls = [
            path(
                "reset/<int:pk>/",
                self.admin_site.admin_view(self.reset_page),
                name="reset_setup_page",
            ),
        ]
        return custom_urls + urls

    def reset_page(self, request, pk):
        setup_page = self.get_object(request, pk)
        if setup_page:
            setup_page.reset_to_default()
        return redirect(request.META.get("HTTP_REFERER", "admin:app_setup_page_changelist"))    
    
    

@admin.register(DeliveryMethod)
class Delivery_methodAdmin(admin.ModelAdmin):
    list_display = (
        'tenant_user','delivery_point', 
        'delivery_amount', 'delivery_type', 'estimated_delivery_time'
        ,'region_served',
    )
    search_fields = ('tenant__name',)