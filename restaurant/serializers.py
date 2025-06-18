from rest_framework import serializers
from .models import Category, MenuItem, Cart, Order, OrderItem, OptionGroup, OptionChoice
from django.contrib.auth.models import User, Group

class CategorySerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Category
        # --- CORRECTED: Added 'image_url' to fields ---
        fields = ['id', 'slug', 'title', 'image_url']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None

class MenuItemSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), source='category', write_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = MenuItem
        fields = [
            'id', 'title', 'price', 'featured', 'category', 'category_id', 
            'image_url', 'is_standalone_item', 'is_available', 
            'allergens', 'ingredient_list', 'nutritional_info'
        ]

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None

class OptionChoiceSerializer(serializers.ModelSerializer):
    item_title = serializers.CharField(source='item.title', read_only=True)
    is_available = serializers.BooleanField(source='item.is_available', read_only=True)

    class Meta:
        model = OptionChoice
        fields = ['id', 'item_title', 'price_adjustment', 'is_default', 'is_available']


class OptionGroupSerializer(serializers.ModelSerializer):
    choices = OptionChoiceSerializer(many=True, read_only=True)

    class Meta:
        model = OptionGroup
        fields = ['name', 'min_selection', 'max_selection', 'choices']


class MenuItemDetailSerializer(MenuItemSerializer):
    option_groups = OptionGroupSerializer(many=True, read_only=True)

    class Meta(MenuItemSerializer.Meta):
        fields = MenuItemSerializer.Meta.fields + ['option_groups']


class CartItemSerializer(serializers.ModelSerializer):
    menuitem = MenuItemSerializer(read_only=True)
    menuitem_id = serializers.PrimaryKeyRelatedField(queryset=MenuItem.objects.all(), source='menuitem', write_only=True)
    price = serializers.DecimalField(max_digits=6, decimal_places=2, read_only=True)
    selected_options = serializers.PrimaryKeyRelatedField(
        queryset=OptionChoice.objects.all(),
        many=True,
        required=False
    )

    class Meta:
        model = Cart
        fields = ['id', 'menuitem', 'menuitem_id', 'quantity', 'unit_price', 'price', 'selected_options']
        read_only_fields = ['unit_price', 'price']

class CartSerializer(serializers.ModelSerializer):
    cartitem_set = CartItemSerializer(many=True, read_only=True, source='cart_set') # Use related_name if you set it in model

    class Meta:
        model = Cart
        fields = ['id', 'user', 'cartitem_set'] # Include 'id'

class OrderItemSerializer(serializers.ModelSerializer):
    menuitem = MenuItemSerializer(read_only=True)
    menuitem_id = serializers.PrimaryKeyRelatedField(queryset=MenuItem.objects.all(), source='menuitem', write_only=True)
    selected_options = OptionChoiceSerializer(many=True, read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'order', 'menuitem', 'menuitem_id', 'quantity', 'price', 'selected_options']

class OrderSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all()) # Or UserSerializer if you create one
    delivery_crew = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(groups__name='Delivery crew'), allow_null=True, required=False) # Filter Delivery Crew users
    order_items = OrderItemSerializer(many=True, read_only=True) # Use related_name
    customer_name = serializers.CharField(read_only=True, allow_blank=True)
    customer_phone = serializers.CharField(read_only=True, allow_blank=True)
    delivery_address = serializers.CharField(read_only=True, allow_blank=True)
    is_voice_order = serializers.BooleanField(read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'user', 'delivery_crew', 'status', 'total', 'order_items', 'is_voice_order', 'date','customer_name', 'customer_phone', 'delivery_address',]

class DirectOrderItemInputSerializer(serializers.Serializer):
    """Serializer for validating items within a direct order request."""
    menuitem_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1)

    def validate_menuitem_id(self, value):
        """Check if the menu item exists."""
        if not MenuItem.objects.filter(pk=value).exists():
            raise serializers.ValidationError(f"MenuItem with id {value} does not exist.")
        return value

class DirectOrderInputSerializer(serializers.Serializer):
    """Serializer for validating the entire direct order request payload."""
    items = DirectOrderItemInputSerializer(many=True, required=True, allow_empty=False)
    customer_name = serializers.CharField(max_length=255, required=True, allow_blank=False)
    customer_phone = serializers.CharField(max_length=20, required=True, allow_blank=False)
    delivery_address = serializers.CharField(required=True, allow_blank=False)

class UserSerializer(serializers.ModelSerializer): # Basic User Serializer for registration/display
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name'] # Include 'id'

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'name'] # We'll expose 'id' and 'name' for groups