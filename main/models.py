from django.db import models
from django.contrib.auth.models import User  

import datetime

# Create your models here.
def get_upload_path(instance, filename):
    return 'documents/{0}/static/{1}/{2}'.format(instance.name_of_employee.user.username, instance.name_of_employee.name, filename)

class EmployeeInfo(models.Model):
    name = models.CharField(max_length=50, blank=True, null=True)
    employee_id = models.CharField(max_length=20, blank=True, null=True)
    Birthday = models.DateField(blank=True, null=True)
    Gender = models.CharField(max_length=6, blank=True, null=True)
    user=models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)

class Images(models.Model):
    name_of_employee = models.ForeignKey(EmployeeInfo, on_delete=models.CASCADE)
    images = models.ImageField(upload_to=get_upload_path)


