from django.contrib import admin
from restaurant.models import Cart, Category, MenuItem, Order

# Register your models here.
admin.site.register(Category)
admin.site.register(MenuItem)
admin.site.register(Cart)
admin.site.register(Order)