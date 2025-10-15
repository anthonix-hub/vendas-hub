from django import forms
from .models import *

class SetUpPageForm(forms.ModelForm):
    reset_defaults = forms.BooleanField(
        required=False,
        label="Reset to Default",
        help_text="Check this box to reset all settings to default."
    )

    class Meta:
        model = SetUpPage
        fields = [
            "font_type",
            "header_footer_color",
            "header_footer_color_shade",
            "logo",
            "banner",
            "background_color",
            "background_color_shade",
            "text_color",
            "text_color_shade",
            "button_color",
            "button_color_shade",
            "reset_defaults",  # Add reset option
        ]

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data.get("reset_defaults"):  # If user checked reset
            cleaned_data["font_type"] = SetUpPage.FONT_SANS
            cleaned_data["header_footer_color"] = SetUpPage.COLOR_GRAY
            cleaned_data["header_footer_color_shade"] = "500"
            cleaned_data["background_color"] = SetUpPage.COLOR_GRAY
            cleaned_data["background_color_shade"] = "100"
            cleaned_data["text_color"] = SetUpPage.COLOR_GRAY
            cleaned_data["text_color_shade"] = "700"
            cleaned_data["button_color"] = SetUpPage.COLOR_GREEN
            cleaned_data["button_color_shade"] = "500"
            cleaned_data["logo"] = None
            cleaned_data["banner"] = None

        return cleaned_data
        # widgets = {
            # "custom_css": forms.Textarea(attrs={"rows": 4, "placeholder": "Enter custom CSS here..."}),
        # }

class DeliveryMethodForm(forms.ModelForm):
    class Meta:
        model = DeliveryMethod
        fields = [
            'delivery_point',
            'delivery_note',
            'delivery_amount',
            'delivery_type',
            'estimated_delivery_time',
            'is_active',
            'region_served',
            'max_weight_limit',
            'max_package_dimensions',
            'cutoff_time',
            'available_days',
            'supports_tracking',
            'handling_fee',
        ]
        widgets = {
            'cutoff_time': forms.TimeInput(attrs={'type': 'time'}),
        }