import os
from uuid import uuid4

import stripe
import stripe.error
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class StripeCustomerManager(models.Manager):
    def new(self, user: AbstractUser, **kwargs) -> "StripeCustomer":
        """Creates a stripe customer passing the email, phone, name (by get_full_name), address (if exists)
        username (by metadata) and store the user instance and his stripe customer id.

        Args:
            user (AbstractUser): the user attributed to the stripe customer object.
            kwargs (Mapping, optional): get the customer_id if given and extra arguments sent to stripe.Customer.create method.
        """
        if not isinstance(user, AbstractUser) or self.filter(user=user).exists():
            return self.create(user=user, customer_id=kwargs.get('customer_id'))

        user_address = user.address.full_address_as_dict() if user.address is not None else None
        idempotency_key = uuid4()
        created = stripe.Customer.create(
            address=user_address,
            email=user.email,
            metadata={'username': user.username},
            name=user.get_full_name(),
            phone=user.phone,
            idempotency_key=str(idempotency_key),
            **kwargs
        )
        return self.create(user=user, customer_id=created.id, idempotency_key=idempotency_key)


class StripeCustomer(models.Model):
    """Model that represent the stripe customer object storing the user which the stripe
    customer object refers and the stripe customer id.

    Args:
        customer_id (Charfield, required): the stripe customer id.
        user (ForeignKey, required): the user which the customer object refers.
    """
    customer_id = models.CharField(
        max_length=100,
        unique=True,
        validators=[
            RegexValidator(
                r'^cus_\w+$', _("invalid customer id"),
                code='invalid_stripe_customer_id',
            )
        ]
    )
    idempotency_key = models.UUIDField(default=uuid4, editable=False)
    user = models.OneToOneField(
        get_user_model(),
        on_delete=models.DO_NOTHING,
        related_name='stripe_customer',
    )

    objects: StripeCustomerManager = StripeCustomerManager()

    class Meta:
        verbose_name = _("stripe customer")
        verbose_name_plural = _("stripe customers")

    def __str__(self):
        return self.customer_id

    def delete(self, *args, **kwargs) -> tuple[tuple[int, dict[str, int]], bool]:
        """deletes the customer from the stripe and database
        
        Returns:
            tuple[tuple[int, dict[str, int]], bool]: the original `delete` method return and the
            value from the `deleted` field of the delete method from `stripe.Customer.delete` method.
        """
        deleted = stripe.Customer.delete(self.customer_id)
        if not deleted.deleted:
            raise stripe.StripeError('The stripe customer was not deleted')

        return super().delete(*args, **kwargs), deleted.deleted

    def update(self, **kwargs) -> stripe.Customer:
        """update the customer on stripe just calling `stripe.Customer.modify` passing
        the given kwargs"""
        return stripe.Customer.modify(self.customer_id, **kwargs)
