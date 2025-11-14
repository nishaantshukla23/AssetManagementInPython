from django.db import models


# Create your models here.
class Asset(models.Model):
    asset_name = models.CharField(max_length=100)
    asset_description = models.TextField(blank=True)
    asset_purchase_date = models.DateField(null=True, blank=True)
    asset_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    # use CharField for status and limit choices in business logic or admin
    asset_status = models.CharField(max_length=150, default='new')
    # Django IntegerField doesn't accept max_length
    asset_id = models.IntegerField(unique=True)
    # assignment: one asset can be assigned to one employee; use string reference to avoid import cycles
    assigned_to = models.ForeignKey('Employees.Employee', null=True, blank=True, on_delete=models.SET_NULL, related_name='assets')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.asset_name