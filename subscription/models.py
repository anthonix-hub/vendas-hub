from django.db import models
from tenant.models import Tenant
from django.utils.timezone import now
from datetime import timedelta
import uuid

def generate_reference():
    return str(uuid.uuid4())

# Subscription Plan Model
class SubscriptionPlan(models.Model):
    FREE_PLAN = 'free_plan'
    BASIC_PLAN = 'basic_plan'
    STANDARD_PLAN = 'standard_plan'
    PREMIUM_PLAN = 'premium_plan'

    PLAN_CHOICES = [
        (FREE_PLAN, 'Free Plan'),
        (BASIC_PLAN, 'Basic Plan'),
        (STANDARD_PLAN, 'Standard Plan'),
        (PREMIUM_PLAN, 'Premium Plan'),
    ]

    name = models.CharField(
        max_length=20,
        choices=PLAN_CHOICES,
        unique=True,
        help_text="The name of the subscription plan."
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="A brief description of the plan."
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="The price of the subscription plan."
    )
    duration = models.PositiveIntegerField(
        help_text="Duration of the subscription plan in days."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_name_display()} - ${self.price}"

    class Meta:
        verbose_name = "Subscription Plan"
        verbose_name_plural = "Subscription Plans"


# Subscription Model
class Subscription(models.Model):
    tenant = models.OneToOneField(
        Tenant,
        on_delete=models.CASCADE,
        related_name='subscription',
        help_text="The tenant this subscription belongs to."
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.SET_NULL,
        null=True,
        related_name="subscriptions",
        help_text="The subscription plan selected by the tenant."
    )
    start_date = models.DateTimeField(
        default=now,
        help_text="Start date of the subscription."
    )
    end_date = models.DateTimeField(
        blank=True,
        null=True,
        help_text="End date of the subscription. Calculated based on start date and plan duration."
    )
    is_active = models.BooleanField(
        default=False,
        help_text="Whether the subscription is currently active."
    )
    auto_renew = models.BooleanField(
        default=False,
        help_text="Whether the subscription will automatically renew after expiration."
    )
    created_at = models.DateTimeField(auto_now_add=True, help_text="Date and time when the subscription was created.")
    updated_at = models.DateTimeField(auto_now=True, help_text="Date and time when the subscription was last updated.")

    def save(self, *args, **kwargs):
        if self.plan and self.start_date:
            self.end_date = self.start_date + timedelta(days=self.plan.duration)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.tenant} - {self.plan}"

    class Meta:
        verbose_name = "Subscription"
        verbose_name_plural = "Subscriptions"


# Subscription History Model
class SubscriptionHistory(models.Model):
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='subscription_history',
        help_text="The tenant this subscription history belongs to."
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.SET_NULL,
        null=True,
        related_name="subscription_history",
        help_text="The subscription plan for this history entry."
    )
    start_date = models.DateTimeField(help_text="Start date of the subscription.")
    end_date = models.DateTimeField(blank=True, null=True, help_text="End date of the subscription.")
    is_active = models.BooleanField(default=True, help_text="Whether the subscription was active at the time of logging.")
    auto_renew = models.BooleanField(default=False, help_text="Whether the subscription was set to auto-renew.")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Date and time when this history entry was created.")

    def __str__(self):
        return f"History - {self.tenant} - {self.plan}"

    class Meta:
        verbose_name = "Subscription History"
        verbose_name_plural = "Subscription Histories"
        ordering = ['-created_at']


# Payment Option Model
class PaymentOption(models.Model):
    BANK_TRANSFER = 'bank_transfer'
    PAYSTACK = 'paystack'
    PAYPAL = 'paypal'
    FLUTTERWAVE = 'flutterwave'
    STRIPE = 'stripe'

    PAYMENT_METHODS = [
        (BANK_TRANSFER, 'Bank Transfer'),
        (PAYSTACK, 'Paystack'),
        (PAYPAL, 'PayPal'),
        (FLUTTERWAVE, 'Flutterwave'),
        (STRIPE, 'Stripe'),
    ]

    name = models.CharField(
        max_length=50,
        choices=PAYMENT_METHODS,
        unique=True,
        help_text="The payment method name."
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Additional details about the payment option."
    )
    is_active = models.BooleanField(default=True, help_text="Whether this payment option is currently available.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.get_name_display()

    class Meta:
        verbose_name = "Payment Option"
        verbose_name_plural = "Payment Options"


# Payment Model
class Payment(models.Model):
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='payments',
        help_text="The tenant making the payment."
    )
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name='payments',
        help_text="The subscription this payment is related to."
    )
    payment_option = models.ForeignKey(
        PaymentOption,
        on_delete=models.SET_NULL,
        null=True,
        help_text="The payment method used for this transaction."
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="The amount paid.")
    transaction_reference = models.CharField(max_length=255, blank=True, null=True, unique=True, help_text="The reference number for the transaction.")
    is_successful = models.BooleanField(default=False, help_text="Whether the payment was successful.")
    processed = models.BooleanField(default=False)  # New field to track processing state
    payment_rejected = models.BooleanField(default=False)  # New field to track processing state
    created_at = models.DateTimeField(auto_now_add=True, help_text="Date and time when the payment was made.")
    updated_at = models.DateTimeField(auto_now=True, help_text="Date and time when the payment was last updated.")

    def __str__(self):
        return f"{self.tenant} - {self.amount} - {self.payment_option}"

    class Meta:
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
