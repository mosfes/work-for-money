# Generated by Django 5.2.4 on 2025-07-18 16:04

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Number",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("number", models.IntegerField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name="Report",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("building", models.CharField(max_length=120)),
                ("floor", models.CharField(max_length=2)),
                ("agency", models.CharField(max_length=255)),
                ("tel", models.CharField(max_length=10)),
                ("report", models.TextField()),
                ("image", models.ImageField(blank=True, upload_to="img")),
                ("number", models.IntegerField(blank=True)),
                ("data", models.DateField(auto_now_add=True)),
                ("status", models.CharField(blank=True, max_length=80)),
                ("details", models.TextField(blank=True)),
                ("equipment", models.TextField(blank=True)),
                ("type", models.CharField(blank=True, max_length=50)),
            ],
        ),
    ]
