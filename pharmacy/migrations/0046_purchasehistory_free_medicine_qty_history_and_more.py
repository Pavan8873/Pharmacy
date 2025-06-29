# Generated by Django 5.2 on 2025-06-06 05:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pharmacy', '0045_alter_purchasehistory_qty_in_strip'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchasehistory',
            name='free_medicine_qty_history',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='purchasehistory',
            name='qty_in_strip_history',
            field=models.DecimalField(decimal_places=1, default=1, max_digits=5),
            preserve_default=False,
        ),
    ]
