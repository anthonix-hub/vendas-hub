from django import forms

from phonenumbers import is_valid_number, parse, NumberParseException
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from tenant.models import *

class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150, 
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Password'})
    )

# class SignupForm(UserCreationForm):
#     fullname = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Full Name'}))
#     phone_number = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Phone Number'}))
#     email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'Email'}))

#     class Meta:
#         model = CustomUser
#         fields = ['username', 'fullname', 'phone_number', 'email', 'password1', 'password2']
#         widgets = {
#             'username': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Username'}),
#             'password1': forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Password'}),
#             'password2': forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Confirm Password'}),
#         }
        
class CheckoutForm(forms.Form):
    payment_method = forms.ChoiceField(choices=[
        ('Credit Card', 'Credit Card'),
        ('PayPal', 'PayPal')
    ])
    
    
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'stock', 'image']
        

class UploadImageForm(forms.ModelForm):
    class Meta:
        model = UploadImage
        fields = ['image']
        
class CustomerForm(forms.ModelForm):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter username'}),
        required=True,
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password'}),
        required=True,
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password'}),
        required=True,
    )

    class Meta:
        model = Customer
        fields = ['name', 'email', 'phone_number']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter phone number'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data

    def clean_email(self):
        email = self.cleaned_data.get("email").lower()  # Normalize email
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already in use.")
        return email

class ManualInvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['order', 'invoice_number', 'due_date', 'total_amount', 'is_paid']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['order'].widget.attrs.update({'class': 'border rounded p-2 w-full'})
        self.fields['invoice_number'].widget.attrs.update({'class': 'border rounded p-2 w-full'})
        self.fields['due_date'].widget.attrs.update({'class': 'border rounded p-2 w-full'})
        self.fields['total_amount'].widget.attrs.update({'class': 'border rounded p-2 w-full'})
        self.fields['is_paid'].widget.attrs.update({'class': 'border rounded p-2 w-full'})
        
        
    # def clean_phone_number(self):
    #     phone_number = self.cleaned_data.get("phone_number")

    #     if not phone_number:
    #         raise forms.ValidationError("Ph
    #         # Parse and validate the phone number using `phonenumbers` library
    #         parsed_number = parse(phone_number, None)  # 'None' assumes international format
    #         if not is_valid_number(parsed_number):
    #             raise forms.ValidationError("Invalid phone number format.")
    #     except NumberParseException:
    #         raise forms.ValidationError("Invalid phone number format.")

    #     return phone_number

    

class ShippingAddressForm(forms.ModelForm):
    class Meta:
        model = ShippingAddress
        fields = ['address', 'city', 'state', 'country', 'zipcode']

# Removed duplicate definition of ManualInvoiceForm

# *********************************************************************
class TenantSignupForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    blog_name = forms.CharField(max_length=50)
    subdomain = forms.CharField(max_length=50)


class TenantLoginForm(forms.Form):
    username = forms.CharField(
        max_length=150, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )

