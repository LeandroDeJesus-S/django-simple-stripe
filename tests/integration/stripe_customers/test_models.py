import os
from pathlib import Path

import pytest
import stripe
from dotenv import load_dotenv

from stripe_customers.models import StripeCustomer

load_dotenv(Path(__file__).parent.parent.parent.parent / '.env')


@pytest.mark.django_db
def test_stripe_customer_manager_new(admin_user):
    """test if the method `new` from `StripeCustomerManager` creates a new customer
    on stripe and store the user and the customer id
    """
    stripe_key = os.environ['STRIPE_SECRET_KEY_TEST']
    new_customer = StripeCustomer.objects.new(admin_user, stripe_api_key=stripe_key)
    stipe_customer = stripe.Customer.retrieve(new_customer.customer_id, api_key=stripe_key)
    customer_username = stipe_customer['metadata'].get('username')

    assert new_customer.user.username == customer_username

    deleted = stripe.Customer.delete(new_customer.customer_id, api_key=stripe_key)
    assert deleted.deleted, 'The stripe customer was not deleted'


@pytest.mark.django_db
def test_stripe_customer_delete(admin_user):
    """test if the delete method deletes the customer on the stripe platform"""
    stripe_key = os.environ['STRIPE_SECRET_KEY_TEST']
    new_customer = StripeCustomer.objects.new(admin_user, stripe_api_key=stripe_key)
    
    result = new_customer.delete()
    deleted = result[1]
    assert deleted
