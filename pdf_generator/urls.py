from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path("sample/", views.sample_pdf, name="sample_pdf"),
    
    path("inspection/<int:pk>/", views.inspection_pdf, name="inspection_pdf"),
    path("regular-inspection/<int:pk>/", views.regular_inspection_pdf, name="regular_inspection_pdf"),
    path("custom-inspection/<int:pk>/", views.custom_inspection_pdf, name="custom_inspection_pdf"),
    path("invoice/<int:pk>/", views.invoice_pdf, name="invoice_pdf"),
    path("estimate/<int:pk>/", views.estimate_pdf, name="estimate_pdf"),
    path("quotation/<int:pk>/", views.quotation_pdf, name="quotation_pdf"),
    path("delivery-note/<int:pk>/", views.delivery_pdf, name="delivery_pdf"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)