from django.db import models
from tenant.models import Tenant


class SetUpPage(models.Model):
    # Font Types
    FONT_SANS = 'font-sans'
    FONT_SERIF = 'font-serif'
    FONT_MONO = 'font-mono'

    FONT_TYPE_CHOICES = [
        (FONT_SANS, 'Sans Serif (font-sans)'),
        (FONT_SERIF, 'Serif (font-serif)'),
        (FONT_MONO, 'Monospace (font-mono)'),
    ]

    # Header/Footer Colors
    COLOR_GRAY = 'gray'
    COLOR_BLUE = 'blue'
    COLOR_YELLOW = 'yellow'
    COLOR_RED = 'red'
    COLOR_GREEN = 'green'
    COLOR_PURPLE = 'purple'
    COLOR_PINK = 'pink'
    COLOR_INDIGO = 'indigo'

    HEADER_FOOTER_COLOR_CHOICES = [
        (COLOR_GRAY, 'Gray'),
        (COLOR_BLUE, 'Blue'),
        (COLOR_YELLOW, 'Yellow'),
        (COLOR_RED, 'Red'),
        (COLOR_GREEN, 'Green'),
        (COLOR_PURPLE, 'Purple'),
        (COLOR_PINK, 'Pink'),
        (COLOR_INDIGO, 'Indigo'),
    ]

    # Color Shades
    SHADE_CHOICES = [
        ('50', '50'),
        ('100', '100'),
        ('200', '200'),
        ('300', '300'),
        ('400', '400'),
        ('500', '500'),
        ('600', '600'),
        ('700', '700'),
        ('800', '800'),
        ('900', '900'),
    ]

    # Additional Page Setup Fields
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    font_type = models.CharField(choices=FONT_TYPE_CHOICES, max_length=20, default=FONT_SANS)
    header_footer_color = models.CharField(choices=HEADER_FOOTER_COLOR_CHOICES, max_length=20, default=COLOR_GRAY)
    header_footer_color_shade = models.CharField(choices=SHADE_CHOICES, max_length=3, default='500')

    # Additional fields for customization
    logo = models.ImageField(upload_to="logos/", null=True, blank=True, help_text="Upload a logo for the page.")
    banner = models.ImageField(upload_to="banners/", null=True, blank=True, help_text="Upload a banner to display at the top of the page.")
    background_color = models.CharField(choices=HEADER_FOOTER_COLOR_CHOICES, max_length=20, default=COLOR_GRAY)
    background_color_shade = models.CharField(choices=SHADE_CHOICES, max_length=3, default='100')
    text_color = models.CharField(choices=HEADER_FOOTER_COLOR_CHOICES, max_length=20, default=COLOR_GRAY)
    text_color_shade = models.CharField(choices=SHADE_CHOICES, max_length=3, default='100')
    display_panel_color = models.CharField(choices=HEADER_FOOTER_COLOR_CHOICES, max_length=20, default=COLOR_GRAY)
    display_panel_color_shade = models.CharField(choices=SHADE_CHOICES, max_length=3, default='100')
    button_color = models.CharField(choices=HEADER_FOOTER_COLOR_CHOICES, max_length=20, default=COLOR_GREEN)
    button_color_shade = models.CharField(choices=SHADE_CHOICES, max_length=3, default='500')
    notification_msg = models.CharField(max_length=200, blank=True,null=True)
    whatsApp_number = models.IntegerField(default=+123456789) 
    custom_css = models.TextField(null=True, blank=True, help_text="Add custom CSS to override default styles.")

    # Created and updated timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Page Setup"
        verbose_name_plural = "Page Settings"

    def reset_to_default(self):
        """Reset fields to their default values."""
        self.font_type = self.FONT_SANS
        self.header_footer_color = self.COLOR_GRAY
        self.header_footer_color_shade = '200'
        self.background_color = self.COLOR_GRAY
        self.background_color_shade = '100'
        self.text_color = self.COLOR_GRAY
        self.text_color_shade = '800'
        self.display_panel_color = self.COLOR_GRAY
        self.display_panel_color_shade = '100'
        self.button_color = self.COLOR_GREEN
        self.button_color_shade = '500'
        self.notification_msg = ""
        self.whatsApp_number = +123456789
        self.custom_css = ""

        # Remove uploaded images
        self.logo.delete(save=False)  # Delete file but do not save immediately
        self.banner.delete(save=False)  

        self.save()

    def __str__(self):
        return f"Page Settings for {self.tenant.name}"
    
class DeliveryMethod(models.Model):
    # Relating to the tenant user
    tenant_user = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    
    # Basic delivery information
    delivery_point = models.CharField(max_length=250, default='free delivery', help_text="Location or method description")
    delivery_note = models.CharField(max_length=250, blank=True, help_text="Additional notes about the delivery")
    delivery_amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Delivery cost")
    
    # New fields for flexibility
    delivery_type_choices = [
        ('standard', 'Standard Delivery'),
        ('express', 'Express Delivery'),
        ('same_day', 'Same Day Delivery'),
        ('pickup', 'Pickup'),
    ]
    delivery_type = models.CharField(max_length=20, choices=delivery_type_choices, default='standard', help_text="Type of delivery service")

    estimated_delivery_time = models.CharField(max_length=100, blank=True, null=True, help_text="Estimated delivery time (e.g., 3-5 business days)")
    is_active = models.BooleanField(default=True, help_text="Enable or disable this delivery method")
    
    # Constraints and regions
    region_served = models.CharField(max_length=250, blank=True, help_text="Region or area served by this delivery method")
    max_weight_limit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Maximum weight limit for the delivery (in kg)")
    max_package_dimensions = models.CharField(max_length=100, blank=True, help_text="Maximum dimensions allowed for a package (e.g., LxWxH in cm)")

    # Time-related fields
    cutoff_time = models.TimeField(null=True, blank=True, help_text="Order cutoff time for same-day or next-day delivery")
    available_days = models.CharField(max_length=250, blank=True, help_text="Days when delivery is available (e.g., Mon-Fri)")

    # Tracking and handling
    supports_tracking = models.BooleanField(default=False, help_text="Indicates if this method supports tracking")
    handling_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Additional handling fee (if any)")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.delivery_type.capitalize()} ({self.delivery_point})"

    class Meta:
        verbose_name = "Delivery Method"
        verbose_name_plural = "Delivery Methods"