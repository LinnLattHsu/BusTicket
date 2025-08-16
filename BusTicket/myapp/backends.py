from django.contrib.auth.hashers import check_password
from .models import Admin, User  # Import your custom models

class MyCustomAuthBackend:
    """
    Authenticates against both the custom Admin model and the custom User model
    using the 'email' field.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        # Authenticate against the Admin model first
        try:
            admin = Admin.objects.get(email=username)
            if check_password(password, admin.password):
                return admin
        except Admin.DoesNotExist:
            pass # No admin found, continue to check regular users

        # Fallback to your custom User model
        try:
            user = User.objects.get(email=username)
            if check_password(password, user.password):
                return user
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        # This is for session management.
        try:
            return Admin.objects.get(pk=user_id)
        except Admin.DoesNotExist:
            try:
                return User.objects.get(pk=user_id)
            except User.DoesNotExist:
                return None
