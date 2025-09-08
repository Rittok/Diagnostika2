from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

UserModel = get_user_model()
class EmailAuthBackend(ModelBackend):
      
    def authenticate(self, request, username=None, **kwargs):
        
        try:
            user = UserModel.objects.get(email__iexact=username)
            return user
        except UserModel.DoesNotExist:
            return None
    
    def get_user(self, user_id):
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None