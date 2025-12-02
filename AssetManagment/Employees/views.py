from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import JsonResponse, HttpResponseBadRequest
from Assets.models import Asset, AssetAssignment
from django.utils import timezone
from .models import Employee
from Assets.models import AssetAssignment
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import authenticate, login as django_login, logout as django_logout
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from django.views.decorators.csrf import csrf_protect

def list_employees(request):
    permission_classes = [IsAuthenticated]
    print("Authenticated User:", request.user)
    print("User is authenticated:", request.user.is_authenticated)
    print(permission_classes)
    employees = Employee.objects.filter(deleted_at__isnull=True).order_by('-created_at')
    return render(request, 'Employees/list.html', {'employees': employees})


def create_employee(request):
	if request.method == 'POST':
		first_name = request.POST.get('first_name')
		last_name = request.POST.get('last_name')
		email = request.POST.get('email')

		# basic validation
		if not first_name or not email:
			return render(request, 'Employees/create.html', { 'error': 'First name and email are required.', 'request': request })

		email = email.strip().lower()
		if Employee.objects.filter(email=email).exists():
			return render(request, 'Employees/create.html', { 'error': 'An employee with this email already exists.', 'request': request })

		employee = Employee.objects.create(first_name=first_name, last_name=last_name or '', email=email)

		# No asset allocation at creation time (assignment is handled later via the employee list)
		return redirect(reverse('list_employees'))

	# GET: render create form (no asset allocation here)
	return render(request, 'Employees/create.html')


def available_assets(request, employee_id):
	# Return JSON list of available assets for assignment; supports optional search via ?q=
	q = request.GET.get('q', '').strip()
	assets_qs = Asset.objects.filter(deleted_at__isnull=True, assigned_to__isnull=True)
	if q:
		assets_qs = assets_qs.filter(asset_name__icontains=q)
	assets_qs = assets_qs.order_by('asset_name')[:100]
	data = [{'asset_id': a.asset_id, 'asset_name': a.asset_name, 'asset_status': a.asset_status} for a in assets_qs]
	return JsonResponse({'results': data})


def assign_asset(request, employee_id):
	# Assign a single available asset to the employee (POST)
	if request.method != 'POST':
		return HttpResponseBadRequest('POST required')

	asset_id = request.POST.get('asset_id')
	if not asset_id:
		return JsonResponse({'error': 'asset_id required'}, status=400)

	employee = get_object_or_404(Employee, pk=employee_id)
	try:
		asset = Asset.objects.get(asset_id=int(asset_id), deleted_at__isnull=True, assigned_to__isnull=True)
	except (Asset.DoesNotExist, ValueError):
		return JsonResponse({'error': 'asset not available'}, status=400)

	# close any open assignment records for this asset (defensive)
	AssetAssignment.objects.filter(asset=asset, unassigned_at__isnull=True).update(unassigned_at=timezone.now())

	# create a new assignment record
	AssetAssignment.objects.create(asset=asset, employee=employee)

	# mark asset as assigned and update status to in-use
	asset.assigned_to = employee
	asset.asset_status = 'in_use'
	asset.save()
	return JsonResponse({'result': 'ok', 'asset': {'asset_id': asset.asset_id, 'asset_name': asset.asset_name, 'asset_status': asset.asset_status}})


def employee_history(request, employee_id):
	employee = get_object_or_404(Employee, pk=employee_id)
	assignments = AssetAssignment.objects.filter(employee=employee).select_related('asset').order_by('-assigned_at')
	return render(request, 'Employees/asset_history.html', {'employee': employee, 'assignments': assignments})


def delete_employee(request, employee_id):
	"""Soft-delete an employee: set deleted_at, unassign any assets and close assignment records."""
	if request.method != 'POST':
		# for safety require POST
		return HttpResponseBadRequest('POST required')

	employee = get_object_or_404(Employee, pk=employee_id, deleted_at__isnull=True)

	# find assets currently assigned to this employee (and not deleted)
	assets = Asset.objects.filter(assigned_to=employee, deleted_at__isnull=True)

	# close any open assignment records for those assets
	AssetAssignment.objects.filter(asset__in=assets, unassigned_at__isnull=True).update(unassigned_at=timezone.now())

	# unassign assets and set status to available
	for a in assets:
		a.assigned_to = None
		a.asset_status = 'available'
		a.save()

	# soft-delete employee
	employee.deleted_at = timezone.now()
	employee.save()

	# respond with simple JSON if requested via fetch, otherwise redirect back to list
	from django.http import JsonResponse
	if request.headers.get('x-requested-with') == 'XMLHttpRequest':
		return JsonResponse({'result': 'ok', 'employee_id': employee_id})

	return redirect(reverse('list_employees'))


