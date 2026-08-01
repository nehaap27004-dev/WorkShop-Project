from django.shortcuts import render, redirect, get_object_or_404
from asset_app.models import *
from asset_app.forms import *
from accounts_app.models import LedgerCreation, Groups

def asset_master_view(request, pk=None):

    if pk:
        asset = get_object_or_404(AssetMaster, pk=pk)
    else:
        asset = None

    if request.method == "POST":

        if asset:
            form = AssetMasterForm(request.POST, instance=asset)
        else:
            form = AssetMasterForm(request.POST)

        if form.is_valid():

            asset_obj = form.save(commit=False)

            ledger_name = f"{asset_obj.asset_name}_{asset_obj.asset_code}"

            fixed_asset_group = Groups.objects.get(id=15)

            # EDIT
            if asset and asset.ledger:

                ledger = asset.ledger
                ledger.ledger_name = ledger_name
                ledger.groups = fixed_asset_group
                ledger.save()

            # CREATE
            else:

                ledger = LedgerCreation.objects.create(
                    ledger_name=ledger_name,
                    groups=fixed_asset_group
                )

                asset_obj.ledger = ledger

            asset_obj.save()

            return redirect('asset_app:asset_master')

    else:

        if asset:
            form = AssetMasterForm(instance=asset)
        else:
            form = AssetMasterForm()

    assets = AssetMaster.objects.all().order_by('-id')

    return render(request, 'asset_master.html', {
        'form': form,
        'assets': assets,
        'edit_id': pk
    })

def asset_delete(request, pk):

    asset = get_object_or_404(AssetMaster, pk=pk)

    if asset.ledger:
        asset.ledger.delete()

    asset.delete()

    return redirect('asset_app:asset_master')