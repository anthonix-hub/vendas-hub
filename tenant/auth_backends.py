# tenant/auth_backends.py

from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from tenant.models import Customer
from django_tenants.utils import schema_context


class TenantAuthenticationBackend(BaseBackend):
    """
    Custom authentication backend for a tenant project.
    """
    def authenticate(self, request, email=None, password=None, **kwargs):
        if not email or not password:
            return None

        try:
            # Get the tenant's schema from the request
            tenant_schema_name = request.tenant.schema_name

            # Switch to the tenant schema to find the Customer
            with schema_context(tenant_schema_name):
                customer = Customer.objects.get(email=email)

            # Switch to the public schema to verify the User
            with schema_context("public"):
                user = customer.user  # Fetch the User associated with the Customer

                # Check if the password is correct
                if user and user.check_password(password):
                    return user
        except (Customer.DoesNotExist, User.DoesNotExist):
            return None

    def get_user(self, user_id):
        """
        Retrieve a user by ID in the public schema.
        """
        try:
            with schema_context("public"):
                return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
