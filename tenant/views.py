# c:\Users\HP\Desktop\pyprog\webprojects\saasy\tenant\views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model, login, authenticate

from tenant.utils import register_user_and_tenant  # The registration utility function

User = get_user_model()

from django.db import transaction, IntegrityError, models

from django.http import JsonResponse, HttpResponseForbidden, HttpResponse, FileResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse, reverse_lazy

from django.db.models.functions import TruncDay, TruncMonth
from django.db.models import Sum, Count, Q, DecimalField, F, Case, Value, When

from datetime import datetime, timedelta, date
from django.utils import timezone
from django.utils.timezone import now

from django.contrib import messages

from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt

import csv
import reportlab
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

import json
from .models import *
from page_settings.models import *
from tools_and_features.models import UserEvent, StoreVisit
from subscription.views import *
from .forms import *

from tenant.auth_backends import TenantAuthenticationBackend
from django_tenants.utils import schema_context

from django.core.validators import validate_email, validate_ipv46_address
from django.core.exceptions import ValidationError
from phonenumbers import parse as parse_phone, is_valid_number, NumberParseException

from django.template.loader import get_template
from django.utils.formats import date_format # For formatting dates nicely


import os
import requests
import pandas as pd
from django.core.files.storage import default_storage
from django.conf import settings

from django.views.generic.edit import UpdateView

from django.contrib.auth.mixins import LoginRequiredMixin

# templatetags/multiply_filter.py
from django import template
from django.core.serializers.json import DjangoJSONEncoder

register = template.Library()

@register.filter
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

def landing_page(request):
    return render(request,'tenant/index.html',None)
def landing_page2(request):
    return render(request,'tenant/index2.html',None)


def store(request):
    # Set visit start time if not already set
    if "visit_start_time" not in request.session:
        request.session["visit_start_time"] = datetime.now().isoformat()

    # Safely retrieve 'email_or_phone' from the session
    active_mail_phone = request.session.get("email_or_phone", None)

    # Filter products by the current tenant
    current_tenant = request.tenant  # This is populated by `django-tenants` middleware
    products = Product.objects.filter(tenant=current_tenant)

    # Filter customers for the current tenant
    current_customer = Customer.objects.filter(tenant=current_tenant)

    # Get cart items count
    cartItems = get_cart_items_count(request)  # Ensure it returns an integer

    # Pagination to display 8 items per page.
    paginator = Paginator(products, 8)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    page_setup = SetUpPage.objects.filter(tenant=current_tenant).first()  # Get the first setup page for the tenant


    return render(request, 'tenant/store.html', {
        'products': products,
        'cartItems': cartItems,  # This is an integer now
        'current_tenant': current_tenant,
        'current_customer': current_customer,
        'active_mail_phone': active_mail_phone,
        'page_obj': page_obj,
        'paginator': paginator,
        'page_setup': page_setup,
    })



# View Cart Page
def view_cart(request):
    # Retrieve the cart (unpaid order items for the user)
    if request.user.is_authenticated:
        # This logic seems incorrect for fetching cart items, it fetches order items
        # Assuming you want to show items from the session cart even for logged-in users before checkout
        cart = request.session.get("cart", {})
        unpaid_orders = []
        total_items = 0
        total_amount = 0.0

        for product_id, details in cart.items():
            try:
                product = Product.objects.get(id=product_id)
                unpaid_orders.append({
                    "product": product,
                    "quantity": details["quantity"],
                    "get_total": float(details["price"]) * details["quantity"], # Ensure float calculation
                })
                total_items += details["quantity"]
                total_amount += float(details["price"]) * details["quantity"]
            except Product.DoesNotExist:
                # Handle case where product might have been deleted
                # Remove from session cart?
                pass
            except (KeyError, ValueError, TypeError):
                 # Handle potential issues with cart data structure or types
                 pass

    else:
        # If user is not authenticated, fallback to session-based cart
        cart = request.session.get("cart", {})
        unpaid_orders = []
        total_items = 0
        total_amount = 0.0

        for product_id, details in cart.items():
            try:
                product = Product.objects.get(id=product_id)
                unpaid_orders.append({
                    "product": product,
                    "quantity": details["quantity"],
                    "get_total": float(details["price"]) * details["quantity"], # Ensure float calculation
                })
                total_items += details["quantity"]
                total_amount += float(details["price"]) * details["quantity"]
            except Product.DoesNotExist:
                 pass # Handle missing product
            except (KeyError, ValueError, TypeError):
                 pass # Handle bad cart data

    context = {
        "unpaid_orders": unpaid_orders, # This now contains items from session cart
        "total_items": total_items,
        "total_amount": total_amount,
    }
    return render(request, "store/cart.html", context) # Assuming template path is store/cart.html


def add_to_cart(request):
    if request.method == "POST":
        try:
            # Parse incoming data
            data = json.loads(request.body)
            product_id = str(data.get("product_id"))  # Convert to string for session key consistency
            action = data.get("action")  # Possible values: "add", "remove", "clear_out"

            # Retrieve the cart from the session, or initialize it if it doesn't exist
            cart = request.session.get("cart", {})

            # Handle actions
            if action not in ["add", "remove", "clear_out"]:
                return JsonResponse({"error": "Invalid action"}, status=400)

            # Fetch the product details
            product = get_object_or_404(Product, id=product_id)

            if action == "add":
                # Add product to cart if not already present
                if product_id not in cart:
                    cart[product_id] = {
                        "id": product_id,
                        "name": product.name,
                        "price": float(product.price),
                        "quantity": 0,
                        "image_url": product.imageURL,
                    }
                # Increment the quantity
                cart[product_id]["quantity"] += 1

            elif action == "remove":
                # Decrement the quantity if the product exists in the cart
                if product_id in cart:
                    cart[product_id]["quantity"] -= 1
                    if cart[product_id]["quantity"] <= 0:
                        del cart[product_id]  # Remove the product if quantity is 0

            elif action == "clear_out":
                # Remove the product from the cart entirely
                if product_id in cart:
                    del cart[product_id]

            # Save the updated cart back to the session
            request.session["cart"] = cart
            request.session.modified = True

            # Calculate cart totals
            cart_total = sum(item["price"] * item["quantity"] for item in cart.values())
            cart_items = sum(item["quantity"] for item in cart.values())

            return JsonResponse({
                "success": True,
                "cart": cart,
                "cart_total": cart_total,
                "cart_items": cart_items,
            })

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)
        except Product.DoesNotExist:
             return JsonResponse({"error": "Product not found"}, status=404)
        except Exception as e:
            # Log the error for debugging
            # import logging
            # logger = logging.getLogger(__name__)
            # logger.error(f"Error in add_to_cart: {e}", exc_info=True)
            print(f"Unexpected error in add_to_cart: {e}")
            return JsonResponse({"error": "An unexpected error occurred. Please try again."}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405) # Use 405 for method not allowed

def merge_cart_after_login(request):
    # This function might not be needed if the cart view always reads from session
    # If you intend to merge session cart into DB OrderItems upon login, this is the place
    if not request.user.is_authenticated:
        return

    # Get session cart
    cart = request.session.get("cart", {})
    if not cart: # No session cart to merge
        return

    # Get or create an order for the logged-in user
    tenant = request.tenant
    # Assuming Customer is linked to User and Tenant
    customer, created = Customer.objects.get_or_create(
        user=request.user,
        tenant=tenant,
        defaults={'email': request.user.email, 'name': request.user.get_full_name() or request.user.username} # Add defaults if needed
    )

    order, created = Orders.objects.get_or_create(tenant=tenant, customer=customer, complete=False)

    # Add session cart items to the order
    for product_id, details in cart.items():
        try:
            product = Product.objects.get(id=product_id)
            order_item, created = OrderItem.objects.get_or_create(order=order, product=product)
            # Decide merge strategy: add quantity or replace? Adding seems more logical.
            order_item.quantity += details.get("quantity", 0)
            order_item.save()
        except Product.DoesNotExist:
            continue # Skip if product doesn't exist anymore

    # Clear the session cart after merging
    request.session["cart"] = {}
    request.session.modified = True

def is_valid_email_or_phone(email_or_phone):
    # Validate email
    try:
        validate_email(email_or_phone)
        return "email"
    except ValidationError: # Catch specific validation error
        pass
    # Validate phone number
    try:
        # Add default region if needed, e.g., 'NG' for Nigeria
        phone = parse_phone(email_or_phone, None) # Use None if no default region assumption
        if is_valid_number(phone):
            return "phone"
    except NumberParseException:
        pass
    return None


# Function to check for a shipping address
def shipping_adddressCheck(request):
    email_or_phone = request.session.get("email_or_phone")
    customer = None

    if email_or_phone:
        # Try to find the customer by email or phone for the current tenant
        customer = Customer.objects.filter(
            Q(email=email_or_phone) | Q(phone_number=email_or_phone),
            tenant=request.tenant
        ).first()

    # Return the shipping address or None
    return ShippingAddress.objects.filter(customer=customer).first() if customer else None


