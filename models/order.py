import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class Order(BaseModel):
    """
    Order Model

    Args:
        order_id: The unique identifier for the order.
        customer_id: The unique identifier for the customer.
        product_id: The unique identifier for the product.
        customer_name: The name of the customer.
        item: The item being ordered.
        quantity: The quantity of the item being ordered.
        price: The price of the item being ordered.
        status: The status of the order.
        created_at: The date and time the order was created.
        updated_at: The date and time the order was last updated.
    """

    order_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str = "CID-001"
    product_id: str = "PID-001"
    customer_name: str
    item: str
    quantity: int = Field(gt=0)
    price: float = Field(gt=0)
    status: str = "pending"
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
