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


class AssetAssignment(models.Model):
    """Historic record of an asset being assigned to an employee.

    - asset: which asset
    - employee: to whom it was assigned
    - assigned_at: when assignment happened
    - unassigned_at: when it ended (null if still assigned)
    """
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='assignments')
    employee = models.ForeignKey('Employees.Employee', on_delete=models.CASCADE, related_name='asset_assignments')
    assigned_at = models.DateTimeField(auto_now_add=True)
    unassigned_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-assigned_at']

    def __str__(self):
        return f"{self.asset.asset_name} -> {self.employee} @ {self.assigned_at:%Y-%m-%d %H:%M}"