# Checkout view
def checkout(request):
    # Check if the shipping address exists for the current session's customer
    address_check = shipping_adddressCheck(request)

    # Retrieve the cart from the session
    cart = request.session.get("cart", {})
    if not cart:
        messages.error(request, "Your cart is empty!")
        return redirect("tenant:cart") # Redirect to cart view

    # Calculate total items and total amount in the cart
    total_items = sum(item.get("quantity", 0) for item in cart.values())
    total_amount = sum(item.get("quantity", 0) * item.get("price", 0.0) for item in cart.values())

    # Initialize variables
    email_or_phone = request.session.get("email_or_phone")
    customer = None
    shipping_address = None

    # Try to fetch customer and address if email_or_phone exists in session
    if email_or_phone:
        customer = Customer.objects.filter(
            Q(email=email_or_phone) | Q(phone_number=email_or_phone),
            tenant=request.tenant
        ).first()
        if customer:
            shipping_address = ShippingAddress.objects.filter(customer=customer).first()

    if request.method == "POST":
        # Use session email_or_phone if available, otherwise get from POST
        email_or_phone_input = request.POST.get("email_or_phone", email_or_phone)

        if not email_or_phone_input:
             messages.error(request, "Please provide your email or phone number.")
             return redirect("tenant:checkout")

        # Validate if the input is an email or phone number
        contact_type = is_valid_email_or_phone(email_or_phone_input)
        if contact_type == "email":
            customer = Customer.objects.filter(email=email_or_phone_input, tenant=request.tenant).first()
        elif contact_type == "phone":
            customer = Customer.objects.filter(phone_number=email_or_phone_input, tenant=request.tenant).first()
        else:
            messages.error(request, "Please enter a valid email or phone number.")
            # Keep existing cart data in context for re-rendering the form
            context = {
                "waiting_list": cart, "total_items": total_items, "total_amount": total_amount,
                "email_or_phone": email_or_phone_input, "Shipping_Address": shipping_address,
                "address_check": address_check, 'page_setup': SetUpPage.objects.filter(tenant=request.tenant).first(),
            }
            return render(request, "tenant/checkout.html", context)


        # Save email_or_phone to the session for reuse
        request.session["email_or_phone"] = email_or_phone_input

        # Check if the customer exists
        if not customer:
            messages.info(request, "No customer found with the provided details. Please sign up or check your details.")
            # Optionally redirect to signup or show signup info
            return redirect("tenant:create_customer") # Or stay on checkout with message

        # Re-check shipping address for the found customer
        shipping_address = ShippingAddress.objects.filter(customer=customer).first()
        if not shipping_address:
             messages.warning(request, "Please add a shipping address.")
             # Redirect to add address page, passing customer info if needed
             return redirect("tenant:add_shipping_address") # Or stay on checkout

        try:
            # Process order creation inside an atomic transaction
            with transaction.atomic():
                # Create the order
                order = Orders.objects.create(
                    tenant=request.tenant, # Use request.tenant directly
                    customer=customer,
                    payment_made=False,
                    complete=False,
                    total_amount = total_amount,
                    Customers_address=shipping_address, # Use the fetched address
                )

                # Add products to the OrderItem table
                for product_id, item in cart.items():
                    product = get_object_or_404(Product, id=product_id)

                    # Validate quantity
                    quantity = item.get("quantity", 0)
                    if not isinstance(quantity, int) or quantity <= 0:
                        # Rollback transaction by raising an error
                        raise ValueError(f"Invalid quantity for product {product.name}.")

                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=quantity,
                    )

                # Clear the cart from the session *after* successful order creation
                request.session["cart"] = {}
                request.session.modified = True

                # Success message
                messages.success(request, "Your order has been placed successfully! Please proceed to payment.")

                # Redirect to payment page
                return redirect("tenant:user_payment", order_id=order.id)

        except ValueError as ve: # Catch specific validation error
             messages.error(request, str(ve))
             # No redirect here, let the page re-render with the error
        except IntegrityError:
            messages.error(request, "An error occurred while processing your order. Please try again.")
            # No redirect here
        except Exception as e:
             # Log the error
             print(f"Checkout Error: {e}")
             messages.error(request, "An unexpected error occurred. Please contact support.")
             # No redirect here

    # For GET requests or failed POST requests, render the checkout page
    page_setup = SetUpPage.objects.filter(tenant=request.tenant).first()
    context = {
        "waiting_list": cart, # Use 'cart' instead of 'waiting_list' for clarity
        "total_items": total_items,
        "total_amount": total_amount,
        "email_or_phone": email_or_phone,
        "Shipping_Address": shipping_address,
        "address_check": address_check, # This might be redundant if shipping_address is fetched
        'page_setup': page_setup,
    }
    return render(request, "tenant/checkout.html", context)

def get_customer(request):
    # This function seems redundant given the logic in checkout and shipping_addressCheck
    # It might be better to consolidate customer fetching logic
    email_or_phone = request.session.get("email_or_phone")
    customer = None
    if email_or_phone:
        customer = Customer.objects.filter(
            Q(email=email_or_phone) | Q(phone_number=email_or_phone),
            tenant=request.tenant
        ).first()
    return customer # Return the customer object or None

def add_shipping_address(request):
    """
    Handles the creation of a new shipping address for the customer identified in the session.
    """
    email_or_phone = request.session.get("email_or_phone")
    customer = None

    # Fetch the customer based on session details and current tenant
    if email_or_phone:
        customer = Customer.objects.filter(
            Q(email=email_or_phone) | Q(phone_number=email_or_phone),
            tenant=request.tenant
        ).first()

    if not customer:
        messages.error(request, "Customer details not found in session. Please provide your details on the checkout page first.")
        return redirect("tenant:checkout")

    if request.method == "POST":
        # Check if an address already exists for this customer
        existing_address = ShippingAddress.objects.filter(customer=customer).first()
        if existing_address:
             # If address exists, use UpdateView logic or redirect to update
             messages.info(request, "You already have a shipping address. You can update it if needed.")
             # Redirect to an update view or handle update here
             return redirect('tenant:update_shipping_address', pk=existing_address.pk) # Assuming UpdateView uses pk

        form = ShippingAddressForm(request.POST)
        if form.is_valid():
            try:
                shipping_address = form.save(commit=False)
                shipping_address.customer = customer
                shipping_address.save()
                messages.success(request, "Shipping address added successfully!")
                return redirect("tenant:checkout")
            except Exception as e:
                 print(f"Error saving shipping address: {e}")
                 messages.error(request, "An error occurred while saving the address.")
        else:
            # Form is invalid, re-render with errors
            messages.error(request, "Please correct the errors below.")
    else:
        # Render an empty form for GET requests
        form = ShippingAddressForm()

    context = {
        "form": form,
        "customer": customer # Pass customer to template if needed
    }
    return render(request, "tenant/shipping_address.html", context)

class UpdateShippingAddress(LoginRequiredMixin, UpdateView): # Consider LoginRequiredMixin if applicable
    model = ShippingAddress
    form_class = ShippingAddressForm
    template_name = 'tenant/shipping_address.html'
    success_url = reverse_lazy('tenant:checkout')

    def get_object(self, queryset=None):
        """Ensure the address belongs to the customer in the session."""
        email_or_phone = self.request.session.get("email_or_phone")
        customer = None
        if email_or_phone:
            customer = Customer.objects.filter(
                Q(email=email_or_phone) | Q(phone_number=email_or_phone),
                tenant=self.request.tenant
            ).first()

        if not customer:
            # Handle case where customer is not found or not in session
            # Maybe raise Http404 or redirect
            raise Http404("Customer not found in session.")

        # Get the address based on PK from URL, ensuring it belongs to the customer
        address = get_object_or_404(ShippingAddress, pk=self.kwargs.get('pk'), customer=customer)
        return address

    def form_valid(self, form):
        messages.success(self.request, "Shipping address updated successfully!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors below.")
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Optionally add the customer to the context if needed in the template
        # context['customer'] = self.get_object().customer
        return context


def order_history(request):
    email_or_phone = request.session.get("email_or_phone")

    if not email_or_phone:
        messages.info(request, "Please provide your email or phone number to view your orders.")
        return redirect("tenant:error")

    # Validate email or phone and fetch customer for the current tenant
    customer = Customer.objects.filter(
        Q(email=email_or_phone) | Q(phone_number=email_or_phone),
        tenant=request.tenant
    ).first()

    if not customer:
        messages.error(request, "No customer found with the provided details for this store.")
        # Clear potentially incorrect session data?
        # if "email_or_phone" in request.session: del request.session["email_or_phone"]
        return redirect("tenant:error")

    # Retrieve all orders for the customer specific to the current tenant
    orders = Orders.objects.filter(customer=customer).select_related('Customers_address').prefetch_related('items__product').order_by("-ordered_date")

    # Get the tenant-specific page setup
    page_setup = SetUpPage.objects.filter(tenant=request.tenant).first()

    context = {
        "orders": orders,
        # "ordered_items" is not needed if using order.items.all in template
        "page_setup": page_setup,
        "customer": customer, # Pass customer for display if needed
    }
    return render(request, "tenant/order_history.html", context)


