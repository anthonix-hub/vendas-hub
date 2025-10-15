from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import *
from .forms import *




def settings_page(request):
    # Get the current tenant
    current_tenant = request.tenant

    # Retrieve or create the setup for the current tenant
    setup_page, created = SetUpPage.objects.get_or_create(tenant=current_tenant)

    if request.method == "POST":
        form = SetUpPageForm(request.POST, request.FILES, instance=setup_page)

        if form.is_valid():
            if form.cleaned_data.get("reset_defaults"):
                # Reset to default values
                setup_page.font_type = SetUpPage.FONT_SANS
                setup_page.header_footer_color = SetUpPage.COLOR_GRAY
                setup_page.header_footer_color_shade = "500"
                setup_page.background_color = SetUpPage.COLOR_GRAY
                setup_page.background_color_shade = "100"
                setup_page.text_color = SetUpPage.COLOR_GRAY
                setup_page.text_color_shade = "100"
                setup_page.button_color = SetUpPage.COLOR_GREEN
                setup_page.button_color_shade = "500"
                setup_page.logo = None
                setup_page.banner = None
                setup_page.save()
                messages.success(request, "Settings have been reset to default!")
            else:
                form.save()
                messages.success(request, "Page settings updated successfully!")

            return redirect("tenant:dashboard")  # Adjust to your actual redirect URL
        else:
            messages.error(request, "There was an error updating the settings.")
    else:
        form = SetUpPageForm(instance=setup_page)

    context = {
        "form": form,
        "setup_page": setup_page,
    }
    return render(request, "page_settings/PageSet_up.html", context)


def delivery_method_create(request):
    if request.method == "POST":
        form = DeliveryMethodForm(request.POST)
        if form.is_valid():
            delivery_method = form.save(commit=False)
            delivery_method.tenant_user = request.tenant  # Assign tenant dynamically
            delivery_method.save()
            return redirect('page_settings:delivery_methods_list')
    else:
        form = DeliveryMethodForm()
    return render(request, "page_settings/delivery_method_form.html", {"form": form})


# @login_required
def delivery_methods_list(request):
    methods = DeliveryMethod.objects.filter(tenant_user=request.tenant)
    return render(request, "page_settings/delivery_methods_list.html", {"methods": methods})



def delivery_method_edit(request, id):
    delivery_method = get_object_or_404(DeliveryMethod, id=id, tenant_user=request.tenant)
    if request.method == "POST":
        form = DeliveryMethodForm(request.POST, instance=delivery_method)
        if form.is_valid():
            form.save()
            return redirect('page_settings:delivery_methods_list')
    else:
        form = DeliveryMethodForm(instance=delivery_method)
    return render(request, "page_settings/delivery_method_form.html", {"form": form})


def delivery_method_delete(request, id):
    delivery_method = get_object_or_404(DeliveryMethod, id=id, tenant_user=request.tenant)
    if request.method == "POST":
        delivery_method.delete()
        return redirect('page_settings:delivery_methods_list')
    return render(request, "/confirm_delete.html", {"delivery_method": delivery_method})


def settings(request):
    
    return render(request, 'page_settings/settings.html',None)
















