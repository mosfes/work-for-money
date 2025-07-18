from django.urls import path
from repair import views

urlpatterns = [
    path('',views.index),
    path('report',views.report),
    path('report_form',views.report_form)
]