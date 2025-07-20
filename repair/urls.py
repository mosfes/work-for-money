from django.urls import path
from repair import views

urlpatterns = [
    path('',views.index),
    path('report',views.report, name='report'),
    path('report_form',views.report_form),
    path('update-repair/', views.update_repair_from_modal, name='update_repair'),
]