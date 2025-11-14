from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .models import Asset
from datetime import date


# Create your views here.
def create_asset(request):
    if request.method == 'POST':
        # simple form handling - expects fields from the template: name and status
        name = request.POST.get('name') or request.POST.get('asset_name')
        status = request.POST.get('status') or request.POST.get('asset_status')
        description = request.POST.get('description') or request.POST.get('asset_description')
        purchase_date = request.POST.get('purchase_date') or request.POST.get('asset_purchase_date')
        value = request.POST.get('value') or request.POST.get('asset_value')

        # basic validation
        if not name:
            return render(request, 'Assets/create.html', { 'error': 'Asset name is required.', 'request': request })

        # generate a simple unique asset_id if not provided
        # use max+1 pattern; in production consider sequences or UUIDs
        last = Asset.objects.order_by('-asset_id').first()
        next_id = 1 if not last else (last.asset_id + 1)

        # Convert/clean some fields
        asset_kwargs = {
            'asset_name': name,
            'asset_status': status or 'new',
            'asset_description': description or '',
            'asset_id': next_id,
        }

        if purchase_date:
            # Expecting YYYY-MM-DD; let Django convert or raise
            asset_kwargs['asset_purchase_date'] = purchase_date
        else:
            # existing DB migration made this field NOT NULL; use today's date as a safe default
            asset_kwargs['asset_purchase_date'] = date.today()

        if value:
            try:
                asset_kwargs['asset_value'] = float(value)
            except (ValueError, TypeError):
                return render(request, 'Assets/create.html', { 'error': 'Invalid asset value', 'request': request })
        else:
            # DB currently enforces NOT NULL for asset_value in the initial migration; default to 0.00
            asset_kwargs['asset_value'] = 0.00

        asset = Asset.objects.create(**asset_kwargs)

        return redirect(reverse('list_assets'))

    # GET -> render form
    return render(request, 'Assets/create.html', { 'request': request })


def list_assets(request):
    assets = Asset.objects.filter(deleted_at__isnull=True).order_by('-created_at')
    return render(request, 'Assets/list.html', { 'assets': assets })


def edit_asset(request, asset_id):
    asset = get_object_or_404(Asset, asset_id=asset_id)

    if request.method == 'POST':
        # take submitted values and update the asset
        name = request.POST.get('name') or asset.asset_name
        status = request.POST.get('status') or asset.asset_status
        description = request.POST.get('description') or asset.asset_description
        purchase_date = request.POST.get('purchase_date') or asset.asset_purchase_date
        value = request.POST.get('value') or asset.asset_value

        asset.asset_name = name
        asset.asset_status = status
        asset.asset_description = description

        # parse and set purchase_date/value if provided
        if purchase_date:
            asset.asset_purchase_date = purchase_date

        if value:
            try:
                asset.asset_value = float(value)
            except (ValueError, TypeError):
                return render(request, 'Assets/edit.html', { 'error': 'Invalid asset value', 'asset': asset })

        asset.save()
        return redirect(reverse('view_asset', args=[asset.asset_id]))

    # GET -> show form prefilled
    return render(request, 'Assets/edit.html', {'asset': asset})


def view_asset(request, asset_id):
    asset = get_object_or_404(Asset, asset_id=asset_id)
    return render(request, 'Assets/view.html', {'asset': asset})


def delete_asset(request, asset_id):
    asset = get_object_or_404(Asset, asset_id=asset_id)
    # soft delete: set deleted_at and clear assignment
    asset.deleted_at = date.today()
    asset.assigned_to = None
    asset.save()
    return redirect(reverse('list_assets'))


