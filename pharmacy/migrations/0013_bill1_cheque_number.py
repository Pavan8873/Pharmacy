# Generated by Django 5.2 on 2025-05-08 05:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pharmacy', '0012_bill1_purchasehistory_batch_number_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='bill1',
            name='cheque_number',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
