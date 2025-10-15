from django.shortcuts import render, redirect, get_object_or_404
from subscription.models import SubscriptionPlan, Subscription, PaymentOption, Payment, generate_reference, SubscriptionHistory
from tenant.models import Tenant
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta

from django.contrib.auth import get_user_model

User = get_user_model()


from django.http import JsonResponse

import requests
from django.conf import settings
from django.shortcuts import render, redirect
from page_settings.models import *
from django.contrib import messages

from django.utils import timezone



def example_view(request):
    messages.success(request, "This is a one-time success message.")
    return redirect('your_view_name')  # Redirect to prevent message on refresh

def initialize_payment(request, subscription_id):
    """
    Handles the payment initialization for a given subscription.
    """
    if request.method == "POST":
        # Debug: Log the subscription ID from the URL
        print(f"Subscription ID from URL: {subscription_id}")

        try:
            # Fetch subscription using the ID from the URL
            subscription = Subscription.objects.get(id=subscription_id, tenant=request.tenant)
        except Subscription.DoesNotExist:
            return render(
                request, 
                "subscription/payment_failed.html", 
                {"message": "Invalid Subscription ID."}
            )

        # Ensure the amount is submitted in the POST data   
        amount = request.POST.get('amount')
        if not amount:
            return render(
                request, 
                "subscription/payment_failed.html", 
                {"message": "Payment amount is missing."}
            )

        try:
            # Convert the amount to kobo (1 Naira = 100 Kobo)
            amount_in_kobo = int(amount) * 100
        except ValueError:
            return render(
                request, 
                "subscription/payment_failed.html", 
                {"message": "Invalid payment amount."}
            )

        # Generate a unique reference for the transaction
        reference = generate_reference()
        
        payment_option_instance = get_object_or_404(PaymentOption, id=2)
        print('payment_option<><>>>>><', payment_option_instance)
        
        print(payment_option_instance)
        
        # Create a new payment record in the database
        payment = Payment.objects.create(
            tenant=request.tenant,  
            payment_option = payment_option_instance,
            subscription=subscription,
            amount=amount,  # Store the amount in Naira
            transaction_reference=reference,
            is_successful=False,  # Set to False until confirmed by webhook
        )
        
        
        # Set up Paystack request headers and payload
        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
        }
        
        tenant_name = request.tenant.name  # Get tenant's name
        print("tenant:", tenant_name)

        tenant_subdomain = request.tenant.domain_url.split(".")[0]
        callback_url = settings.PAYSTACK_CALLBACK_URL.replace("subdomain", tenant_subdomain)


        data = {
            "email": request.tenant.email,  # Use tenant's email for payment
            "amount": amount_in_kobo,
            "reference": reference,
            "callback_url": callback_url,
        }


        # Send the initialize transaction request to Paystack
        response = requests.post(
            "https://api.paystack.co/transaction/initialize", 
            headers=headers, 
            json=data
        )

        if response.status_code == 200:
            # Redirect to the Paystack authorization URL
            response_data = response.json()
            return redirect(response_data['data']['authorization_url'])
        else:
            # Handle failure in initializing the transaction
            return render(
                request, 
                "subscription/payment_failed.html", 
                {"message": response.json().get("message", "Failed to initialize payment.")}
            )

    current_tenant = request.tenant
    page_setup = SetUpPage.objects.filter(tenant=current_tenant).first()  # Get the first setup page for the tenant
    subscription = get_object_or_404(Subscription, id=subscription_id, tenant=request.tenant)
    payment_option = PaymentOption.objects.all()

    # Render the payment form if the request method is not POST
    
    context = {
        "subscription_id": subscription_id,
        'page_setup':page_setup, 
        'subscription':subscription,
        'payment_option':payment_option
    }
    
    return render(request, "subscription/payment_form.html", context)


def check_confirmation(request, subscription_id):
    subscription = get_object_or_404(Subscription, id=subscription_id)
    return JsonResponse({"is_successful": subscription.is_successful})


