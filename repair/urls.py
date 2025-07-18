from django.urls import path
from repair import views

urlpatterns = [
    path('',views.index),
    path('report',views.report),
    path('form',views.form)
]