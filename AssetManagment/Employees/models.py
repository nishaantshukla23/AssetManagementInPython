from django.db import models


# Create your models here.
class Employee(models.Model):
	first_name = models.CharField(max_length=80)
	last_name = models.CharField(max_length=80, blank=True)
	email = models.EmailField(unique=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"{self.first_name} {self.last_name}" if self.last_name else self.first_name
