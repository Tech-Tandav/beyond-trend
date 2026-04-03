from django.db import transaction
from rest_framework.exceptions import NotFound

from beyond_trend.core.usecases import BaseUseCase
from beyond_trend.inventory.models import ProductVariant
from beyond_trend.loyalty.models import Customer

from ..models import Order, OrderItem, PreOrder


class CreateOrderUseCase(BaseUseCase):
    def __init__(self, data):
        self._data = data
        self._loyalty_customer = None
        self._items_to_create = []
        self._total_amount = 0

    def is_valid(self):
        loyalty_customer_id = self._data.get("loyalty_customer_id")
        if loyalty_customer_id:
            try:
                self._loyalty_customer = Customer.objects.get(id=loyalty_customer_id)
            except Customer.DoesNotExist:
                raise NotFound("Loyalty customer not found.")

        for item in self._data["items"]:
            try:
                variant = ProductVariant.objects.get(id=item["variant_id"])
            except ProductVariant.DoesNotExist:
                raise NotFound(f"Variant {item['variant_id']} not found.")
            price = variant.selling_price
            self._total_amount += price * item["quantity"]
            self._items_to_create.append((variant, item["quantity"], price))

    @transaction.atomic
    def execute(self):
        self.is_valid()
        return self._factory()

    def _factory(self):
        order = Order.objects.create(
            customer_name=self._data["customer_name"],
            email=self._data["email"],
            phone=self._data.get("phone", ""),
            notes=self._data.get("notes", ""),
            total_amount=self._total_amount,
            loyalty_customer=self._loyalty_customer,
        )

        for variant, quantity, price in self._items_to_create:
            OrderItem.objects.create(
                order=order,
                variant=variant,
                quantity=quantity,
                price=price,
            )

        return order


class UpdateOrderStatusUseCase(BaseUseCase):
    def __init__(self, order, new_status):
        self._order = order
        self._new_status = new_status

    def _factory(self):
        self._order.status = self._new_status
        self._order.save(update_fields=["status"])
        return self._order


class NotifyPreOrderUseCase(BaseUseCase):
    def __init__(self, pre_order):
        self._pre_order = pre_order

    def _factory(self):
        self._pre_order.status = PreOrder.NOTIFIED
        self._pre_order.save(update_fields=["status"])
        return {"detail": "Customer marked as notified."}


class FulfillPreOrderUseCase(BaseUseCase):
    def __init__(self, pre_order):
        self._pre_order = pre_order

    def _factory(self):
        self._pre_order.status = PreOrder.FULFILLED
        self._pre_order.save(update_fields=["status"])
        return {"detail": "Pre-order marked as fulfilled."}
