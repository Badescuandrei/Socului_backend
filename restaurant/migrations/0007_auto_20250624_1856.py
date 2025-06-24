# In restaurant/migrations/0007_....py

from django.db import migrations
import uuid # Make sure to import uuid

def generate_unique_order_codes(apps, schema_editor):
    """
    Populates the new order_code field with unique codes for all existing orders.
    """
    Order = apps.get_model('restaurant', 'Order')
    for order in Order.objects.all():
        # Generate a unique code for each order
        while True:
            code = f"SOC-{uuid.uuid4().hex[:6].upper()}"
            # Check against other orders to ensure it's truly unique
            if not Order.objects.filter(order_code=code).exists():
                order.order_code = code
                break
        order.save()


class Migration(migrations.Migration):

    dependencies = [
        ('restaurant', '0006_storelocation_remove_order_date_order_created_at_and_more'), # Make sure this matches the previous migration filename!
    ]

    operations = [
        # This is where we tell Django to run our custom Python function
        migrations.RunPython(generate_unique_order_codes),
    ]