def manage_assets(request, employee_id):
	"""Server-rendered page to view available assets and assign one to the employee.

	This replaces the client-side modal + AJAX approach: assignment happens via regular POST form.
	"""
	employee = get_object_or_404(Employee, pk=employee_id, deleted_at__isnull=True)

	if request.method == 'POST':
		asset_id = request.POST.get('asset_id')
		if not asset_id:
			return render(request, 'Employees/manage_assets.html', {'employee': employee, 'assets': [], 'error': 'asset_id required'})

		try:
			asset = Asset.objects.get(asset_id=int(asset_id), deleted_at__isnull=True, assigned_to__isnull=True)
		except (Asset.DoesNotExist, ValueError):
			return render(request, 'Employees/manage_assets.html', {'employee': employee, 'assets': Asset.objects.filter(deleted_at__isnull=True, assigned_to__isnull=True).order_by('asset_name'), 'error': 'Asset not available'})

		# close any open assignment records for this asset
		AssetAssignment.objects.filter(asset=asset, unassigned_at__isnull=True).update(unassigned_at=timezone.now())

		# create assignment and mark asset in-use
		AssetAssignment.objects.create(asset=asset, employee=employee)
		asset.assigned_to = employee
		asset.asset_status = 'in_use'
		asset.save()

		return redirect(reverse('list_employees'))

	# GET: show available assets
	assets = Asset.objects.filter(deleted_at__isnull=True, assigned_to__isnull=True).order_by('asset_name')
	return render(request, 'Employees/manage_assets.html', {'employee': employee, 'assets': assets})


@csrf_protect
def register_view(request):
	"""Register a new Django user and issue JWT tokens (set as HttpOnly cookies).

	After successful registration the user is also logged in via Django session to make
	server-rendered pages work without additional middleware.
	"""
	if request.method == 'POST':
		username = request.POST.get('username', '').strip()
		email = request.POST.get('email', '').strip().lower()
		password = request.POST.get('password', '')
		password2 = request.POST.get('password2', '')

		if not username or not email or not password:
			return render(request, 'Auth/register.html', {'error': 'All fields required', 'username': username, 'email': email})
		if password != password2:
			return render(request, 'Auth/register.html', {'error': 'Passwords do not match', 'username': username, 'email': email})
		if User.objects.filter(username=username).exists():
			return render(request, 'Auth/register.html', {'error': 'Username already taken', 'username': username, 'email': email})
		if User.objects.filter(email=email).exists():
			return render(request, 'Auth/register.html', {'error': 'Email already registered', 'username': username, 'email': email})

		user = User.objects.create_user(username=username, email=email, password=password)

		# issue JWT tokens
		refresh = RefreshToken.for_user(user)
		access_token = str(refresh.access_token)
		refresh_token = str(refresh)

		# login user with Django session too (makes server-rendered pages recognize user)
		django_login(request, user)

		resp = redirect(reverse('list_assets'))
		# set tokens as HttpOnly cookies
		resp.set_cookie('access_token', access_token, httponly=True, samesite='Lax')
		resp.set_cookie('refresh_token', refresh_token, httponly=True, samesite='Lax')
		return resp

	return render(request, 'Auth/register.html')


@csrf_protect
def login_view(request):
	"""Login a user and issue JWT tokens as HttpOnly cookies, plus Django session login."""
	if request.method == 'POST':
		username = request.POST.get('username', '').strip()
		password = request.POST.get('password', '')
		user = authenticate(request, username=username, password=password)
		if user is not None:
			django_login(request, user)
			refresh = RefreshToken.for_user(user)
			access_token = str(refresh.access_token)
			refresh_token = str(refresh)
			resp = redirect(reverse('list_assets'))
			resp.set_cookie('access_token', access_token, httponly=True, samesite='Lax')
			resp.set_cookie('refresh_token', refresh_token, httponly=True, samesite='Lax')
			return resp
		else:
			return render(request, 'Auth/login.html', {'error': 'Invalid credentials', 'username': username})

	return render(request, 'Auth/login.html')


def logout_view(request):
	"""Logout: remove session and clear JWT cookies. Optionally blacklist refresh token if implemented."""
	django_logout(request)
	resp = redirect(reverse('home'))
	resp.delete_cookie('access_token')
	resp.delete_cookie('refresh_token')
	return resp
