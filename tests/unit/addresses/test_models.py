import pytest

from addresses.models import Address, AddressLines


@pytest.mark.django_db
def test_address_lines_full_address_as_dict():
    # arrange
    addr = Address.objects.create(
        country='BR',
        state="SP",
        city="itaquera",
        postal_code="57302675"
    )
    
    addr_lines = AddressLines(
        line1='liberdade, 123',
        line2='',
        address=addr
    )
    expected_result = {
        'country': addr.country,
        'state': addr.state,
        'city': addr.city,
        'postal_code': addr.postal_code,
        'line1': addr_lines.line1,
        'line2': addr_lines.line2,
    }

    # act
    result = addr_lines.full_address_as_dict()
    
    # assert
    assert result == expected_result
