# Generated by Django 5.0 on 2024-01-14 22:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ecommerce_app', '0018_alter_order_tracking_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='tracking_id',
            field=models.CharField(blank=True, default='c6332e96a609469dac51d0ecf963ebbe', max_length=255, null=True),
        ),
    ]
