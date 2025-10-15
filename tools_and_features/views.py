from django.shortcuts import render, redirect, get_object_or_404
from django.core.files.storage import default_storage
from django.conf import settings
from tools_and_features.forms import *
from tools_and_features.models import *
from tenant.views import *
import os
import requests
from django.contrib import messages
from django.core.mail import send_mail

from django.db import close_old_connections
from django.contrib.auth.decorators import login_required



def remove_bg(request):
    if request.method == 'POST' and request.FILES.get('image'):
        # Save the uploaded image
        uploaded_image = request.FILES['image']
        image_path = default_storage.save(f"input/{uploaded_image.name}", uploaded_image)

        # Get the full path of the uploaded image
        input_full_path = os.path.join(settings.MEDIA_ROOT, image_path)

        # API endpoint and headers
        url = 'https://api.remove.bg/v1.0/removebg'
        api_key = 'dNtWZjMYRZ2AbRSgniZ2bm2K'  # API key goes here
        headers = {'X-Api-Key': api_key}

        # Read the image and send it to remove.bg
        with open(input_full_path, 'rb') as image_file:
            response = requests.post(
                url,
                files={'image_file': image_file},
                data={'size': 'auto'},
                headers=headers
            )

        # Check for successful response
        if response.status_code == requests.codes.ok:
            # Define output path
            output_directory = os.path.join(settings.MEDIA_ROOT, "output")
            os.makedirs(output_directory, exist_ok=True)
            output_path = os.path.join(output_directory, f"no-bg_{uploaded_image.name}")

            # Save the image without the background
            with open(output_path, 'wb') as out_file:
                out_file.write(response.content)

            # Get the URLs for saving and downloading
            output_url = f"{settings.MEDIA_URL}output/no-bg_{uploaded_image.name}"
            download_url = f"{settings.MEDIA_URL}output/no-bg_{uploaded_image.name}"

            # Render the result with save and download options
            return render(request, 'tools_and_features/result.html', {
                'output_image_url': output_url,
                'download_url': download_url
            })
        else:
            error_message = f"Error: {response.status_code} {response.text}"
            return render(request, 'tools_and_features/error.html', {'error_message': error_message})

    return render(request, 'tools_and_features/upload.html')


from django.shortcuts import redirect
from django.core.files.storage import default_storage
import os
import requests

def save_image(request):
    if request.method == 'POST':
        image_url = request.POST.get('image_url')
        if image_url:
            # Download and save the image locally or associate with a user
            response = requests.get(image_url)
            if response.status_code == 200:
                file_name = os.path.basename(image_url)
                save_path = default_storage.save(f"saved_images/{file_name}", response.content)
                return redirect('success_page')  # Redirect to a success page

    return redirect('error_page')  # Redirect to an error page



def useful_tools(request):

    return render(request,'tools_and_features/useful_tools.html',None)    

@csrf_exempt
def track_exit(request):
    print(">>>>>>>>>>>>>>>> Session tracking started >>>>>>>>>>>>>>")
    session_key = request.session.session_key

    if not session_key:
        request.session.create()
        session_key = request.session.session_key

    if "visit_start_time" in request.session:
        start_time = datetime.fromisoformat(request.session["visit_start_time"])
        end_time = datetime.now()
        duration = (end_time - start_time).seconds  # Get duration in seconds

        print(">>>>>>>>>>>>>>>> Within the session >>>>>>>>>>>>>>")

        StoreVisit.objects.update_or_create(
            session_id=session_key,
            defaults={"duration": duration, "end_time": end_time}
        )
        del request.session["visit_start_time"]  # Clear session time

    return JsonResponse({"status": "success"})


def price_calculator(request):
    """
    Calculates the selling price based on:
      - cost (production or purchase)
      - shipping_cost
      - other_expenses
      - markup_percent and tax_percent percentages

    Formula:
        production_cost = cost + shipping_cost + other_expenses
        selling_price = production_cost * (1 + markup_percent/100) * (1 + tax_percent/100)
        profit = selling_price - production_cost
    """
    context = {}
    if request.method == "POST":
        try:
            cost = float(request.POST.get("cost", 0))
            shipping_cost = float(request.POST.get("shipping_cost", 0))
            other_expenses = float(request.POST.get("other_expenses", 0))
            markup_percent = float(request.POST.get("markup_percent", 0))
            tax_percent = float(request.POST.get("tax_percent", 0))
            
            production_cost = cost + shipping_cost + other_expenses
            selling_price = production_cost * (1 + markup_percent/100) * (1 + tax_percent/100)
            profit = selling_price - production_cost
            
            context.update({
                "selling_price": round(selling_price, 2),
                "profit": round(profit, 2),
                "cost": cost,
                "shipping_cost": shipping_cost,
                "other_expenses": other_expenses,
                "markup_percent": markup_percent,
                "tax_percent": tax_percent,
            })
        except ValueError:
            messages.error(request, "Please enter valid numbers for all fields.")
    return render(request, "tools_and_features/price_calculator.html", context)


def low_stock_alert(request):
    """
    Checks all products against a threshold. If a product's stock is below the threshold, it:
      - Sends an email alert to the configured admin email(s)
      - Optionally marks the product as low stock (or auto-hides it from the storefront)
    """
    # Define a low-stock threshold (this value can be customized or made configurable)
    threshold = 10

    # Find products where stock is below the threshold
    low_stock_products = Product.objects.filter(stock__lt=threshold)

    if low_stock_products.exists():
        # Prepare a simple report of low stock items
        product_lines = []
        for product in low_stock_products:
            product_lines.append(f"{product.name}: Only {product.stock} left")
        product_list = "\n".join(product_lines)

        # Email alert details (ensure you have ADMIN_EMAIL or similar in settings)
        subject = "Low Stock Alert"
        message = (
            "The following products have low stock levels:\n\n"
            f"{product_list}\n\n"
            "Please restock these items as soon as possible."
        )
        recipient_list = [email.strip() for email in settings.ADMIN_EMAILS.split(",")]
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list, fail_silently=False)

        # Optionally mark these products as low stock (if you have an is_low_stock field)
        low_stock_products.update(is_low_stock=True)

        messages.info(request, "Low stock alerts sent for products below the threshold.")
    else:
        messages.info(request, "All products are sufficiently stocked.")

    # Redirect to a dashboard or management page (adjust the name as needed)
    return redirect("tenant:dashboard")