from django.db import models
from tenant.models import Tenant
from django.contrib.auth.models import User
from django.utils.timezone import now

class UploadImage(models.Model):
    image = models.ImageField(upload_to="uploads/")
    processed_image = models.ImageField(upload_to="processed/", blank=True, null=True)

    def __str__(self):
        return self.image.name


class StoreVisit(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=255)  # Unique session to avoid duplicate tracking
    ip_address = models.GenericIPAddressField()
    city = models.CharField(max_length=100, blank=True, null=True)
    region = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    user_agent = models.TextField()
    visit_time = models.DateTimeField(auto_now_add=True)
    duration = models.IntegerField(null=True, blank=True)  # Store duration in seconds

from django.db import models

class UserEvent(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=255, null=True, blank=True)
    event_type = models.CharField(max_length=255)
    product_id = models.IntegerField(null=True, blank=True)
    product_name = models.CharField(max_length=255, null=True, blank=True)
    product_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    click_time = models.DateTimeField(auto_now_add=True)
    user_agent = models.TextField(null=True, blank=True)
    
    # IP and Location Fields
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    country_code = models.CharField(max_length=10, null=True, blank=True)
    region = models.CharField(max_length=100, null=True, blank=True)
    region_name = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    zip_code = models.CharField(max_length=20, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    timezone = models.CharField(max_length=100, null=True, blank=True)
    isp = models.CharField(max_length=255, null=True, blank=True)
    org = models.CharField(max_length=255, null=True, blank=True)
    asn = models.CharField(max_length=255, null=True, blank=True)  # 'as' field from API
    