def reset_session(request):
    # Clear specific session keys related to customer identification
    if "email_or_phone" in request.session:
        del request.session["email_or_phone"]
    # Optionally clear cart as well if desired on reset
    # if "cart" in request.session: del request.session["cart"]
    request.session.modified = True
    messages.info(request, "Session reset. You can now enter different details.")
    return redirect("tenant:checkout") # Or redirect to store front page


def error(request):
    # This view is intended to capture email/phone if missing from session
    if request.method == "POST":
        email_or_phone = request.POST.get("email_or_phone")

        if not email_or_phone:
             messages.error(request, "Please enter your email or phone number.")
             return redirect("tenant:error")

        # Validate email or phone
        contact_type = is_valid_email_or_phone(email_or_phone)
        if not contact_type:
            messages.error(request, "Please enter a valid email or phone number.")
            return redirect("tenant:error")

        # Check if customer exists for the current tenant
        customer = Customer.objects.filter(
            Q(email=email_or_phone) | Q(phone_number=email_or_phone),
            tenant=request.tenant
        ).first()

        if not customer:
            messages.error(request, "No customer found with the provided details for this store.")
            # Optionally redirect to signup
            # return redirect("tenant:create_customer")
            return redirect("tenant:error") # Stay on error page with message

        # Save email_or_phone in the session
        request.session["email_or_phone"] = email_or_phone
        request.session.modified = True

        # Redirect to the orders page
        messages.success(request, f"Welcome back! Viewing orders for {email_or_phone}.")
        return redirect("tenant:order_history")

    # For GET request
    current_tenant = request.tenant
    page_setup = SetUpPage.objects.filter(tenant=current_tenant).first()
    context = {'page_setup': page_setup}
    return render(request, "tenant/error.html", context)

# @login_required # This likely needs customer identification, not user login
def mark_received(request, order_id):
    # Identify customer from session
    email_or_phone = request.session.get("email_or_phone")
    customer = None
    if email_or_phone:
         customer = Customer.objects.filter(
            Q(email=email_or_phone) | Q(phone_number=email_or_phone),
            tenant=request.tenant
        ).first()

    if not customer:
         messages.error(request, "Could not identify customer.")
         return redirect("tenant:order_history") # Or error page

    # Get the order, ensuring it belongs to the identified customer and tenant
    order = get_object_or_404(Orders, id=order_id, customer=customer, tenant=request.tenant)

    if not order.received:
        order.received = True
        # Assuming received_date is auto_now_add or handled by save method
        order.save()
        messages.success(request, f"Order #{order.id} marked as received.")
    else:
        messages.info(request, f"Order #{order.id} was already marked as received.")

    return redirect('tenant:order_history')

def product_detail(request, product_id):
    # Ensure product belongs to the current tenant
    product = get_object_or_404(Product, id=product_id, tenant=request.tenant)
    data = {
        'name': product.name,
        'description': product.description,
        'price': str(product.price), # Keep as string for consistency
        'image': product.image.url if product.image else None # Handle missing image
    }
    return JsonResponse(data)


def get_cart_items_count(request):
    # This function should solely rely on the session cart as DB OrderItems are only created at checkout
    cart = request.session.get('cart', {})
    # Ensure quantity is treated as int, default to 0 if missing or invalid
    return sum(int(item.get('quantity', 0)) for item in cart.values() if isinstance(item, dict))


def cart(request):
    # Retrieve cart from session or initialize it if not present
    cart = request.session.get("cart", {})

    # Initialize total quantities and amounts
    total_quantity = 0
    total_amount = 0.0
    cart_items_details = [] # To hold product objects and quantities

    # Calculate totals and prepare details from the cart
    for item_id, item_data in cart.items():
        try:
            quantity = int(item_data.get("quantity", 0))
            price = float(item_data.get("price", 0.0))
            if quantity > 0:
                product = Product.objects.get(id=item_id, tenant=request.tenant) # Ensure product belongs to tenant
                total_quantity += quantity
                total_amount += quantity * price
                cart_items_details.append({
                    'product': product,
                    'quantity': quantity,
                    'total_price': quantity * price,
                    'image_url': item_data.get('image_url', product.imageURL) # Use cart image URL or fallback
                })
        except (Product.DoesNotExist, ValueError, TypeError, KeyError):
            # Handle errors: product removed, invalid data in session cart
            # Optionally remove invalid item from session cart here
            pass

    current_tenant = request.tenant
    page_setup = SetUpPage.objects.filter(tenant=current_tenant).first()

    context = {
        "cart_items_details": cart_items_details, # Pass detailed items
        "total_quantity": total_quantity,
        "total_amount": total_amount,
        "page_setup": page_setup,
        "cart": cart, # Pass raw cart if needed by JS, though details are better
    }
    return render(request, "tenant/cart.html", context)


# @login_required # Dashboard access might depend on tenant user, not public user
def dashboard(request):
    # Ensure user is authenticated and potentially staff/admin for dashboard access
    # Add appropriate permission checks if needed

    current_tenant = request.tenant
    thirty_days_ago = timezone.now() - timedelta(days=30)

    # --- Metrics ---
    products_qs = Product.objects.filter(tenant=current_tenant)
    orders_qs = Orders.objects.filter(tenant=current_tenant)
    customers_qs = Customer.objects.filter(tenant=current_tenant)
    user_events_qs = UserEvent.objects.filter(tenant=current_tenant, click_time__gte=thirty_days_ago)

    orders_count = orders_qs.count()
    products_count = products_qs.count()
    customers_count = customers_qs.count()

    total_revenue = Invoice.objects.filter(
        order__tenant=current_tenant,
        is_paid=True,
        # Optionally filter by date range
        # created_at__gte=thirty_days_ago
    ).aggregate(total=Sum('total_amount'))['total'] or 0

    recent_orders = orders_qs.select_related('customer').order_by('-ordered_date')[:5]

    low_stock_alerts = products_qs.filter(stock__lt=10).values('name', 'stock') # Use values for efficiency

    # --- Event Tracking Metrics ---
    total_product_views = user_events_qs.filter(event_type='click').count()

    most_viewed_products_full = user_events_qs.filter(
        event_type='click',
        product_id__isnull=False,
    ).values(
        'product_id', 'product_name' # Group by product
    ).annotate(
        view_count=Count('id') # Count events for each product
    ).order_by('-view_count')[:15] # Get top 15

    # --- Top Locations (Cities) ---
    top_cities = user_events_qs.filter(
        event_type='click', # Or filter by other relevant events
        city__isnull=False, # Exclude events with no city data
        city__gt='' # Exclude empty city strings
    ).values(
        'city', 'region_name', 'country' # Group by city, region, country
    ).annotate(
        event_count=Count('id') # Count events per location
    ).order_by('-event_count')[:7] # Get top 7 locations

    context = {
        'orders_count': orders_count,
        'products_count': products_count,
        'customers_count': customers_count,
        'total_revenue': total_revenue,
        'recent_orders': recent_orders,
        'current_tenant': current_tenant,
        'low_stock_alerts': low_stock_alerts,
        'total_product_views': total_product_views,
        'most_viewed_products_full': most_viewed_products_full,
        'most_viewed_products_card': most_viewed_products_full[:5],
        'top_cities': top_cities,
    }
    return render(request, 'tenant/dashboard/dashboard.html', context)



# @login_required # Needs appropriate permissions
def orders_chart_data(request):
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    # Default to last 30 days if no dates provided
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)

    # Override with provided dates if valid
    try:
        if start_date_str:
            start_date = timezone.make_aware(datetime.strptime(start_date_str, '%Y-%m-%d'))
        if end_date_str:
            # Add one day to end_date to include the whole day
            end_date = timezone.make_aware(datetime.strptime(end_date_str, '%Y-%m-%d')) + timedelta(days=1)
    except ValueError:
        # Handle invalid date format, maybe return error or use defaults
        pass # Stick to defaults for now

    # Filter orders by tenant and date range
    orders = Orders.objects.filter(
        tenant=request.tenant,
        ordered_date__range=[start_date, end_date]
    )

    # Group by day and count
    orders_by_date = orders.annotate(
        date=TruncDay('ordered_date')
    ).values('date').annotate(
        total=Count('id')
    ).order_by('date')

    # Prepare data for Chart.js
    # Create a dictionary with all dates in the range initialized to 0
    date_range = pd.date_range(start_date.date(), end_date.date() - timedelta(days=1)) # pandas for easy date range
    orders_dict = {d.strftime('%Y-%m-%d'): 0 for d in date_range}

    # Populate the dictionary with actual counts
    for order_data in orders_by_date:
        date_str = order_data['date'].strftime('%Y-%m-%d')
        if date_str in orders_dict:
            orders_dict[date_str] = order_data['total']

    # Extract sorted dates and counts
    dates = sorted(orders_dict.keys())
    order_counts = [orders_dict[d] for d in dates]


    data = {
        'dates': dates,
        'orders': order_counts,
    }
    return JsonResponse(data)

