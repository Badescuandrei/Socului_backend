from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Category(models.Model):
    slug = models.SlugField(max_length=100, unique=True)
    title = models.CharField(max_length=255, db_index=True)

    def __str__(self):
        return self.title
    
class MenuItem(models.Model):
    title = models.CharField(max_length=255, db_index=True)
    price = models.DecimalField(max_digits=6, decimal_places=2, db_index=True)
    featured = models.BooleanField(default=False, db_index=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)

    def __str__(self):
        return self.title
    
class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    menuitem = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.SmallIntegerField()
    unit_price = models.DecimalField(max_digits=6, decimal_places=2)
    price = models.DecimalField(max_digits=6, decimal_places=2)

    class Meta:
        unique_together = ('menuitem', 'user')

    def __str__(self):
        return f"Cart for {self.user.username} - MenuItem: {self.menuitem.title}"
    
class Order(models.Model):
    STATUS_CHOICES = [
        (0, 'Pending'),
        (1, 'Delivering'),
        (2, 'Delivered'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    delivery_crew = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="delivery_crew_orders",
        null=True,
        blank=True, # Allow no delivery crew assigned initially
        limit_choices_to={'groups__name': "Delivery crew"}
    )
    status = models.SmallIntegerField(choices=STATUS_CHOICES, db_index=True, default=0) # Using choices for status
    total = models.DecimalField(max_digits=8, decimal_places=2) # Increased max_digits for total
    date = models.DateField(db_index=True, auto_now_add=True) # auto_now_add for order date

    def __str__(self):
        return f"Order #{self.pk} by {self.user.username} on {self.date}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items') # Added related_name
    menuitem = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.SmallIntegerField()
    price = models.DecimalField(max_digits=6, decimal_places=2) # Added price to OrderItem

    class Meta:
        unique_together = ('order', 'menuitem')

    def __str__(self):
        return f"OrderItem for Order #{self.order.pk} - MenuItem: {self.menuitem.title}, Quantity: {self.quantity}"