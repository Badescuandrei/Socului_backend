from django.db import models
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
        blank=True, # Allow no delivery crew assigned initially
        limit_choices_to={'groups__name': "Delivery crew"}
    )
    status = models.SmallIntegerField(choices=STATUS_CHOICES, db_index=True, default=0) # Using choices for status
    total = models.DecimalField(max_digits=8, decimal_places=2) # Increased max_digits for total
    date = models.DateField(db_index=True, auto_now_add=True) # auto_now_add for order date
    customer_name = models.CharField(max_length=255, blank=True)
    customer_phone = models.CharField(max_length=20, blank=True, db_index=True)
    delivery_address = models.TextField(blank=True)
    is_voice_order = models.BooleanField(default=False, db_index=True)

    def __str__(self):
        # --- MODIFIED __str__ based on flag ---
        if self.is_voice_order:
            user_identifier = f"{self.customer_name or 'Unknown'} ({self.customer_phone or 'N/A'}) [Voice]"
        elif self.user:
            user_identifier = f"{self.user.username} [App]"
        else:
             user_identifier = "Unknown/System" # Should ideally not happen if user was mandatory before

        return f"Order #{self.pk} by {user_identifier} on {self.date}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items') # Added related_name
    menuitem = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.SmallIntegerField()
    price = models.DecimalField(max_digits=6, decimal_places=2) # Added price to OrderItem
    selected_options = models.ManyToManyField('OptionChoice', blank=True)

    def __str__(self):
        return f"OrderItem for Order #{self.order.pk} - MenuItem: {self.menuitem.title}, Quantity: {self.quantity}"