from django.urls import path
from repair import views

urlpatterns = [
    path("", views.index),
    path("report", views.report, name="report"),
    path("report_form", views.report_form),
    path("update-repair/", views.update_repair_from_modal, name="update_repair"),
    path("download/<int:report_id>/", views.download_pdf, name="download_pdf"),
    path("api/report-type-counts/", views.report_type_counts_api),
]
