from django.db import models
from django.contrib.auth.models import User
from django_tenants.models import DomainMixin, TenantMixin
from phonenumber_field.modelfields import PhoneNumberField
from django.utils.timezone import now
from django.db.models import UniqueConstraint


class Tenant(TenantMixin):
    name = models.CharField(max_length=255, unique=True)
    email = models.EmailField()
    schema_name = models.CharField(max_length=63, unique=True)
    created_on = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    auto_create_schema = True
    auto_drop_schema = False

    def __str__(self):
        return self.name

    @property
    def customer_count(self):
        return self.customers.count()


class Domain(DomainMixin):
    pass


class Customer(models.Model):
    user = models.OneToOneField(User, null=False, blank=False, on_delete=models.CASCADE)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="customers", db_index=True
    )
    name = models.CharField(max_length=300)
    email = models.CharField(max_length=300)
    phone_number = PhoneNumberField(blank=True, null=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.name

    class Meta:
        constraints = [
            UniqueConstraint(fields=['email', 'tenant'], name='unique_customer_email_per_tenant')
        ]

class Product(models.Model):
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="products"
    )
    name = models.CharField(max_length=50, null=True)
    price = models.FloatField()
    image = models.ImageField(null=True, blank=True)
    digital = models.BooleanField(default=False, null=True, blank=True)
    description = models.TextField(blank=True, max_length=250)
    stock = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @property
    def imageURL(self):
        try:
            url = self.image.url
        except:
            url = ""
        return url

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Product"
        verbose_name_plural = "Products"

class ShippingAddress(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True)
    address = models.CharField(max_length=400)
    city = models.CharField(max_length=400)
    state = models.CharField(max_length=400)
    country = models.CharField(max_length=100, null=False, blank=False)
    zipcode = models.CharField(max_length=400)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.address

class Orders(models.Model):
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="orders"
    )
    customer = models.ForeignKey(
        Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders"
    )
    Customers_address = models.ForeignKey(ShippingAddress, on_delete=models.CASCADE)
    ordered_date = models.DateTimeField(auto_now_add=True)
    received = models.BooleanField(default=False)
    received_date = models.DateTimeField(null=True, blank=True)
    shipped = models.BooleanField(default=False)
    payment_made = models.BooleanField(default=False)
    payment_reference = models.CharField(max_length=100, null=True, blank=True)
    payment_method = models.CharField(
        max_length=20, choices=[("paystack", "Paystack"), ("bank", "Bank Transfer")], null=True, blank=True
    )
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    complete = models.BooleanField(default=False)

    def __str__(self):
        
        return str(self.id)

    @property
    def get_cart_total(self):
        """
        Calculate the total price of all items in the cart.
        """
        total = sum([item.get_total() for item in self.items.all()])
        return total

    @property
    def get_cart_items(self):
        """
        Calculate the total quantity of all items in the cart.
        """
        total = sum([item.quantity for item in self.items.all()])
        return total

class uncompleted_order(models.Model):
    tenant = models.CharField(max_length=100)
    customer = models.CharField(max_length=100)
    order_id = models.IntegerField()
    ordered_date = models.DateTimeField()
    payment_made = models.BooleanField(default=False)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    complete = models.BooleanField(default=False)
    product = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField(default=1)
    
class OrderItem(models.Model):
    order = models.ForeignKey(
        'Orders',
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        
        return f"{self.product.name} (x{self.quantity})"

    def get_total(self):
        """
        Calculate the total price for this item.
        """
        return self.product.price * self.quantity

class CartItem(models.Model):
    user = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    payment_made = models.BooleanField(default=False)

    def get_total(self):
        return self.price * self.quantity

class UploadImage(models.Model):
    image = models.ImageField(upload_to="uploads/")
    processed_image = models.ImageField(upload_to="processed/", blank=True, null=True)

    def __str__(self):
        return self.image.name

class InventoryAudit(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="audits")
    action = models.CharField(max_length=50)  # E.g., 'Stock Added', 'Stock Removed', 'Sale', 'Damaged'
    quantity_changed = models.IntegerField()  # Positive or negative changes
    current_stock = models.IntegerField()  # Stock after the change
    reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.product.name} - {self.action}"


class HistoricData(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="history")
    date = models.DateField(auto_now_add=True)
    stock = models.IntegerField()
    sales = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} - {self.date}"

class StoreVisit(models.Model):
    session_id = models.CharField(max_length=255, unique=True)
    duration = models.IntegerField(default=0)  # Duration in seconds
    end_time = models.DateTimeField(null=True, blank=True)
    # Add other fields as necessary, e.g., start_time, user_agent, etc.

    def __str__(self):
        return f"Session {self.session_id} - Duration: {self.duration} seconds"

class Invoice(models.Model):
    order = models.OneToOneField('Orders', on_delete=models.CASCADE, related_name='invoice')
    invoice_number = models.CharField(max_length=20, unique=True)
    created_at = models.DateTimeField(default=now)
    due_date = models.DateTimeField(null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)

    def __str__(self):
        return f"Invoice #{self.invoice_number} for Order #{self.order.id}"