# restaurant/admin.py
from django.contrib import admin
from django.utils.html import format_html # Import format_html
from .models import Cart, Category, MenuItem, Order, OrderItem, UserProfile # Import OrderItem and UserProfile

# Register your models here.

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

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'category', 'featured', 'image_tag') # Add image_tag
    list_filter = ('category', 'featured')
    search_fields = ('title', 'category__title')

    # Method to display image thumbnail in admin list
    def image_tag(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;" />', obj.image.url)
        return "-" # Display '-' if no image
    image_tag.short_description = 'Image' # Column header

# Basic registration for other models
admin.site.register(Cart)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(UserProfile) # Register UserProfile