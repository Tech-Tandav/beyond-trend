from django.db import transaction
from rest_framework.exceptions import NotFound, ValidationError

from beyond_trend.core.usecases import BaseUseCase
from beyond_trend.inventory.models import InventoryLog, Product

from beyond_trend.orders.models import Order, OrderItem, PreOrder


# Status transitions Order is allowed to follow.
# Cancelled is reachable from any non-terminal state.
ORDER_STATUS_TRANSITIONS = {
    Order.PENDING: {Order.CONFIRMED, Order.CANCELLED},
    Order.CONFIRMED: {Order.PROCESSING, Order.CANCELLED},
    Order.PROCESSING: {Order.READY, Order.CANCELLED},
    Order.READY: {Order.DELIVERED, Order.CANCELLED},
    Order.DELIVERED: set(),
    Order.CANCELLED: set(),
}


class CreateOrderUseCase(BaseUseCase):
    def __init__(self, data, staff=None):
        self._data = data
        self._staff = staff
        self._items_to_create = []  # list of (product, quantity, price)
        self._total_amount = 0

    def is_valid(self):
        for item in self._data["items"]:
            product_id = item["product_id"]
            quantity = item["quantity"]
            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                raise NotFound(f"Product {product_id} not found.")

            price = item.get("selling_price") or product.selling_price or 0
            self._total_amount += price * quantity
            self._items_to_create.append((product, quantity, price))

    @transaction.atomic
    def execute(self):
        self.is_valid()
        return self._factory()

    def _factory(self):
        # Lock + verify stock atomically so two concurrent orders can't oversell.
        for product, quantity, _ in self._items_to_create:
            locked = Product.objects.select_for_update().get(pk=product.pk)
            if locked.quantity < quantity:
                raise ValidationError(
                    {
                        "detail": (
                            f"Insufficient stock for {locked}. "
                            f"Requested {quantity}, available {locked.quantity}."
                        )
                    }
                )
            locked.quantity -= quantity
            locked.save(update_fields=["quantity"])

        phone = self._data.get("phone", "")

        order = Order.objects.create(
            customer_name=self._data["customer_name"],
            email=self._data["email"],
            phone=phone,
            notes=self._data.get("notes", ""),
            total_amount=self._total_amount,
        )

        for product, quantity, price in self._items_to_create:
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price=price,
            )
            InventoryLog.objects.create(
                product=product,
                action=InventoryLog.CHECK_OUT,
                quantity=-quantity,
                staff=self._staff,
                notes=f"Order {order.id}",
            )

        return order


class UpdateOrderStatusUseCase(BaseUseCase):
    def __init__(self, order, new_status, staff=None):
        self._order = order
        self._new_status = new_status
        self._staff = staff

    def is_valid(self):
        current = self._order.status
        if self._new_status == current:
            raise ValidationError(
                {"detail": f"Order is already in status '{current}'."}
            )
        allowed = ORDER_STATUS_TRANSITIONS.get(current, set())
        if self._new_status not in allowed:
            raise ValidationError(
                {
                    "detail": (
                        f"Cannot transition from '{current}' to "
                        f"'{self._new_status}'."
                    )
                }
            )

    @transaction.atomic
    def execute(self):
        self.is_valid()
        return self._factory()

    def _factory(self):
        previous_status = self._order.status

        # If we're cancelling, restore stock for every line item exactly once.
        if self._new_status == Order.CANCELLED and previous_status != Order.CANCELLED:
            items = self._order.items.select_related("product").all()
            for item in items:
                product = Product.objects.select_for_update().get(pk=item.product_id)
                product.quantity += item.quantity
                product.save(update_fields=["quantity"])

                InventoryLog.objects.create(
                    product=product,
                    action=InventoryLog.CHECK_IN,
                    quantity=item.quantity,
                    staff=self._staff,
                    notes=f"Order {self._order.id} cancelled",
                )

        self._order.status = self._new_status
        self._order.save(update_fields=["status"])
        return self._order


class NotifyPreOrderUseCase(BaseUseCase):
    def __init__(self, pre_order):
        self._pre_order = pre_order

    def is_valid(self):
        if self._pre_order.status == PreOrder.FULFILLED:
            raise ValidationError(
                {"detail": "Cannot notify a fulfilled pre-order."}
            )
        if self._pre_order.status == PreOrder.NOTIFIED:
            raise ValidationError(
                {"detail": "Customer has already been notified."}
            )

    def _factory(self):
        self._pre_order.status = PreOrder.NOTIFIED
        self._pre_order.save(update_fields=["status"])
        return {"detail": "Customer marked as notified."}


class FulfillPreOrderUseCase(BaseUseCase):
    def __init__(self, pre_order):
        self._pre_order = pre_order

    def is_valid(self):
        if self._pre_order.status == PreOrder.FULFILLED:
            raise ValidationError(
                {"detail": "Pre-order is already fulfilled."}
            )

    def _factory(self):
        self._pre_order.status = PreOrder.FULFILLED
        self._pre_order.save(update_fields=["status"])
        return {"detail": "Pre-order marked as fulfilled."}
