# Generated by Django 5.2 on 2025-05-13 04:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pharmacy', '0017_salesregister_customer_mobile'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='salesregister',
            name='customer_mobile',
        ),
    ]
