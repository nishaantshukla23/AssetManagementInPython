from django.urls import path
from . import views


urlpatterns = [
    path('list/', views.list_employees, name='list_employees'),
    path('create/', views.create_employee, name='create_employee'),
]