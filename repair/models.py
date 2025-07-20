from django.db import models

# Create your models here.
class Report(models.Model):
    id = models.AutoField(primary_key=True)
    building = models.CharField(max_length=120)
    floor = models.CharField(max_length=3)
    agency = models.CharField(max_length=255)
    tel = models.CharField(max_length=10)
    report = models.TextField()
    image=models.ImageField(upload_to="img",blank=True)
    number=models.IntegerField(blank=True)
    data = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=80,blank=True)
    details = models.TextField(blank=True)
    equipment = models.TextField(blank=True)
    type = models.CharField(max_length=50,blank=True)
    task_status = models.CharField(default="0", max_length=1)

    def __str__(self):
        return self.report


class Number(models.Model):
    year = models.IntegerField(default=2025)
    number=models.IntegerField(default=0)

    