def verify_payment(request):
    reference = request.GET.get('reference') or request.GET.get('trxref')
    if not reference:
        return render(request, "subscription/payment_failed.html", {"message": "No transaction reference provided."})

    # Fetch the Payment object
    payment = Payment.objects.filter(transaction_reference=reference).first()
    if not payment:
        return render(request, "subscription/payment_failed.html", {"message": "Invalid transaction reference."})

    # Verify the transaction with Paystack
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"
    }
    response = requests.get(f"https://api.paystack.co/transaction/verify/{reference}", headers=headers)

    if response.status_code == 200:
        response_data = response.json()
        if response_data['data']['status'] == 'success':
            # Mark payment as successful
            payment.is_successful = True
            payment.save()

            # Activate subscription
            subscription = payment.subscription
            subscription.is_active = True
            subscription.save()

            # Log the subscription in history
            SubscriptionHistory.objects.create(
                tenant=request.tenant,
                plan=subscription.plan,
                start_date=subscription.start_date,
                end_date=subscription.end_date,
                notes="Payment verified successfully.",
            )

            return render(request, "subscription/payment_success.html", {"payment": payment})
        else:
            # Payment failed
            payment.is_successful = False
            payment.save()
            return render(request, "subscription/payment_failed.html", {"message": "Payment verification failed."})

    # API error
    payment.is_successful = False
    payment.save()
    
    
    return render(request, "subscription/payment_failed.html", {"message": "Payment verification failed!"})

# @login_required
def plan_view(request):
    """
    Displays all available subscription plans to the user.
    """
    plans = SubscriptionPlan.objects.all()  # Fetch all subscription plans
    return render(request, 'subscription/plan_view.html', {'plans': plans})


# @login_required
    # def select_plan(request):
    #     """
    #     Allows the user to select a plan and redirects to the payment options page.
    #     """
    #     plans = SubscriptionPlan.objects.all()  # Fetch all subscription plans

    #     if request.method == 'POST':
    #         plan_id = request.POST.get('plan_id')
    #         plan = get_object_or_404(SubscriptionPlan, id=plan_id)

    #         # Fetch the current tenant associated with the user
    #         tenant = request.tenant  # This is populated by `django-tenants` middleware

    #         # Create or update the subscription
    #         subscription, created = Subscription.objects.update_or_create(
    #             tenant=tenant,
    #             defaults={
    #                 'plan': plan,
    #                 'start_date': datetime.now(),
    #                 'end_date': datetime.now() + timedelta(days=plan.duration),
    #                 'is_active': False,  # Will be activated after successful payment
    #                 'auto_renew': False,
    #             }
    #         )

    #         # Redirect to the payment options page
    #         return redirect('subscription:payment_options', subscription_id=subscription.id)
        
    #     current_tenant = request.tenant
    #     page_setup = SetUpPage.objects.filter(tenant=current_tenant).first()  # Get the first setup page for the tenant
        

    #     return render(request, 'subscription/select_plan.html', {'plans': plans,'page_setup':page_setup})


def select_plan(request):
    """
    Allows the user to select a plan and redirects to the appropriate page based on the selected plan.
    """
    plans = SubscriptionPlan.objects.all()  # Fetch all subscription plans

    if request.method == 'POST':
        plan_id = request.POST.get('plan_id')
        plan = get_object_or_404(SubscriptionPlan, id=plan_id)

        # Fetch the current tenant associated with the user
        tenant = request.tenant  # This is populated by `django-tenants` middleware

        # Check if the tenant has already used the free plan
        if plan.name == SubscriptionPlan.FREE_PLAN:
            free_plan_exists = SubscriptionHistory.objects.filter(
                tenant=tenant,
                plan__name=SubscriptionPlan.FREE_PLAN
            ).exists()

            if free_plan_exists:
                messages.error(request, "You can only use the free plan once.")
                return redirect('subscription:select_plan')

        # Determine subscription duration
        if plan.name == SubscriptionPlan.FREE_PLAN:
            duration = 7  # Free plan duration is 7 days
            is_active = True  # Free plan activates immediately
        else:
            duration = plan.duration
            is_active = False  # Paid plans activate after successful payment

        # Calculate end date
        start_date = datetime.now()
        end_date = start_date + timedelta(days=duration)

        # Create or update the subscription
        subscription, created = Subscription.objects.update_or_create(
            tenant=tenant,
            defaults={
                'plan': plan,
                'start_date': start_date,
                'end_date': end_date,
                'is_active': is_active,
                'auto_renew': False,
            }
        )

        # Log the subscription in the history table
        SubscriptionHistory.objects.create(
            tenant=tenant,
            plan=plan,
            start_date=start_date,
            end_date=end_date,
            is_active=is_active,
            auto_renew=False,
        )

        # Redirect based on the plan type
        if plan.name == SubscriptionPlan.FREE_PLAN:
            # Redirect to the free plan trial page
            return redirect('subscription:free_plan_trial')
        else:
            # Redirect to the payment options page for paid plans
            return redirect('subscription:payment_options', subscription_id=subscription.id)

    # Fetch page setup for the current tenant
    current_tenant = request.tenant
    page_setup = SetUpPage.objects.filter(tenant=current_tenant).first()

    return render(request, 'subscription/select_plan.html', {'plans': plans, 'page_setup': page_setup})

