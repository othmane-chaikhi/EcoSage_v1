# Generated by Django 5.0.4 on 2024-05-28 15:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('EcoSageApp', '0004_transaction_title'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='useraccount',
            name='balance',
        ),
    ]
