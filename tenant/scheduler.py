from apscheduler.schedulers.background import BackgroundScheduler
from django.utils.timezone import now
from datetime import timedelta
from .models import Orders, OrderItem,uncompleted_order
import logging

logger = logging.getLogger(__name__)

def check_unpaid_orders():
    """
    Check orders that are unpaid for more than 24 hours.
    Store them in uncompleted_order, restock the items, and delete the orders.
    """
    time_limit = now() - timedelta(hours=24)
    unpaid_orders = Orders.objects.filter(payment_made=False, ordered_date__lt=time_limit)

    for order in unpaid_orders:
        for item in order.items.all():
            # Store order details in uncompleted_order
            uncompleted_order.objects.create(
                tenant=str(order.tenant),
                customer=str(order.customer),
                order_id=order.id,
                ordered_date=order.ordered_date,
                payment_made=order.payment_made,
                total_amount=order.total_amount,
                complete=order.complete,
                product=str(item.product.name),
                quantity=item.quantity
            )

            # Restock the product
            product = item.product
            product.stock += item.quantity
            product.save()
            logger.info(f"Restocked {item.quantity} of {product.name}")

        # Delete the unpaid order
        order.delete()
        logger.info(f"Deleted unpaid order {order.id}")

    logger.info("Unpaid orders processed.")
    print("Unpaid orders processed and items restocked.")

def start():
    """
    Start the scheduler and schedule the `check_unpaid_orders` job.
    """
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_unpaid_orders, 'interval', hours=2)  # Run every 2 hours
    scheduler.start()