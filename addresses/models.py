from typing import Any

from django.db import models
from django.utils.translation import gettext_lazy as _


class Address(models.Model):
    """model that represent the base address information.

    Args:
        country (CharField): the address country.
        state (CharField): the state from the address.
        city (CharField): the address city.
        postal_code (CharField):
    """
    country = models.CharField(_("country"), max_length=2)
    state = models.CharField(_("state"), max_length=2)
    city = models.CharField(_("city"), max_length=255)
    postal_code = models.CharField(_("postal code"), max_length=15)

    class Meta:
        verbose_name = _("Base address")
        verbose_name_plural = _("Base addresses")


class AddressLines(models.Model):
    """Store the line fields of an address
    
    Args:
        line1 (CharField, required): the first line of the address.
        line2 (CharField, optional): the second line of the address.
    """
    line1 = models.CharField(_("line 1"),  max_length=150)
    line2 = models.CharField(_("line 2"),  max_length=150, blank=True)
    address = models.ForeignKey(Address, on_delete=models.DO_NOTHING)

    class Meta:
        verbose_name = _("Address lines")
        verbose_name_plural = _("Address lines")
    
    def __str__(self):
        return self.line1
    
    def full_address_as_dict(self) -> dict[str, Any]:
        """return the complete address in dictionary format"""
        return {
            'country': self.address.country,
            'state': self.address.state,
            'city': self.address.city,
            'postal_code': self.address.postal_code,
            'line1': self.line1,
            'line2': self.line2,
        }
