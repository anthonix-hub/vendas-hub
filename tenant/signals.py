from django.db.models.signals import post_save
from django.dispatch import receiver
from tenant.models import Tenant, Orders, Invoice
from page_settings.models import SetUpPage
import uuid
from datetime import now, timedelta

@receiver(post_save, sender=Tenant)
def create_default_setup_page(sender, instance, created, **kwargs):
    if created:
        # Ensure the SetUpPage model is imported correctly
        SetUpPage.objects.create(
            tenant=instance,
            font_type=SetUpPage.FONT_SANS,
            header_footer_color=SetUpPage.COLOR_GRAY,
            header_footer_color_shade='500',
            background_color=SetUpPage.COLOR_GRAY,
            background_color_shade='100',
            button_color=SetUpPage.COLOR_GREEN,
            button_color_shade='500',
            
        )


receiver(post_save, sender=Orders)
def create_invoice_for_order(sender, instance, created, **kwargs):
    if created:
        Invoice.objects.create(
            order=instance,
            invoice_number=str(uuid.uuid4())[:8],  # Generate a unique invoice number
            total_amount=instance.total_amount,
            due_date=now() + timedelta(days=30)  # Example: 30 days from creation
        )