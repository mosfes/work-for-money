# Generated by Django 5.2.4 on 2025-07-18 18:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("repair", "0002_alter_report_floor"),
    ]

    operations = [
        migrations.AddField(
            model_name="number",
            name="year",
            field=models.TextField(default=1, max_length=5),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="number",
            name="number",
            field=models.IntegerField(default=0),
        ),
    ]
