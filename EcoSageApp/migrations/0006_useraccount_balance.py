# Generated by Django 5.0.4 on 2024-05-28 15:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('EcoSageApp', '0005_remove_useraccount_balance'),
    ]

    operations = [
        migrations.AddField(
            model_name='useraccount',
            name='balance',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
    ]
