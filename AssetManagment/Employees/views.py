from django.shortcuts import render, redirect
from django.urls import reverse
from Assets.models import Asset
from .models import Employee


def list_employees(request):
	employees = Employee.objects.all().order_by('-created_at')
	return render(request, 'Employees/list.html', {'employees': employees})


def create_employee(request):
	if request.method == 'POST':
		first_name = request.POST.get('first_name')
		last_name = request.POST.get('last_name')
		email = request.POST.get('email')
		asset_ids = request.POST.getlist('asset_ids')

		# basic validation
		if not first_name or not email:
			return render(request, 'Employees/create.html', { 'error': 'First name and email are required.', 'request': request })

		email = email.strip().lower()
		if Employee.objects.filter(email=email).exists():
			return render(request, 'Employees/create.html', { 'error': 'An employee with this email already exists.', 'request': request })

		employee = Employee.objects.create(first_name=first_name, last_name=last_name or '', email=email)

		# assign assets if provided and available (allow multiple)
		for aid in asset_ids:
			if not aid:
				continue
			try:
				asset = Asset.objects.get(asset_id=int(aid), deleted_at__isnull=True, assigned_to__isnull=True)
				asset.assigned_to = employee
				asset.save()
			except (Asset.DoesNotExist, ValueError):
				# skip invalid or unavailable assets
				continue

		return redirect(reverse('list_employees'))

	# GET: show form with available assets
	available_assets = Asset.objects.filter(deleted_at__isnull=True, assigned_to__isnull=True).order_by('asset_name')
	return render(request, 'Employees/create.html', {'available_assets': available_assets})
