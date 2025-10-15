from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from tenant.forms import TenantSignupForm
from tenant.models import *
from django.contrib import messages

from tenant.utils import register_user_and_tenant  # Assuming the function is properly defined in tenant.utils
def user_signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # Save the user
            user = form.save()
            # Log in the user after successful signup
            login(request, user)

            # Tenant data from form
            name = form.cleaned_data['username']
            email = form.cleaned_data['email']  # Get email from the form
            # Remove '-' and '_' from the username for subdomain
            subdomain = name.replace('-', '').replace('_', '')

            # Register the tenant
            tenant = register_user_and_tenant(name, subdomain, email)

            # Create domain for the tenant
            # tenant_domain = f"{subdomain}.192.168.1.140/"  # Replace with your domain logic
            tenant_domain = f"{subdomain}.localhost"  # Replace with your domain logic

            # Redirect to the tenant's domain subscription page
            return redirect(f"http://{tenant_domain}:8087/subscription/select-plan")
    else:
        form = CustomUserCreationForm()

    return render(request, 'accounts/signup.html', {'form': form})


# def user_login(request):
#     if request.method == 'POST':
#         # form = CustomAuthenticationForm(data=request.POST)
#         if form.is_valid():
#             user = form.get_user()
#             login(request, user)
#             # return redirect('tenant:tenant_dashboard')  # Redirect to tenant dashboard
#             return redirect('tenant:dashboard')  # Redirect to tenant dashboard
#     else:
#         form = CustomAuthenticationForm()

#     return render(request, 'accounts/login.html', {'form': form})


def user_login(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        if not email or not password:
            messages.error(request, "Email and password are required.")
            return render(request, "accounts/login.html")

        # Get the current tenant schema
        tenant = request.tenant
        print("Checking tenant<><><><>>1st>>", tenant)

        try:
            # Get the Customer object for the current tenant and email
            customer = Customer.objects.get(email=email, tenant=tenant)
            print("Checking customer<><><><2nd><<<<", customer)

            # Ensure the Customer has an associated User
            user = customer
            print("Checking user<><><>", user)
            
            if not user:
                messages.error(request, "This account is not properly configured. Please contact support.")
                return render(request, "accounts/login.html")

            # Authenticate the user by checking their password
            if user.check_password(password):
                # Set the backend explicitly to avoid multiple backend errors
                user.backend = "django.contrib.auth.backends.ModelBackend"

                # Log the user in
                login(request, user)
                messages.success(request, "You have successfully logged in.")
                return redirect("tenant:store")  # Replace with your desired redirect
            else:
                messages.error(request, "Invalid email or password.")
        except Customer.DoesNotExist:
            messages.error(request, "No account found with this email.")
        except Exception as e:
            messages.error(request, f"An unexpected error occurred: {e}")
            print(f"Login Exception: {e}")  # Debugging log

    return render(request, "accounts/login.html")