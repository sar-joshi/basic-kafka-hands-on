from models.order import Order


class TestOrderModel:
    def test_order_serialization(self, sample_order):
        """
        Test that the order model can be serialized to JSON.
        """
        json_str = sample_order.model_dump_json()

        assert json_str is not None
        assert sample_order.customer_name in json_str
        assert sample_order.item in json_str
        assert str(sample_order.quantity) in json_str
        assert str(sample_order.price) in json_str
        assert sample_order.status in json_str
        assert sample_order.created_at in json_str
        assert sample_order.updated_at in json_str
        assert isinstance(json_str, str)
        assert isinstance(Order.model_validate_json(json_str), Order)
