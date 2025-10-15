from django.urls import path
from . import views
# from tenant.views import tenant_signup

app_name = 'accounts'

urlpatterns = [
    path('signup/', views.user_signup, name='user_signup'),
    path('login/', views.user_login, name='user_login'),
    # path('tenant_signup/', tenant_signup, name='tenant_signup'),
]
