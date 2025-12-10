from .models import Customer

def update_customer_after_completed_order(customer: Customer, order_total: float):
    """
    Call this from orders app when an order is COMPLETED.
    It updates total_spent, order_count and checks VIP promotion
    """
    customer.total_spent += order_total
    customer.orders_count += 1
    customer.save()
    customer.consider_vip_promotion()