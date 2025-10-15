# from django import forms
# from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

# User = get_user_model()

# class CustomUserCreationForm(UserCreationForm):
#     # Add extra fields
#     # phone_number = forms.CharField(max_length=15, required=False, help_text="Optional.")
#     # address = forms.CharField(max_length=255, required=False, help_text="Optional.")
#     blog_name = forms.CharField(max_length=255, required=True, )

#     class Meta:
#         model = User
#         fields = ['email', 'username', 'first_name', 'last_name', 'password1', 'password2']
        
    # def save(self, commit=True):
    #     user = super().save(commit=False)
    #     # Perform any additional custom processing here
    #     user.phone_number = self.cleaned_data['phone_number']
    #     user.address = self.cleaned_data['address']
    #     if commit:
    #         user.save()
    #     return user

class CustomAuthenticationForm(AuthenticationForm):
    pass


from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    # blog_name = forms.CharField(max_length=255, required=True)
    # subdomain = forms.CharField(max_length=50, required=True)

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'username','password1', 'password2']
