# Generated by Django 5.2 on 2025-05-15 10:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pharmacy', '0033_alter_bill1_bill_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bill1',
            name='combined_pay',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
