# Generated by Django 5.0 on 2024-01-07 23:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ecommerce_app', '0002_alter_order_tracking_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='product_images/'),
        ),
        migrations.AlterField(
            model_name='order',
            name='tracking_id',
            field=models.CharField(blank=True, default='c51b5152a59a48718adfd7bbf1152105', max_length=255, null=True),
        ),
    ]
