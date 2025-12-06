from pyexpat.errors import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from .forms import *
from .models import *


def settings_view(request):
    # Always fetch or create a single settings record
    settings, created = GlobalSettings.objects.get_or_create(id=1)

    if request.method == "POST":
        form = SettingsForm(request.POST, instance=settings)
        if form.is_valid():
            form.save()
            
            return redirect("settings:settings_view")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = SettingsForm(instance=settings)

    return render(request, "settings_form.html", {"form": form})

def currency_list_create(request, pk=None):
    """
    Handles:
    - List all currencies
    - Create new currency
    - Edit existing currency (when pk is provided)
    """

    # If editing
    if pk:
        currency = get_object_or_404(Currency, pk=pk)
    else:
        currency = None

    # Form handling
    if request.method == 'POST':
        form = CurrencyForm(request.POST, instance=currency)
        if form.is_valid():
            form.save()
            return redirect('settings:currency_list_create')
    else:
        form = CurrencyForm(instance=currency)

    currencies = Currency.objects.all()

    return render(request, 'currency_master.html', {
        'form': form,
        'currencies': currencies,
        'edit_mode': True if pk else False,
        'edit_id': pk,
    })


def currency_delete(request, pk):
    """
    Delete a currency and redirect back to list page
    """
    currency = get_object_or_404(Currency, pk=pk)
    currency.delete()
    return redirect('currency_list_create')