def free_plan_trial(request):
    """
    A page shown to users who selected the free plan.
    """
    return render(request, 'subscription/free_plan_trial.html')

import uuid
from django.http import HttpResponseBadRequest, HttpResponseNotFound


def select_payment(request):
    if request.method == "POST":
        # Retrieve subscription ID from POST data
        subscription_id = request.POST.get("subscription_id")
        
        print('subscription_id >><>><><>>>><<<', subscription_id)
        
        # if not subscription_id:
        #     return HttpResponseBadRequest("Missing subscription ID.")

        # Fetch the subscription or return a 404 if not found
        subscription = get_object_or_404(Subscription, id=subscription_id)
        
        print('subscription <>><>>>', subscription)

        # Retrieve payment option ID from POST data
        payment_option_id = request.POST.get("payment_option_id")
        
        print('payment_option_id <><><>>>>', payment_option_id)
        
        if not payment_option_id:
            return HttpResponseBadRequest("Missing payment option ID.")


        # Fetch the payment option or return a 404 if not found
        payment_option = get_object_or_404(PaymentOption, id=payment_option_id)
        print('payment_option<><>>>>><', payment_option)

        # Handle bank transfer payment
        if payment_option.name == "bank_transfer":
            transaction_reference = str(uuid.uuid4())  # Generate unique transaction reference
            Payment.objects.create(
                tenant=request.tenant,
                subscription=subscription,
                payment_option=payment_option,
                amount=subscription.plan.price,
                transaction_reference=transaction_reference,
                is_successful=False,
            )
            return redirect('subscription:bank_payment_pending', transaction_reference=transaction_reference)
        else:
            # Payment.objects.create(
            #     tenant = request.tenant,
            #     subscription = subscription,
            #     payment_option = payment_option,
            #     amount = subscription.plan.price,
            #     # transaction_reference = transaction_reference,
            #     is_successful = False,
                
            # )
            return redirect('subscription:initialize_payment', subscription_id=subscription.id)    
    

# @login_required
def payment_options(request, subscription_id):
    """
    Displays the available payment options for the selected subscription.
    """
    subscription = get_object_or_404(Subscription, id=subscription_id, tenant=request.tenant)
    payment_options = PaymentOption.objects.filter(is_active=True)

    if request.method == 'POST':
        payment_option_id = request.POST.get('payment_option_id')
        payment_option = get_object_or_404(PaymentOption, id=payment_option_id)

        # Create a payment record
        payment = Payment.objects.create(
            tenant=request.tenant,
            subscription=subscription,
            payment_option=payment_option,
            amount=subscription.plan.price,
            is_successful=False,  # Payment will be confirmed later
        )

        # Redirect to the payment initialization page with the subscription_id
        return redirect('subscription:initialize_payment', subscription_id=subscription.id)
    
    current_tenant = request.tenant
    page_setup = SetUpPage.objects.filter(tenant=current_tenant).first()  # Get the first setup page for the tenant
    

    return render(request, 'subscription/payment_options.html', {
        'subscription': subscription,
        'subscription_id': subscription.id,
        'payment_options': payment_options,
        'page_setup': page_setup,
    })


