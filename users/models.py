from django.db import models
from django.contrib.auth.models import AbstractUser
from phonenumber_field.modelfields import PhoneNumberField
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinLengthValidator


class CustomUser(AbstractUser):
    first_name = models.CharField(
        _("first name"),
        max_length=150,
        validators=[
            MinLengthValidator(
                limit_value=2,
                message=_("The fist name must have at least 2 chars")
            )
        ]
    )
    last_name = models.CharField(
        _("last name"),
        max_length=150,
        validators=[
            MinLengthValidator(
                limit_value=2,
                message=_("The last name must have at least 2 chars")
            )
        ]
    )
    email = models.EmailField(_("email address"), unique=True)
    phone = PhoneNumberField(_("phone number"), unique=True)
    address = models.ForeignKey(
        "addresses.AddressLines",
        on_delete=models.DO_NOTHING,
        verbose_name=_("address"),
        related_name='users',
        related_query_name='user',
        blank=True,
        null=True,
    )

    def __str__(self) -> str:
        """return the full name or the username if the full is empty"""
        return self.get_full_name() or self.username
