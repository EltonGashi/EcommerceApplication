# Generated by Django 5.0 on 2024-01-08 16:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ecommerce_app', '0009_alter_order_tracking_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='tracking_id',
            field=models.CharField(blank=True, default='b29297bc84934569a6be4766fd463c47', max_length=255, null=True),
        ),
    ]
