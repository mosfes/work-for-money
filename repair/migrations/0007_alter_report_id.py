# Generated by Django 5.2.4 on 2025-07-19 17:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("repair", "0006_alter_report_data"),
    ]

    operations = [
        migrations.AlterField(
            model_name="report",
            name="id",
            field=models.AutoField(primary_key=True, serialize=False),
        ),
    ]