# ********************Dashboard CRUD**********************
def admin_required(view_func):
    # Simple check if user is staff - adjust if you have more complex roles
    def _wrapped_view_func(request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, "You are not authorized to access this page.")
            return redirect('tenant:dashboard') # Redirect non-staff users
        return view_func(request, *args, **kwargs)
    return _wrapped_view_func

# @login_required 
# @admin_required
def product_list(request):
    current_tenant = request.tenant
    # Add filtering/searching if needed
    search_query = request.GET.get('search', '')
    products_qs = Product.objects.filter(tenant=current_tenant).order_by('name')

    if search_query:
        products_qs = products_qs.filter(name__icontains=search_query)

    # Add pagination
    paginator = Paginator(products_qs, 10) # Show 10 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
    }
    return render(request, 'tenant/dashboard/product_list.html', context)

# @login_required
# @admin_required
def product_create(request):
    current_tenant = request.tenant

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                product = form.save(commit=False)
                product.tenant = current_tenant
                product.save()
                messages.success(request, f"Product '{product.name}' created successfully.")
                return redirect('tenant:admin_product_list')
            except Exception as e:
                 messages.error(request, f"Error creating product: {e}")
        else:
             messages.error(request, "Please correct the errors below.")
    else:
        form = ProductForm()

    context = {
        'form': form,
        'form_title': 'Create New Product', # Add title for clarity
    }
    return render(request, 'tenant/dashboard/product_form.html', context)

# @login_required
# @admin_required
def product_update(request, product_id):
    # Ensure product belongs to the current tenant
    product = get_object_or_404(Product, id=product_id, tenant=request.tenant)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, f"Product '{product.name}' updated successfully.")
                return redirect('tenant:admin_product_list')
            except Exception as e:
                 messages.error(request, f"Error updating product: {e}")
        else:
             messages.error(request, "Please correct the errors below.")
    else:
        form = ProductForm(instance=product)

    context = {
        'form': form,
        'product': product, # Pass product for context
        'form_title': f'Update Product: {product.name}', # Add title
    }
    return render(request, 'tenant/dashboard/product_form.html', context)

# @login_required
# @admin_required
def product_delete(request, product_id):
    # Ensure product belongs to the current tenant
    product = get_object_or_404(Product, id=product_id, tenant=request.tenant)
    if request.method == 'POST':
        try:
            product_name = product.name # Get name before deleting
            product.delete()
            messages.success(request, f"Product '{product_name}' deleted successfully.")
            return redirect('tenant:admin_product_list')
        except Exception as e:
             messages.error(request, f"Error deleting product: {e}")
             # Redirect back to list or confirmation page
             return redirect('tenant:admin_product_list')

    # For GET request, show confirmation page
    return render(request, 'tenant/dashboard/product_confirm_delete.html', {'product': product})

# @login_required
# @admin_required
def customer_list_view(request):
    search_query = request.GET.get("search", "")
    sort_by = request.GET.get("sort_by", "name") # Default sort
    order = request.GET.get("order", "asc")
    page_number = request.GET.get("page", 1)
    customers_per_page = 10

    # Base query filtered by tenant
    customers = Customer.objects.filter(tenant=request.tenant)

    # Apply search filter
    if search_query:
        customers = customers.filter(
            Q(name__icontains=search_query) |
            Q(phone_number__icontains=search_query) |
            Q(email__icontains=search_query)
        )

    # Sorting logic
    valid_sort_fields = {"name": "name", "date": "date_joined", "email": "email"} # Map URL param to model field
    sort_field = valid_sort_fields.get(sort_by, "name") # Default to name if invalid sort_by
    order_prefix = "-" if order == "desc" else ""
    customers = customers.order_by(f"{order_prefix}{sort_field}")

    # Paginate results
    paginator = Paginator(customers, customers_per_page)
    customers_page = paginator.get_page(page_number)

    # Preserve filter/sort parameters in pagination links
    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']
    pagination_query_string = query_params.urlencode()

    context = {
        "customers_page": customers_page, # Pass page object
        "search_query": search_query,
        "sort_by": sort_by,
        "order": order,
        "pagination_query_string": pagination_query_string,
    }
    return render(request, "tenant/dashboard/customers_list.html", context)

# @login_required
# @admin_required
def export_users_csv(request):
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="tenant_{request.tenant.schema_name}_customers.csv"'

    writer = csv.writer(response)
    # Define headers based on Customer model fields
    writer.writerow(['Name', 'Email', 'Phone Number', 'Date Joined']) # Adjust headers as needed

    # Fetch customers for the current tenant only
    customers = Customer.objects.filter(tenant=request.tenant).values_list(
        'name', 'email', 'phone_number', 'date_joined' # Adjust fields as needed
    )
    for customer_data in customers:
        # Format date if needed
        row = list(customer_data)
        if isinstance(row[3], datetime): # Check if the date field is datetime
            row[3] = row[3].strftime('%Y-%m-%d %H:%M:%S') # Format date
        writer.writerow(row)

    return response

# PDF export might be complex, consider if truly needed or use a library like WeasyPrint
# def export_users_pdf(request): ...

# @user_passes_test(lambda u: u.is_superuser) # Superuser check might be too restrictive for tenant admin
# @login_required
# @admin_required
def infograph(request):
    # This view seems more suited for cross-tenant analytics (superuser)
    # If intended for tenant admin, queries need to be filtered by request.tenant
    tenant = request.tenant # Filter by current tenant

    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    number_of_results = int(request.GET.get('number_of_results', 5)) # Default to 5

    # Default date range
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)

    try:
        if start_date_str:
            start_date = timezone.make_aware(datetime.strptime(start_date_str, '%Y-%m-%d'))
        if end_date_str:
            end_date = timezone.make_aware(datetime.strptime(end_date_str, '%Y-%m-%d')) + timedelta(days=1)
    except ValueError:
        pass # Use defaults

    date_filter = {'ordered_date__range': [start_date, end_date]}
    order_items_qs = OrderItem.objects.filter(order__tenant=tenant, **date_filter)

    # Top Customers (based on OrderItem value)
    top_customers_data = order_items_qs.values(
        'order__customer__name', 'order__customer__email' # Group by customer
    ).annotate(
        total_amount=Sum(F('quantity') * F('product__price'), output_field=DecimalField())
    ).order_by('-total_amount')[:number_of_results]

    # Most Selling Products (based on OrderItem quantity)
    most_selling_products_data = order_items_qs.values(
        'product__name' # Group by product name
    ).annotate(
        total_sold=Sum('quantity')
    ).order_by('-total_sold')[:number_of_results]

    # Worst Selling Products (based on OrderItem quantity)
    worst_selling_products_data = order_items_qs.values(
        'product__name'
    ).annotate(
        total_sold=Sum('quantity')
    ).order_by('total_sold')[:number_of_results]

    # Prepare data for charts
    top_users = {
        'labels': [f"{c['order__customer__name']} ({c['order__customer__email']})" for c in top_customers_data],
        'total_amounts': [float(c['total_amount'] or 0) for c in top_customers_data] # Ensure float for JSON
    }
    most_selling_products = {
        'labels': [p['product__name'] for p in most_selling_products_data],
        'total_sold': [p['total_sold'] for p in most_selling_products_data]
    }
    worst_selling_products = {
        'labels': [p['product__name'] for p in worst_selling_products_data],
        'total_sold': [p['total_sold'] for p in worst_selling_products_data]
    }

    context = {
        'top_users_json': json.dumps(top_users, cls=DjangoJSONEncoder),
        'most_selling_products_json': json.dumps(most_selling_products, cls=DjangoJSONEncoder),
        'worst_selling_products_json': json.dumps(worst_selling_products, cls=DjangoJSONEncoder),
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': (end_date - timedelta(days=1)).strftime('%Y-%m-%d'), # Adjust back for display
        'number_of_results': number_of_results,
    }

    return render(request, 'tenant/dashboard/infograph.html', context)

def login_view(request):
    # This seems like a generic login view, potentially conflicting with user_login
    # Consider removing or clarifying its purpose (e.g., admin login?)
    if request.method == 'POST':
        # Use Django's authentication form for better validation
        from django.contrib.auth.forms import AuthenticationForm
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            # Redirect to `next` if available, else default (e.g., dashboard)
            next_url = request.GET.get('next', reverse('tenant:dashboard')) # Use reverse for safety
            messages.success(request, "Login successful.")
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, 'tenant/login.html', {'form': form}) # Assuming template path


@receiver(user_logged_in)
def migrate_cart_to_user(sender, request, user, **kwargs):
    # This signal receiver calls merge_cart_after_login
    merge_cart_after_login(request)


