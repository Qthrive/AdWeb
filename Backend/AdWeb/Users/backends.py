from django.contrib.auth.backends import BaseBackend
from .models import User

class EmailBackend(BaseBackend):
    def authenticate(self, request, email=None, password=None, **kwargs):
        if not email or not password:
            print("Email or password not provided.")
            return None
        try:
            user = User.objects.get(email=email)
            if user.check_password(password) and user.is_verified and user.is_active:
                return user
        except User.DoesNotExist:
            print("User with this email does not exist.")
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None