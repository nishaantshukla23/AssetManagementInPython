from django.urls import path
from Assets import views


urlpatterns = [
    path('create/', views.create_asset, name='create_asset'),
    path('list/', views.list_assets, name='list_assets'),
    path('edit/<int:asset_id>/', views.edit_asset, name='edit_asset'),
    path('view/<int:asset_id>/', views.view_asset, name='view_asset'),
    path('delete/<int:asset_id>/', views.delete_asset, name='delete_asset'),
]