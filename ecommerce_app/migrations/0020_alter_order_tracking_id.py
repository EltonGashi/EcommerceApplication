# Generated by Django 5.0 on 2024-01-14 22:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ecommerce_app', '0019_alter_order_tracking_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='tracking_id',
            field=models.CharField(blank=True, default='ffa04461f15642eb96697426daa4daf5', max_length=255, null=True),
        ),
    ]