def create_customer(request):
    # This view creates both a public User and a tenant Customer
    # Ensure this aligns with your user model strategy (public vs. tenant-specific users)
    tenant = request.tenant # Current tenant

    if request.method == "POST":
        form = CustomerForm(request.POST) # Assuming CustomerForm handles necessary fields
        if form.is_valid():
            email = form.cleaned_data.get("email").lower()
            password = form.cleaned_data.get("password") # Ensure form includes password
            name = form.cleaned_data.get("name")
            phone_number = form.cleaned_data.get("phone_number") # Assuming form has phone

            # Check if user or customer already exists
            with schema_context("public"):
                if User.objects.filter(username=email).exists():
                    messages.error(request, "An account with this email already exists.")
                    return render(request, "tenant/create_customer.html", {"form": form})

            if Customer.objects.filter(Q(email=email) | Q(phone_number=phone_number), tenant=tenant).exists():
                 messages.error(request, "A customer with this email or phone already exists for this store.")
                 return render(request, "tenant/create_customer.html", {"form": form})

            try:
                with transaction.atomic():
                    # Create User in public schema
                    user = User.objects.create_user(username=email, email=email, password=password)

                    # Create Customer in tenant schema
                    customer = form.save(commit=False)
                    customer.user = user # Link the User object (if Customer model has a user FK)
                    customer.tenant = tenant
                    # Ensure all required Customer fields are set (name, email, phone_number might be set by form)
                    customer.save()

                messages.success(request, "Account created successfully. You can now use your details at checkout.")
                # Redirect to store or checkout, maybe pre-fill email/phone in session?
                request.session["email_or_phone"] = email # Pre-fill session
                return redirect("tenant:store")

            except IntegrityError as e:
                 messages.error(request, f"Database error: Could not create account. {e}")
            except Exception as e:
                print(f"Error creating customer: {e}")
                messages.error(request, "An unexpected error occurred. Please try again.")
                # Optionally add form error: form.add_error(None, "Server error.")
        else:
             messages.error(request, "Please correct the errors below.")
    else:
        form = CustomerForm()

    return render(request, "tenant/create_customer.html", {"form": form})

def user_login(request):
    # This view seems specific to logging in a *Customer* via email/password
    # It doesn't use Django's standard auth system directly but checks password manually
    # Consider using Django's auth system (authenticate/login) for consistency if Customer is linked to User
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        if not email or not password:
            messages.error(request, "Email and password are required.")
            return render(request, "tenant/login.html")

        tenant = request.tenant
        try:
            # Find the customer within the current tenant
            customer = Customer.objects.get(email=email, tenant=tenant)

            # Check if the customer is linked to a User object (assuming Customer has a ForeignKey to User)
            if hasattr(customer, 'user') and customer.user:
                user = customer.user
                # Use Django's check_password
                if user.check_password(password):
                    # Log in the actual User associated with the Customer
                    # Need to ensure the user object has the correct backend attribute
                    # This might require fetching the user from public schema if that's where users live
                    with schema_context('public'):
                         user_public = User.objects.get(id=user.id) # Fetch from public if needed
                    user_public.backend = 'django.contrib.auth.backends.ModelBackend' # Set backend
                    login(request, user_public)

                    # Merge cart after successful login
                    merge_cart_after_login(request)

                    messages.success(request, "You have successfully logged in.")
                    # Redirect based on 'next' parameter or default to store
                    next_url = request.GET.get('next', reverse('tenant:store'))
                    return redirect(next_url)
                else:
                    messages.error(request, "Invalid email or password.")
            else:
                # Handle case where Customer exists but isn't linked to a User or password check is different
                messages.error(request, "Account configuration issue. Cannot log in.")

        except Customer.DoesNotExist:
            messages.error(request, "No account found with this email for this store.")
        except Exception as e:
            messages.error(request, f"An unexpected error occurred: {e}")
            print(f"Login Exception: {e}")

    # For GET request or failed POST
    return render(request, "tenant/login.html")


def list_customers(request):
    # Simple JSON endpoint, likely for internal use or AJAX
    tenant = request.tenant
    customers = Customer.objects.filter(tenant=tenant)
    # Select specific fields to return
    customer_data = [{"id": c.id, "name": c.name, "email": c.email, "phone": c.phone_number} for c in customers]
    return JsonResponse({"customers": customer_data})

# @login_required # Needs appropriate permissions
# @admin_required
def analytics(request):
    tenant = request.tenant  # Get the active tenant

    # Get date filters from query parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Parse dates only if provided
    date_filter = {}
    if start_date and end_date:
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
            date_filter['date_added__range'] = (start_date, end_date)
        except ValueError:
            return JsonResponse({'error': 'Invalid date format'}, status=400)

    # Calculate Total Revenue
    total_revenue = OrderItem.objects.filter(order__tenant=tenant, **date_filter).aggregate(
        revenue=Sum('product__price')
    )['revenue'] or 0

    # Get Best Selling Products
    best_selling_products = list(
        OrderItem.objects.filter(order__tenant=tenant, **date_filter)
        .values('product__name')
        .annotate(total_sold=Sum('quantity'))
        .order_by('-total_sold')[:5]
    )

    # Get Monthly Revenue
    monthly_revenue = list(
        OrderItem.objects.filter(order__tenant=tenant, **date_filter)
        .annotate(month=TruncMonth('date_added'))
        .values('month')
        .annotate(revenue=Sum('product__price'))
        .order_by('month')
    )

    # Get Customer Heatmap Data
    heatmap_data = list(
        OrderItem.objects.filter(order__tenant=tenant, **date_filter)
        .values('product__name')
        .annotate(clicks=Sum('quantity'))
        .order_by('-clicks')
    )

    # Low Stock Alerts
    low_stock_alerts = list(
        Product.objects.filter(tenant=tenant, stock__lt=10).values('name', 'stock')
    )
    
    # Get Top Performing Products
    top_performing_products = list(
        OrderItem.objects.filter(order__tenant=tenant, **date_filter)
        .values('product__name')
        .annotate(
            total_sold=Sum('quantity'),
            total_revenue=Sum(F('product__price') * F('quantity'), output_field=DecimalField())
        )
        .order_by('-total_sold')[:5]
    )

    # Get Top Buying Customers
    top_customers = list(
        OrderItem.objects.filter(order__tenant=tenant, **date_filter)
        .annotate(
            customer_name=Case(
                When(order__customer__name__isnull=False, then=F('order__customer__name')),
                default=F('order__customer__user__username'),
                output_field=models.CharField()
            )
        )
        .values('customer_name')
        .annotate(
            total_spent=Sum(F('product__price') * F('quantity'), output_field=DecimalField()),
            total_items=Sum('quantity')
        )
        .order_by('-total_spent')[:5]
    )
    

    # Check if the request is AJAX for filtering
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'total_revenue': total_revenue,
            'best_selling_products': best_selling_products,
            'monthly_revenue': monthly_revenue,
            'heatmap_data': heatmap_data,
        })
        
    
    # Prepare context for the template (initial load)
    context = {
        'total_revenue': total_revenue,
        'best_selling_products': json.dumps(best_selling_products, cls=DjangoJSONEncoder),
        'monthly_revenue': json.dumps(monthly_revenue, cls=DjangoJSONEncoder),
        'heatmap_data': json.dumps(heatmap_data, cls=DjangoJSONEncoder),
        'top_customers': json.dumps(top_customers, cls=DjangoJSONEncoder),
        'top_performing_products': json.dumps(top_performing_products, cls=DjangoJSONEncoder),
    }

    return render(request, 'tenant/dashboard/infograph.html', context)


def log_inventory_action(product, action, quantity_changed, performed_by, reason=None):
    # Ensure product belongs to the same tenant as performed_by user if applicable
    # Or pass tenant explicitly
    current_stock = product.stock # Get stock *before* potential changes if action implies change
    InventoryAudit.objects.create(
        tenant=product.tenant, # Assuming product has tenant FK
        product=product,
        action=action,
        quantity_changed=quantity_changed,
        current_stock=current_stock, # Log stock level at time of action
        reason=reason,
        performed_by=performed_by, # Should be a User object
    )

def record_daily_snapshot():
    # This should likely be run as a scheduled task (e.g., daily cron job or celery task)
    # Consider filtering by tenant if running per tenant
    tenants = Tenant.objects.all() # Or filter as needed
    for tenant in tenants:
         with schema_context(tenant.schema_name):
            products = Product.objects.all()
            today = date.today()
            for product in products:
                # Calculate sales for the day if needed, or just record stock
                # sales_today = ... calculation ...
                HistoricData.objects.update_or_create(
                    product=product,
                    date=today,
                    tenant=tenant, # Assuming HistoricData has tenant FK
                    defaults={'stock': product.stock} # Update stock for today
                    # defaults={'stock': product.stock, 'sales': sales_today}
                )

