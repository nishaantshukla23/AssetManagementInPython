from django.urls import path
from . import views


urlpatterns = [
    path('list/', views.list_employees, name='list_employees'),
    path('create/', views.create_employee, name='create_employee'),
    path('<int:employee_id>/available-assets/', views.available_assets, name='available_assets'),
    path('<int:employee_id>/assign-asset/', views.assign_asset, name='assign_asset'),
    path('<int:employee_id>/asset-history/', views.employee_history, name='employee_history'),
    path('<int:employee_id>/delete/', views.delete_employee, name='delete_employee'),
    path('<int:employee_id>/manage-assets/', views.manage_assets, name='manage_assets'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]