from django.db import models

# Create your models here.
class Report(models.Model):
    building = models.CharField(max_length=120)
    floor = models.CharField(max_length=3)
    agency = models.CharField(max_length=255)
    tel = models.CharField(max_length=10)
    report = models.TextField()
    image=models.ImageField(upload_to="img",blank=True)
    number=models.IntegerField(blank=True)
    data = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=80,blank=True)
    details = models.TextField(blank=True)
    equipment = models.TextField(blank=True)
    type = models.CharField(max_length=50,blank=True)

    def __str__(self):
        return self.report


class Number(models.Model):
    year = models.IntegerField(default=2025)
    number=models.IntegerField(default=0)

    