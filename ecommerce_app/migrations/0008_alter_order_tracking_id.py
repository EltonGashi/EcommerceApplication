# Generated by Django 5.0 on 2024-01-08 00:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ecommerce_app', '0007_alter_order_tracking_id_alter_product_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='tracking_id',
            field=models.CharField(blank=True, default='430a1ad6aa504de8b6f7034c7c8a05df', max_length=255, null=True),
        ),
    ]
