# Generated by Django 5.1.3 on 2024-11-17 15:43

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Address',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('country', models.CharField(max_length=2, verbose_name='country')),
                ('state', models.CharField(max_length=2, verbose_name='state')),
                ('city', models.CharField(max_length=255, verbose_name='city')),
                ('postal_code', models.CharField(max_length=15, verbose_name='postal code')),
            ],
            options={
                'verbose_name': 'Address',
                'verbose_name_plural': 'Addresses',
            },
        ),
        migrations.CreateModel(
            name='AddressLines',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('line1', models.CharField(max_length=150, verbose_name='line 1')),
                ('line2', models.CharField(blank=True, max_length=150, verbose_name='line 2')),
                ('address', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='addresses.address')),
            ],
            options={
                'verbose_name': 'Address lines',
                'verbose_name_plural': 'Addresse lines',
            },
        ),
    ]