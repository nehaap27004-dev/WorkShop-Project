
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.urls import path, include




urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
    path('', include(('accounts_app.urls','accounts_app'), namespace='accounts_app')),
    path('', include(('fleet_app.urls', 'fleet_app'), namespace='fleet_app')),
    path('', include(('item_master.urls', 'item_master'), namespace='item_master')),
    path('', include(('settings.urls', 'settings'), namespace='settings')),
    path('', include(('audit_app.urls', 'audit_app'), namespace='audit_app')),
    path('', include(('asset_app.urls', 'asset_app'), namespace='asset_app')),
    path('jobcard/', include('jobcard_app.urls', namespace='jobcard_app')),
    
   
    
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)