import pytest
from models.order import Order


@pytest.fixture
def sample_order():
    return Order(
        customer_name="John Doe",
        item="MacBook Pro",
        quantity=1,
        price=100,
    )
