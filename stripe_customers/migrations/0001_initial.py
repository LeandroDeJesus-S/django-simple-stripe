# Generated by Django 5.1.3 on 2024-11-17 15:37

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='StripeCustomer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('customer_id', models.CharField(max_length=100, unique=True, validators=[django.core.validators.RegexValidator('^cus_\\w+$', 'invalid customer id', code='invalid_stripe_customer_id')])),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'stripe customer',
                'verbose_name_plural': 'stripe customers',
            },
        ),
    ]
