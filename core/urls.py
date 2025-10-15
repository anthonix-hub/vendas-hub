from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin_page/', admin.site.urls),
    # path('', include('blog.urls', namespace='blog')),
    path('accounts/', include('accounts.urls')),  # URLs for signup and login
    path('tenant/', include('tenant.urls', namespace='tenant')),
    path('subscription/', include('subscription.urls')),
    path('tools_and_features/', include('tools_and_features.urls')),
    path('page_settings/', include('page_settings.urls')),
    
    path('ckeditor/', include('ckeditor_uploader.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

