from django.db import models
import uuid
from django.contrib.auth.models import User
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.validators import RegexValidator

# Create your models here.
class Category(models.Model):
    slug = models.SlugField(max_length=100, unique=True)
    title = models.CharField(max_length=255, db_index=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)

    def __str__(self):
        return self.title
    
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    phone_number = models.CharField(
        max_length=20, 
        blank=True, 
        null=True, 
        db_index=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        ],
        help_text="Enter phone number in international format"
    )
    store_location = models.ForeignKey(
        'StoreLocation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="The home store for a delivery crew member."
    )

    def __str__(self):
        return f"Profile for {self.user.username} - Phone: {self.phone_number or 'N/A'}"

    @property
    def formatted_phone(self):
        """Return formatted phone number."""
        if self.phone_number:
            # Simple formatting logic
            if self.phone_number.startswith('+'):
                return self.phone_number
            return f"+{self.phone_number}"
        return None

# Add this for data integrity
@receiver(post_delete, sender=User)
def delete_user_profile(sender, instance, **kwargs):
    """
    Clean up orphaned profiles if needed (though CASCADE should handle this).
    """
    try:
        instance.userprofile.delete()
    except UserProfile.DoesNotExist:
        pass

class MenuItem(models.Model):
    title = models.CharField(max_length=255, db_index=True)
    price = models.DecimalField(max_digits=6, decimal_places=2, db_index=True)
    featured = models.BooleanField(default=False, db_index=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    image = models.ImageField(upload_to='menu_items/', blank=True, null=True)

    # New Fields from our discussion
    is_standalone_item = models.BooleanField(
        default=True, 
        help_text="Can this item be purchased on its own from the menu?"
    )
    is_available = models.BooleanField(
        default=True, 
        db_index=True, 
        help_text="Is this item available for purchase or as an option?"
    )
    allergens = models.TextField(blank=True, null=True)
    ingredient_list = models.TextField(blank=True, null=True)
    nutritional_info = models.JSONField(
        blank=True, 
        null=True, 
        help_text="e.g., {'calories': 500, 'protein_g': 25}"
    )

    def __str__(self):
        return self.title

class OptionGroup(models.Model):
    name = models.CharField(max_length=100, help_text="e.g., 'Sides', 'Choose your sauces'")
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name='option_groups')
    min_selection = models.PositiveIntegerField(default=1)
    max_selection = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"Option Group '{self.name}' for {self.menu_item.title}"

class OptionChoice(models.Model):
    group = models.ForeignKey(OptionGroup, on_delete=models.CASCADE, related_name='choices')
    item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, help_text="The MenuItem being offered as a choice.")
    price_adjustment = models.DecimalField(
        max_digits=6, 
        decimal_places=2, 
        default=0.00, 
        help_text="Price difference. Can be positive (upcharge) or negative (discount)."
    )
    is_default = models.BooleanField(default=False, help_text="Is this option selected by default?")

    def __str__(self):
        return f"Choice '{self.item.title}' in group '{self.group.name}'"
    
class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    menuitem = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.SmallIntegerField()
    unit_price = models.DecimalField(max_digits=6, decimal_places=2)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    selected_options = models.ManyToManyField('OptionChoice', blank=True)

    def __str__(self):
        return f"Cart for {self.user.username} - MenuItem: {self.menuitem.title}"
    
class Order(models.Model):
    STATUS_CHOICES = [
        (0, 'Pending'),
        (1, 'Delivering'),
        (2, 'Delivered'),
    ]

    # New unique, human-readable identifier
    order_code = models.CharField(max_length=12, unique=True, editable=False, db_index=True)

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    delivery_crew = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="delivery_crew_orders",
        null=True,
        blank=True,
        limit_choices_to={'groups__name': "Delivery crew"}
    )
    status = models.SmallIntegerField(choices=STATUS_CHOICES, db_index=True, default=0)
    total = models.DecimalField(max_digits=8, decimal_places=2)
    
    # Replaced 'date' with a precise timestamp
    created_at = models.DateTimeField(db_index=True, auto_now_add=True)
    
    customer_name = models.CharField(max_length=255, blank=True)
    customer_phone = models.CharField(max_length=20, blank=True, db_index=True)
    delivery_address = models.TextField(blank=True) # Will store a snapshot of the address text
    is_voice_order = models.BooleanField(default=False, db_index=True)

    # New links to our new models
    store_location = models.ForeignKey(
        'StoreLocation',
        on_delete=models.PROTECT,
        related_name='orders',
        null=True, # Nullable to support old or phone orders
        blank=True
    )
    delivery_address_link = models.ForeignKey(
        'UserAddress',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def save(self, *args, **kwargs):
        """Generate a unique order code on creation."""
        if not self.order_code:
            # Generate a code like "SOC-A4E8B1"
            while True:
                code = f"SOC-{uuid.uuid4().hex[:6].upper()}"
                if not Order.objects.filter(order_code=code).exists():
                    self.order_code = code
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        if self.is_voice_order:
            user_identifier = f"{self.customer_name or 'Unknown'} ({self.customer_phone or 'N/A'}) [Voice]"
        elif self.user:
            user_identifier = f"{self.user.username} [App]"
        else:
             user_identifier = "Unknown/System"
        
        # Use the new fields for a more informative string representation
        return f"Order {self.order_code} by {user_identifier} on {self.created_at.strftime('%Y-%m-%d')}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items') # Added related_name
    menuitem = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.SmallIntegerField()
    price = models.DecimalField(max_digits=6, decimal_places=2) # Added price to OrderItem
    selected_options = models.ManyToManyField('OptionChoice', blank=True)

    def __str__(self):
        return f"OrderItem for Order #{self.order.pk} - MenuItem: {self.menuitem.title}, Quantity: {self.quantity}"
    
class StoreLocation(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField()
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    delivery_radius_km = models.DecimalField(
        max_digits=4, 
        decimal_places=1, 
        default=5.0,
        help_text="The delivery radius in kilometers from this location."
    )
    is_active = models.BooleanField(
        default=True, 
        help_text="Is this location currently accepting online orders?"
    )

    def __str__(self):
        return self.name
    
class UserAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    nickname = models.CharField(max_length=100, help_text="e.g., Home, Work")
    street_address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.nickname} ({self.street_address}) for {self.user.username}"

    class Meta:
        # Ensures a user cannot have two addresses with the same nickname
        unique_together = ('user', 'nickname')