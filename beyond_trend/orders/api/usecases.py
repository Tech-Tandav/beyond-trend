from django.db import transaction
from rest_framework.exceptions import NotFound, ValidationError

from beyond_trend.core.usecases import BaseUseCase
from beyond_trend.loyalty.models import Customer
from beyond_trend.inventory.models import InventoryLog, Product, Stock

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
        self._loyalty_customer = None
        self._items_to_create = []  # list of (variant, quantity, price)
        self._total_amount = 0

    def is_valid(self):
        loyalty_customer_id = self._data.get("loyalty_customer_id")
        if loyalty_customer_id:
            try:
                self._loyalty_customer = Customer.objects.get(id=loyalty_customer_id)
            except Customer.DoesNotExist:
                raise NotFound("Loyalty customer not found.")

        for item in self._data["items"]:
            variant_id = item["variant_id"]
            quantity = item["quantity"]
            try:
                variant = Product.objects.get(id=variant_id)
            except Product.DoesNotExist:
                raise NotFound(f"Product {variant_id} not found.")

            if variant.selling_price is None:
                raise ValidationError(
                    {"detail": f"Product {variant} has no selling price set."}
                )

            self._total_amount += variant.selling_price * quantity
            self._items_to_create.append((variant, quantity, variant.selling_price))

    @transaction.atomic
    def execute(self):
        self.is_valid()
        return self._factory()

    def _factory(self):
        # Lock + verify stock atomically so two concurrent orders can't oversell.
        for variant, quantity, _ in self._items_to_create:
            try:
                stock = Stock.objects.select_for_update().get(product=variant)
            except Stock.DoesNotExist:
                raise ValidationError(
                    {"detail": f"No stock record for {variant}."}
                )
            if stock.quantity < quantity:
                raise ValidationError(
                    {
                        "detail": (
                            f"Insufficient stock for {variant}. "
                            f"Requested {quantity}, available {stock.quantity}."
                        )
                    }
                )
            stock.quantity -= quantity
            stock.save(update_fields=["quantity"])

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
            InventoryLog.objects.create(
                variant=variant,
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
            items = self._order.items.select_related("variant").all()
            for item in items:
                stock, _ = Stock.objects.select_for_update().get_or_create(
                    product=item.variant
                )
                stock.quantity += item.quantity
                stock.save(update_fields=["quantity"])

                InventoryLog.objects.create(
                    variant=item.variant,
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
