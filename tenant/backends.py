from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class EmailBackend(ModelBackend):
    """
    Custom authentication backend that allows users to log in with their email and password.
    """
    def authenticate(self, request, username=None, email=None, password=None, **kwargs):
        if email is None:
            email = kwargs.get('email')

        try:
            user = User.objects.get(email=email)  # Check if a user exists with the provided email
        except User.DoesNotExist:
            return None

        # Verify the password
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
