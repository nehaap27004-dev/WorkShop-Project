from django.urls import path
from . import views

urlpatterns = [
    path("sample/", views.sample_pdf, name="sample_pdf"),
    path("inspection/<int:pk>/", views.inspection_pdf, name="inspection_pdf"),
]