def predict_future_demand(product_id, tenant):
    # Filter historic data by product and tenant
    data = HistoricData.objects.filter(
        product_id=product_id,
        tenant=tenant
    ).order_by('date').values("date", "sales") # Assuming 'sales' field exists

    if not data:
        return 0 # No historical data

    df = pd.DataFrame(list(data)) # Convert queryset to list first
    if df.empty or 'sales' not in df.columns:
        return 0

    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)

    # Simple moving average for forecasting (adjust window as needed)
    window_size = 7
    if len(df) < window_size:
        return df['sales'].mean() if not df['sales'].empty else 0 # Use overall mean if not enough data

    df['forecast'] = df['sales'].rolling(window=window_size).mean()

    # Return the last calculated forecast value
    last_forecast = df['forecast'].iloc[-1]
    return last_forecast if pd.notna(last_forecast) else 0


# @login_required
# @admin_required
def inventory_view(request):
    # Get the current tenant
    tenant = request.tenant  # Assuming `request.tenant` provides the current tenant

    # Fetch all products for the tenant
    products = Product.objects.filter(tenant=tenant)

    # Low stock alerts for the tenant
    low_stock_threshold = 5  # Example threshold for low stock
    low_stock_alerts = products.filter(stock__lte=low_stock_threshold)

    # Sort low-stock alerts if necessary
    sort_field = request.GET.get('sort', 'name')  # Default sorting by name
    if sort_field in ['name', 'stock']:
        low_stock_alerts = low_stock_alerts.order_by(sort_field)

    # Handle search query for low-stock alerts
    search_query = request.GET.get('search', '')
    if search_query:
        low_stock_alerts = low_stock_alerts.filter(name__icontains(search_query))

    # Bulk actions for low-stock alerts
    if request.method == "POST" and "bulk_action" in request.POST:
        selected_items = request.POST.getlist("selected_items")
        action_type = request.POST.get("bulk_action")
        if action_type == "restock":
            # Restock selected items
            products.filter(id__in=selected_items).update(stock=F('stock') + 10)
        elif action_type == "remove":
            # Remove selected items
            products.filter(id__in=selected_items).delete()
        return redirect('inventory_view')

    # Audit logs for the tenant
    audit_logs = InventoryAudit.objects.filter(tenant=tenant).order_by('-created_at')[:20]  # Latest 20 logs

    # Forecasting (Example: predict stock needs for next week for the tenant)
    forecast_data = []
    for product in products:
        sales_last_week = HistoricData.objects.filter(
            product=product,
            date__gte=now().date() - timedelta(days=7),
            tenant=tenant
        ).aggregate(total_sales=Sum('sales'))['total_sales'] or 0
        forecast_data.append({
            "product": product,
            "sales_last_week": sales_last_week,
            "forecast_next_week": sales_last_week * 1.1  # Simple multiplier for prediction
        })

    # Context to pass to the frontend
    context = {
        'products': products,
        'low_stock_alerts': low_stock_alerts,
        'audit_logs': audit_logs,
        'forecast_data': forecast_data,
    }

    return render(request, 'tenant/dashboard/inventory_management.html', context)    


def inventory_alerts_view(request):
    # Get low-stock products (e.g., stock < 5)
    low_stock_alerts = Product.objects.filter(stock__lte=5).annotate(
        name=F('name'),
        stock=F('stock')
    )

    # Render data to the template
    return render(request, 'tenant/dashboard/inventory_management.html', {
        'low_stock_alerts': low_stock_alerts
    })

