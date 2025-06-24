# restaurant/admin.py
from django.contrib import admin
from django.utils.html import format_html # Import format_html
from .models import Cart, Category, MenuItem, Order, OrderItem, StoreLocation, UserAddress, UserProfile, OptionGroup, OptionChoice # Import new models

# Register your models here.

class OptionChoiceInline(admin.TabularInline):
    model = OptionChoice
    extra = 1 # Show one extra blank form by default

class OptionGroupInline(admin.TabularInline):
    model = OptionGroup
    extra = 1

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'image_tag') # Add image_tag
    search_fields = ('title', 'slug')
    prepopulated_fields = {'slug': ('title',)} # Auto-populate slug

    # Method to display image thumbnail in admin list
    def image_tag(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;" />', obj.image.url)
        return "-" # Display '-' if no image
    image_tag.short_description = 'Image' # Column header

# Unregister the original MenuItemAdmin to re-register it with inlines
# admin.site.unregister(MenuItem) 

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'category', 'featured', 'image_tag', 'is_standalone_item', 'is_available') # Add new fields
    list_filter = ('category', 'featured', 'is_available', 'is_standalone_item')
    search_fields = ('title', 'category__title')
    inlines = [OptionGroupInline] # Add the OptionGroup inline

    # Method to display image thumbnail in admin list
    def image_tag(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;" />', obj.image.url)
        return "-" # Display '-' if no image
    image_tag.short_description = 'Image' # Column header

@admin.register(OptionGroup)
class OptionGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'menu_item', 'min_selection', 'max_selection')
    list_filter = ('menu_item',)
    search_fields = ('name', 'menu_item__title')
    inlines = [OptionChoiceInline]

@admin.register(StoreLocation)
class StoreLocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'delivery_radius_km', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'address')
    # Make coordinates read-only as they should be set programmatically or by an admin who knows what they're doing
    readonly_fields = ('latitude', 'longitude')

@admin.register(UserAddress)
class UserAddressAdmin(admin.ModelAdmin):
    list_display = ('nickname', 'user', 'street_address', 'city', 'is_default')
    list_filter = ('is_default', 'city')
    search_fields = ('user__username', 'nickname', 'street_address')
    # Coordinates are set by the system, so they should be read-only
    readonly_fields = ('latitude', 'longitude')

# Basic registration for other models
admin.site.register(Cart)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(UserProfile) # Register UserProfile
admin.site.register(OptionChoice)