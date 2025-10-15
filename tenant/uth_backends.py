from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.hashers import check_password
from django.contrib.auth import get_user_model
from django.db import connection

class TenantAuthenticationBackend(ModelBackend):
    """
    Custom authentication backend for tenant-based authentication.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        # Ensure tenant schema is set
        if not connection.schema_name:
            return None

        # Use the custom or default User model
        User = get_user_model()

        try:
            # Fetch user within the current tenant schema
            user = User.objects.get(username=username)

            # Check if the provided password is correct
            if user and check_password(password, user.password):
                return user
        except User.DoesNotExist:
            return None
        return None

    def get_user(self, user_id):
        """
        Retrieve a user by their ID.
        """
        User = get_user_model()
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None