@csrf_exempt
def adjust_stock(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == "POST":
        # Example: get new stock value from form
        new_stock = request.POST.get("new_stock")
        if new_stock is not None:
            try:
                product.stock = int(new_stock)
                product.save()
                messages.success(request, "Stock updated successfully.")
            except ValueError:
                messages.error(request, "Invalid stock value.")
        else:
            messages.error(request, "No stock value provided.")
        return redirect("tenant:inventory")

# Paystack API key (store securely in settings)
PAYSTACK_SECRET_KEY = settings.PAYSTACK_SECRET_KEY


def user_payment(request, order_id):
    """
    Display payment options (Paystack or Bank Transfer) and handle redirection or details display.
    """
    # Ensure order belongs to the current tenant and is not paid
    order = get_object_or_404(Orders, id=order_id, tenant=request.tenant, payment_made=False)

    # Identify the customer associated with the order
    customer = order.customer
    customer_email = customer.email if customer else 'default@example.com' # Fallback email if needed

    if request.method == "POST":
        payment_method = request.POST.get("payment_method")
        if payment_method not in ['paystack', 'bank']:
             messages.error(request, "Invalid payment method selected.")
             return redirect("tenant:user_payment", order_id=order.id)

        order.payment_method = payment_method
        order.save()

        if payment_method == "paystack":
            # Initialize Paystack transaction
            headers = {
                "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
                "Content-Type": "application/json",
            }
            payload = {
                "email": customer_email,
                "amount": int(order.total_amount * 100),  # Amount in kobo
                "order_id": order.id, # Include order_id in metadata
                "metadata": {
                    "order_id": order.id,
                    "customer_id": customer.id if customer else None,
                    "tenant_schema": request.tenant.schema_name,
                },
                "callback_url": request.build_absolute_uri(
                    reverse("tenant:paystack_callback") # Use generic callback URL
                ),
                 # Optionally add reference if you want to generate it beforehand
                 # "reference": f"order_{order.id}_{int(time.time())}"
            }
            try:
                response = requests.post("https://api.paystack.co/transaction/initialize", json=payload, headers=headers)
                response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
                payment_data = response.json()

                if payment_data.get("status"):
                    # Store reference for verification later
                    order.payment_reference = payment_data["data"]["reference"]
                    order.save()
                    # Redirect user to Paystack's payment page
                    return redirect(payment_data["data"]["authorization_url"])
                else:
                    error_msg = payment_data.get("message", "Unknown error from Paystack.")
                    messages.error(request, f"Paystack Error: {error_msg}")

            except requests.exceptions.RequestException as e:
                 messages.error(request, f"Network error connecting to Paystack: {e}")
            except Exception as e:
                 messages.error(request, f"An error occurred during payment initialization: {e}")

            # If Paystack initialization fails, redirect back
            return redirect("tenant:user_payment", order_id=order.id)

        elif payment_method == "bank":
            # Redirect to a page with bank details
            return redirect(reverse("tenant:bank_payment", args=[order.id]))

    # For GET request
    page_setup = SetUpPage.objects.filter(tenant=request.tenant).first()
    context = {
        "order": order,
        'total_amount': order.total_amount,
        'page_setup': page_setup,
    }
    return render(request, "tenant/order_payment.html", context)


def bank_payment(request, order_id):
    """
    Display bank details for payment and allow users to mark payment as completed.
    """
    # Ensure order belongs to tenant, method is bank, and not paid
    order = get_object_or_404(Orders, id=order_id, tenant=request.tenant, payment_method="bank", payment_made=False)

    if request.method == "POST":
        # Here, you might want admin confirmation rather than user marking as paid
        # For now, let's assume user confirms they've paid (sets status to pending admin verification)
        # Add a field to Order model like 'payment_status' (e.g., pending, confirmed, failed)
        # order.payment_status = 'pending_confirmation'
        order.payment_reference = request.POST.get("payment_reference", "N/A") # Store user provided ref if any
        order.save()
        messages.info(request, "Your payment confirmation has been noted. We will verify and update the order status soon.")
        return redirect("tenant:order_confirmation", order_id=order.id)

    # Fetch bank details from settings or a model
    bank_details = {
        "account_name": settings.BANK_ACCOUNT_NAME, # Example from settings
        "account_number": settings.BANK_ACCOUNT_NUMBER,
        "bank_name": settings.BANK_NAME,
    }
    page_setup = SetUpPage.objects.filter(tenant=request.tenant).first()
    context = {
        "order": order,
        "bank_details": bank_details,
        "page_setup": page_setup,
    }
    return render(request, "tenant/bank_payment.html", context)


def order_confirmation(request, order_id):
    # Ensure order belongs to the current tenant
    order = get_object_or_404(Orders, id=order_id, tenant=request.tenant)
    page_setup = SetUpPage.objects.filter(tenant=request.tenant).first()
    context = {
        "order": order,
        'countdown_duration': 45 * 60,  # 45 minutes in seconds (if needed by JS)
        'page_setup': page_setup,
    }
    return render(request, "tenant/order_confirmation.html", context)

# This view seems problematic. Checking payment status usually involves querying the payment gateway (Paystack)
# or checking internal flags set by callbacks/admin actions. Relying on the Payment model directly might be incorrect.
# Let's assume it's meant to check the Order's payment_made status for AJAX polling.
def check_payment_status(request, order_id):
    try:
        # Fetch the order, ensuring it belongs to the tenant
        order = Orders.objects.get(id=order_id, tenant=request.tenant)

        # Return the payment status of the order
        response = {"payment_made": order.payment_made}
        return JsonResponse(response, status=200)

    except Orders.DoesNotExist:
        error_response = {"error": "Order not found"}
        return JsonResponse(error_response, status=404)
    except Exception as e:
         print(f"Error checking payment status: {e}")
         return JsonResponse({"error": "An internal error occurred"}, status=500)


# Use @csrf_exempt ONLY if Paystack webhook cannot send CSRF token, otherwise use standard CSRF protection.
# Paystack callbacks typically use GET requests for redirection, webhooks use POST. This handles the GET redirection.
def paystack_callback(request):
    """
    Handle Paystack payment callback (GET request after user payment) to verify payment.
    This view verifies the transaction using the reference provided by Paystack.
    """
    reference = request.GET.get("reference")
    if not reference:
        messages.error(request, "Payment reference not found in callback.")
        return redirect("tenant:store") # Redirect to a safe page

    headers = { "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}" }
    order = None # Initialize order

    try:
        # Verify the transaction with Paystack
        verify_url = f"https://api.paystack.co/transaction/verify/{reference}"
        response = requests.get(verify_url, headers=headers)
        response.raise_for_status() # Raise HTTPError for bad responses
        payment_data = response.json()

        if payment_data.get("status") and payment_data["data"]["status"] == "success":
            # Payment successful according to Paystack
            paystack_amount = payment_data["data"]["amount"] / 100 # Amount in Naira/base currency
            order_id = payment_data["data"]["metadata"].get("order_id") # Get order_id from metadata

            if not order_id:
                 messages.error(request, "Order ID missing in payment metadata. Please contact support.")
                 # Log this issue: print(f"Missing order_id in metadata for reference {reference}")
                 return redirect("tenant:store")

            # Fetch the corresponding order, ensuring it belongs to the tenant and is not already paid
            order = get_object_or_404(Orders, id=order_id, tenant=request.tenant)

            if order.payment_made:
                 messages.info(request, f"Payment for order #{order.id} has already been confirmed.")
                 return redirect("tenant:order_confirmation", order_id=order.id)

            # Verify amount (optional but recommended)
            if abs(float(order.total_amount) - float(paystack_amount)) > 0.01: # Allow small tolerance
                 messages.error(request, "Payment amount mismatch. Please contact support.")
                 # Log this issue: print(f"Amount mismatch for order {order.id}. Expected {order.total_amount}, got {paystack_amount}")
                 # Potentially flag the order for review
                 return redirect("tenant:user_payment", order_id=order.id)

            # Mark order as paid
            order.payment_made = True
            order.payment_reference = reference # Store the successful reference
            order.payment_method = 'paystack' # Ensure method is set
            order.save()

            # Optionally create an Invoice record here
            Invoice.objects.get_or_create(
                 order=order,
                 defaults={
                     'total_amount': order.total_amount,
                     'is_paid': True,
                     # Add other invoice fields like invoice_number, due_date if applicable
                 }
            )


            messages.success(request, "Payment successful!")
            return redirect("tenant:order_confirmation", order_id=order.id)
        else:
            # Payment failed or status unknown according to Paystack
            error_msg = payment_data.get("message", "Payment verification returned unsuccessful status.")
            messages.error(request, f"Payment Failed: {error_msg}")
            # Find order via reference if possible to redirect user
            order = Orders.objects.filter(payment_reference=reference, tenant=request.tenant).first()
            if order:
                 return redirect("tenant:user_payment", order_id=order.id)
            else:
                 return redirect("tenant:store") # Fallback redirect

    except requests.exceptions.RequestException as e:
        messages.error(request, f"Network error verifying payment: {e}")
    except Http404:
         messages.error(request, "Order associated with this payment not found.")
    except Exception as e:
        messages.error(request, f"An unexpected error occurred during payment verification: {e}")
        print(f"Paystack Callback Error: {e}") # Log the error

    # Fallback redirect in case of errors before finding order
    if order:
        return redirect("tenant:user_payment", order_id=order.id)
    else:
        return redirect("tenant:store")


# --- Event Tracking with Geolocation ---

# Function to get client IP (Corrected)
def get_client_ip(request):
    """ Extract the real IP address of a visitor """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # Take the first IP, ensuring it's a valid IP format
        ip = x_forwarded_for.split(',')[0].strip()
        try:
            validate_ipv46_address(ip)
        except ValidationError:
            ip = request.META.get('REMOTE_ADDR') # Fallback if forwarded IP is invalid
    else:
        ip = request.META.get('REMOTE_ADDR')
    # Handle None case for REMOTE_ADDR (though unlikely)
    return ip if ip else '0.0.0.0' # Return a placeholder if IP is None

# Function to get geolocation from IP (Corrected)
def get_ip_location(ip_address):
    """ Get location data (city, country, latitude, longitude) from IP """
    if not ip_address or ip_address == '127.0.0.1' or ip_address == '0.0.0.0': # Skip local/placeholder IPs
        return {}
    try:
        # Use the actual ip_address variable
        response = requests.get(f"http://ip-api.com/json/{ip_address}", timeout=5) # Add timeout
        response.raise_for_status() # Raise HTTPError for bad responses
        data = response.json()

        if data.get("status") == "fail":
            print(f"IP API failed for {ip_address}: {data.get('message')}")
            return {}

        # Extract relevant fields safely
        return {
            "country": data.get("country"),
            "country_code": data.get("countryCode"),
            "region": data.get("region"),
            "region_name": data.get("regionName"),
            "city": data.get("city"),
            "zip_code": data.get("zip"),
            "latitude": data.get("lat"),
            "longitude": data.get("lon"),
            "timezone": data.get("timezone"),
            "isp": data.get("isp"),
            "org": data.get("org"),
            "asn": data.get("as"),
        }
    except requests.exceptions.Timeout:
        print(f"Timeout fetching IP location for {ip_address}")
        return {}
    except requests.exceptions.RequestException as e:
        print(f"Error fetching IP location for {ip_address}: {e}")
        return {}
    except Exception as e: # Catch broader exceptions during processing
        print(f"Generic error in get_ip_location for {ip_address}: {e}")
        return {}


@csrf_exempt # Keep CSRF exempt for simple JS fetch calls, but consider security implications
@require_POST # Ensure only POST requests
def track_event(request):
    """Track product click events with location data."""
    try:
        data = json.loads(request.body)
        event_type = data.get("event")
        product_id = data.get("product_id") # Can be None if not product-specific event
        click_time = now() # Use server time
        user_agent = request.headers.get("User-Agent", "Unknown")

        if not event_type:
             return JsonResponse({"status": "error", "message": "Event type is required."}, status=400)

        # Fetch product details only if product_id is provided
        product_name = None
        product_price = None # Use None instead of 0.00 for clarity
        if product_id:
            # Ensure product belongs to the current tenant
            product = Product.objects.filter(id=product_id, tenant=request.tenant).first()
            if product:
                product_name = product.name
                product_price = product.price
            # else: product not found or doesn't belong to tenant, proceed without details

        # Get REAL IP and location data
        ip_address = get_client_ip(request)
        location_data = get_ip_location(ip_address)

        # Handle lat/lon values safely
        latitude = location_data.get("latitude")
        longitude = location_data.get("longitude")
        try:
            latitude = float(latitude) if latitude is not None else None
            longitude = float(longitude) if longitude is not None else None
        except (ValueError, TypeError):
            latitude, longitude = None, None # Set to None if conversion fails

        # Save event in DB
        UserEvent.objects.create(
            tenant = request.tenant,
            session_id=request.session.session_key, # Can be None for new sessions
            event_type=event_type,
            product_id=product_id,
            product_name=product_name,
            product_price=product_price,
            click_time=click_time,
            user_agent=user_agent,
            ip_address=ip_address,
            city=location_data.get("city"), # Use get with default None implicitly
            region=location_data.get("region"),
            country=location_data.get("country"),
            country_code=location_data.get("country_code"),
            region_name=location_data.get("region_name"),
            timezone=location_data.get("timezone"),
            isp=location_data.get("isp"),
            org=location_data.get("org"),
            asn=location_data.get("asn"),
            zip_code=location_data.get("zip_code"),
            latitude=latitude,
            longitude=longitude,
        )

        # Return minimal success response
        return JsonResponse({"status": "success"})

    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON data"}, status=400)
    except Exception as e:
        # Log the error properly in production
        # import logging
        # logger = logging.getLogger(__name__)
        # logger.error(f"Error in track_event: {e}", exc_info=True)
        print(f"Error in track_event: {e}") # Basic logging for development
        return JsonResponse({"status": "error", "message": "An internal error occurred."}, status=500)


# --- Invoice Views ---

# @login_required
# @admin_required
def invoice_list(request):
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')

    # Base queryset for the current tenant
    invoices_qs = Invoice.objects.filter(order__tenant=request.tenant).select_related('order', 'order__customer').order_by('-created_at')

    # Apply search filter
    if search_query:
        invoices_qs = invoices_qs.filter(
            Q(invoice_number__icontains=search_query) |
            Q(order__id__icontains=search_query) |
            Q(order__customer__name__icontains=search_query) |
            Q(order__customer__email__icontains=search_query)
        )

    # Apply status filter
    if status_filter == 'paid':
        invoices_qs = invoices_qs.filter(is_paid=True)
    elif status_filter == 'unpaid':
        invoices_qs = invoices_qs.filter(is_paid=False)

    # Apply pagination
    paginator = Paginator(invoices_qs, 10)
    page_number = request.GET.get('page')
    invoices_page = paginator.get_page(page_number)

    # Preserve filter parameters in pagination links
    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']
    pagination_query_string = query_params.urlencode()

    context = {
        'invoices': invoices_page,
        'search_query': search_query,
        'status_filter': status_filter,
        'pagination_query_string': pagination_query_string,
    }
    return render(request, 'tenant/dashboard/invoice_list.html', context)

# @login_required
# @admin_required
def invoice_detail(request, invoice_id):
    # Ensure invoice belongs to the current tenant
    invoice = get_object_or_404(Invoice.objects.select_related('order__customer', 'order__tenant'),
                                id=invoice_id, order__tenant=request.tenant)
    return render(request, 'tenant/dashboard/invoice_detail.html', {'invoice': invoice})

# @login_required
# @admin_required
def create_manual_invoice(request):
    # This needs more logic: associate with an Order, calculate total, etc.
    # Form needs to allow selecting/creating Order, Customer, Items.
    if request.method == 'POST':
        # Form processing needs to handle order/item creation and linking
        form = ManualInvoiceForm(request.POST) # Assuming this form exists and is complex
        if form.is_valid():
            # Logic to create Order, OrderItems based on form data
            # Then create Invoice linked to the Order
            # form.save() # Simple save likely won't work
            messages.success(request, "Manual invoice created (logic pending).")
            return redirect('tenant:invoice_list')
        else:
             messages.error(request, "Please correct the form errors.")
    else:
        form = ManualInvoiceForm() # Initialize form

    context = {
        'form': form,
        'form_title': 'Create Manual Invoice'
    }
    return render(request, 'tenant/dashboard/create_invoice.html', context)


# Original simple PDF export (might be useful as fallback)
def export_invoice_pdf_simple(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id, order__tenant=request.tenant)
    pdf_file = BytesIO()
    p = canvas.Canvas(pdf_file, pagesize=letter)
    p.drawString(100, 750, f"Invoice ID: {invoice.id}")
    # ... (add more details simply) ...
    p.showPage()
    p.save()
    pdf_file.seek(0)
    return FileResponse(pdf_file, content_type='application/pdf', filename=f'invoice_simple_{invoice_id}.pdf')


# Refactored download_invoice using ReportLab
# @login_required
# @admin_required # Or allow customers to download their own invoices? Needs logic change.
def download_invoice(request, invoice_id):
    """
    Generates and downloads a PDF invoice using ReportLab.
    """
    # Fetch the invoice ensuring it belongs to the current tenant
    # Add customer check if non-admins can download:
    # Q(order__customer=request.user.customer_profile) | Q(request.user.is_staff)
    invoice = get_object_or_404(Invoice.objects.select_related(
        'order__tenant', 'order__customer'
    ).prefetch_related('order__items__product'), # Prefetch items and products
                                id=invoice_id, order__tenant=request.tenant)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            leftMargin=0.75*inch, rightMargin=0.75*inch,
                            topMargin=0.75*inch, bottomMargin=0.75*inch)
    styles = getSampleStyleSheet()
    story = []

    # --- Header ---
    story.append(Paragraph(f"Invoice #{invoice.invoice_number}", styles['h1']))
    story.append(Spacer(1, 0.2*inch))

    # --- Tenant/Company Info (Example) ---
    # You might fetch this from tenant model or settings
    company_info_data = [
        [Paragraph(f"<b>{request.tenant.name}</b>", styles['Normal'])],
        # [Paragraph("123 Business Rd.", styles['Normal'])],
        # [Paragraph("City, State, Zip", styles['Normal'])],
        # [Paragraph(f"Contact: {request.tenant.contact_email}", styles['Normal'])],
    ]
    company_table = Table(company_info_data, colWidths=[6*inch])
    company_table.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'LEFT')]))
    # story.append(company_table)
    # story.append(Spacer(1, 0.1*inch))


    # --- Invoice & Order Details ---
    details_data = [
        [Paragraph("<b>Invoice Details</b>", styles['h3']), Paragraph("<b>Order Details</b>", styles['h3'])],
        [
            f"Invoice Number: {invoice.invoice_number}",
            f"Order ID: {invoice.order.id}"
        ],
        [
            f"Created At: {date_format(invoice.created_at, 'F j, Y, P')}",
            f"Ordered Date: {date_format(invoice.order.ordered_date, 'F j, Y, P')}"
        ],
        [
            f"Due Date: {date_format(invoice.due_date, 'F j, Y') if invoice.due_date else 'N/A'}",
            f"Customer: {invoice.order.customer.name if invoice.order.customer else 'N/A'}"
        ],
        [
            f"Status: {'Paid' if invoice.is_paid else 'Unpaid'}",
            f"Payment Method: {invoice.order.payment_method or 'N/A'}"
        ],
         [
            "", # Empty cell for alignment
            f"Payment Ref: {invoice.order.payment_reference or 'N/A'}"
        ],
    ]
    details_table = Table(details_data, colWidths=[3*inch, 3*inch])
    details_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4), # Padding for data rows
        ('TOPPADDING', (0, 1), (-1, -1), 0),
        ('SPAN', (0, 0), (0, 0)), # Span header cell
        ('SPAN', (1, 0), (1, 0)), # Span header cell
        # ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey), # Optional grid
    ]))
    story.append(details_table)
    story.append(Spacer(1, 0.3*inch))


    # --- Items Table ---
    story.append(Paragraph("Products", styles['h2']))
    story.append(Spacer(1, 0.1*inch))

    items_data = [[
        Paragraph('<b>Product</b>', styles['Normal']),
        Paragraph('<b>Quantity</b>', styles['Normal']),
        Paragraph('<b>Unit Price</b>', styles['Normal']),
        Paragraph('<b>Line Total</b>', styles['Normal'])
    ]] # Header row

    order_items = invoice.order.items.all() # Use prefetched items

    if not order_items:
         items_data.append([Paragraph('No items found for this order.', styles['Normal']), '', '', ''])
    else:
        for item in order_items:
            unit_price_str = f"₦{item.product.price:,.2f}"
            try:
                # Use item.get_total if it exists and returns a Decimal/float
                line_total_val = item.get_total()
            except AttributeError:
                line_total_val = item.quantity * item.product.price
            line_total_str = f"₦{line_total_val:,.2f}"

            items_data.append([
                Paragraph(item.product.name, styles['Normal']),
                Paragraph(str(item.quantity), styles['Normal']), # Ensure quantity is string
                Paragraph(unit_price_str, styles['Normal']),
                Paragraph(line_total_str, styles['Normal'])
            ])

    items_table = Table(items_data, colWidths=[3*inch, 0.8*inch, 1.1*inch, 1.1*inch]) # Adjusted widths slightly
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'), # Center headers
        ('ALIGN', (1, 1), (1, -1), 'CENTER'), # Center quantity
        ('ALIGN', (2, 1), (-1, -1), 'RIGHT'), # Right align prices/totals
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6), # Padding for data rows
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        # ('GRID', (0, 0), (-1, -1), 0.5, colors.grey), # Removed grid
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LINEBELOW', (0,0), (-1,0), 1, colors.black), # Line below header
    ]))
    story.append(items_table)
    story.append(Spacer(1, 0.3*inch))

    # --- Total Amount ---
    total_data = [
        ['', '', Paragraph('<b>Total Amount:</b>', styles['Normal']), Paragraph(f"<b>₦{invoice.total_amount:,.2f}</b>", styles['Normal'])]
    ]
    total_table = Table(total_data, colWidths=[3*inch, 0.8*inch, 1.1*inch, 1.1*inch])
    total_table.setStyle(TableStyle([
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (2, 0), (-1, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('LINEABOVE', (2,0), (-1,0), 1, colors.black), # Line above total
    ]))
    story.append(total_table)
    story.append(Spacer(1, 0.5*inch))

    # --- Footer ---
    story.append(Paragraph("Thank you for your Patronage!", styles['Normal']))

    # --- Build the PDF ---
    try:
        doc.build(story)
    except Exception as e:
         # Log error building PDF
         print(f"Error building PDF for invoice {invoice_id}: {e}")
         # Return an error response or raise
         return HttpResponse("Error generating PDF.", status=500)


    buffer.seek(0)
    response = FileResponse(buffer, as_attachment=True, filename=f"Invoice_{invoice.invoice_number}.pdf")
    response['Content-Type'] = 'application/pdf'

    return response

from django.views.decorators.http import require_GET
@require_GET
def search_products(request):
    query = request.GET.get('q', '').strip()
    products = Product.objects.filter(name__icontains=query) if query else []
    context = {
        'query': query,
        'products': products,
        'found': products.exists(),
    }
    return render(request, 'tenant/search_results.html', context)