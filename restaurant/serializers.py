from rest_framework import serializers
from .models import Category, MenuItem, Cart, Order, OrderItem
from django.contrib.auth.models import User

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'slug', 'title'] # Include 'id' for API responses

class MenuItemSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True) # Nested serializer for category
    category_id = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), source='category', write_only=True) # For writable API

    class Meta:
        model = MenuItem
        fields = ['id', 'title', 'price', 'featured', 'category', 'category_id'] # Include 'id'

class CartItemSerializer(serializers.ModelSerializer):
    menuitem = MenuItemSerializer(read_only=True)
    menuitem_id = serializers.PrimaryKeyRelatedField(queryset=MenuItem.objects.all(), source='menuitem', write_only=True)
    price = serializers.DecimalField(max_digits=6, decimal_places=2, read_only=True) # Make price read-only, calculated in backend

    class Meta:
        model = Cart
        fields = ['id', 'menuitem', 'menuitem_id', 'quantity', 'unit_price', 'price'] # Include 'id'
        read_only_fields = ['unit_price', 'price'] # unit_price will be set in view

class CartSerializer(serializers.ModelSerializer):
    cartitem_set = CartItemSerializer(many=True, read_only=True, source='cart_set') # Use related_name if you set it in model

    class Meta:
        model = Cart
        fields = ['id', 'user', 'cartitem_set'] # Include 'id'

class OrderItemSerializer(serializers.ModelSerializer):
    menuitem = MenuItemSerializer(read_only=True)
    menuitem_id = serializers.PrimaryKeyRelatedField(queryset=MenuItem.objects.all(), source='menuitem', write_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'order', 'menuitem', 'menuitem_id', 'quantity', 'price'] # Include 'id'

class OrderSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all()) # Or UserSerializer if you create one
    delivery_crew = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(groups__name='Delivery crew'), allow_null=True, required=False) # Filter Delivery Crew users
    order_items = OrderItemSerializer(many=True, read_only=True) # Use related_name

    class Meta:
        model = Order
        fields = ['id', 'user', 'delivery_crew', 'status', 'total', 'date', 'order_items'] # Include 'id'


class UserSerializer(serializers.ModelSerializer): # Basic User Serializer for registration/display
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name'] # Include 'id'