# @login_required
def payment_pending(request):
    """
    Handles the callback from Paystack after payment.
    Verifies the transaction and updates the payment status.
    """
    # Extract reference from callback URL
    reference = request.GET.get("reference")
    if not reference:
        return HttpResponseBadRequest("Missing transaction reference.")

    # Fetch the payment record using the transaction reference
    payment = Payment.objects.filter(transaction_reference=reference).first()
    if not payment:
        return render(
            request, 
            "subscription/payment_failed.html", 
            {"message": "Transaction reference not found."}
        )

    # Verify the transaction with Paystack
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }
    response = requests.get(
        f"https://api.paystack.co/transaction/verify/{reference}",
        headers=headers
    )

    if response.status_code == 200:
        response_data = response.json()
        if response_data["status"] and response_data["data"]["status"] == "success":
            # Mark payment as successful
            payment.is_successful = True
            payment.payment_options = 'Paystack'
            payment.processed = True
            payment.save()
            
            active_sub, created = Subscription.objects.get_or_create(tenant=request.tenant)
            
            SubscriptionHistory.objects.create(
                tenant=request.tenant,
                plan=active_sub.plan,
                start_date=active_sub.start_date,
                end_date=active_sub.end_date,
                is_active=True,
                auto_renew=active_sub.auto_renew,
            )

            Subscription.objects.update_or_create (
                tenant=request.tenant,
                defaults={
                    # "plan": plan,
                    'start_date': datetime.now(),
                    "is_active": True,
                    "auto_renew": False  # Or fetch from payment if applicable
                }
            )
            
            return render(
                request, 
                "subscription/payment_success.html", 
                {"message": "Payment was successful.", "subscription": payment.subscription}
            )
        else:
            # Payment was not successful
            return render(
                request, 
                "subscription/payment_failed.html", 
                {"message": "Payment verification failed. Please try again."}
            )
    else:
        # Failed to verify transaction
        return render(
            request, 
            "subscription/payment_failed.html", 
            {"message": "Could not verify transaction. Please contact support."}
        )
        

def payment_page(request, transaction_reference):
    try:
        payment = Payment.objects.get(transaction_reference=transaction_reference)
        if payment.is_successful:
            return render(request, "payment_already_confirmed.html")
        # Render the actual payment page otherwise
        return render(request, "payment_page.html", {"transaction_reference": transaction_reference})
    except Payment.DoesNotExist:
        return HttpResponseNotFound("Payment not found")


def bank_payment_pending(request, transaction_reference):
    payment = get_object_or_404(Payment, transaction_reference=transaction_reference)

    # Pass the payment object and countdown duration (in seconds)
    return render(request, 'subscription/bankPayment_pending.html', {
        'payment': payment,
        'countdown_duration': 45 * 60  # 45 minutes in seconds
    })

# For polling confirmation status
def check_payment_status(request, transaction_reference):
    
    print(f"Received transaction_reference: {transaction_reference}")  # Debugging

    try:
        # Fetch the payment
        payment = Payment.objects.get(transaction_reference=transaction_reference)

        # Check if the payment is already processed
        if payment.processed:
            response = {"error": "Payment already processed", "is_successful": payment.is_successful}
            print(f"Response: {response}")  # Debugging
            return JsonResponse(response, status=400)

        # If payment is successful, process it
        if payment.is_successful:
            tenant = payment.tenant

            # Fetch or create a subscription for the tenant
            active_sub, created = Subscription.objects.get_or_create(tenant=tenant)

            # Update or create subscription history
            SubscriptionHistory.objects.create(
                tenant=tenant,
                plan=active_sub.plan,
                start_date=active_sub.start_date,
                end_date=active_sub.end_date,
                is_active=True,
                auto_renew=active_sub.auto_renew,
            )

            # Update the subscription's active status
            active_sub.is_active = True
            active_sub.save()

            # Mark payment as processed
            payment.processed = True
            payment.save()

            response = {"is_successful": payment.is_successful}
            print(f"Response: {response}")  # Debugging
            return JsonResponse(response, status=200)

        # If payment is not successful
        response = {"is_successful": payment.is_successful}
        print(f"Response: {response}")  # Debugging
        return JsonResponse(response, status=200)

    except Payment.DoesNotExist:
        error_response = {"error": "Payment not found"}
        print(f"Response: {error_response}")  # Debugging
        return JsonResponse(error_response, status=404)
    
