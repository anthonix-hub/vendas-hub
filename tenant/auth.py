from django.contrib.auth.models import User
from .models import Customer
from django_tenants.utils import schema_context

def authenticate_customer(email, password, tenant_schema_name):
    """
    Custom authentication function to verify a Customer's email and password.
    """
    try:
        # Switch to the tenant's schema to get the Customer
        with schema_context(tenant_schema_name):
            customer = Customer.objects.get(email=email)

        # Switch to the public schema to validate the User
        with schema_context("public"):
            user = customer.user  # Access the associated User object
            if user and user.check_password(password):  # Validate the password
                return user
    except (Customer.DoesNotExist, User.DoesNotExist):
        return None  # Return None if Customer or User does not exist
