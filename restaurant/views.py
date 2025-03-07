from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Cart, Category, MenuItem, Order, OrderItem
from .serializers import CartItemSerializer, CategorySerializer, MenuItemSerializer, OrderSerializer
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.decorators import api_view, permission_classes, action
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User

class CategoryViewSet(viewsets.ViewSet):
    """
    ViewSet for viewing and editing Categories.
    """
    permission_classes_by_action = {
        'list': [AllowAny],
        'retrieve': [AllowAny],
        'create': [IsAuthenticated, IsAdminUser], # Manager role (or admin)
        'update': [IsAuthenticated, IsAdminUser], # Manager role (or admin)
        'partial_update': [IsAuthenticated, IsAdminUser], # Manager role (or admin)
        'destroy': [IsAuthenticated, IsAdminUser], # Manager role (or admin)
    }

    def get_permissions(self):
        try:
            # return permission_classes depending on `action`
            return [permission() for permission in self.permission_classes_by_action[self.action]]
        except KeyError:
            # action is not set return default permission_classes
            return [permission() for permission in self.permission_classes]

    def list(self, request):
        """
        List all categories. Publicly accessible.
        """
        queryset = Category.objects.all()
        serializer = CategorySerializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """
        Retrieve a specific category. Publicly accessible.
        """
        queryset = Category.objects.all()
        category = get_object_or_404(queryset, pk=pk)
        serializer = CategorySerializer(category)
        return Response(serializer.data)

    def create(self, request):
        """
        Create a new category. Managers only.
        """
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        """
        Update an existing category. Managers only.
        """
        queryset = Category.objects.all()
        category = get_object_or_404(queryset, pk=pk)
        serializer = CategorySerializer(category, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, pk=None):
        """
        Partially update an existing category. Managers only.
        """
        queryset = Category.objects.all()
        category = get_object_or_404(queryset, pk=pk)
        serializer = CategorySerializer(category, data=request.data, partial=True) # partial=True for partial updates
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        """
        Delete a category. Managers only.
        """
        queryset = Category.objects.all()
        category = get_object_or_404(queryset, pk=pk)
        category.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MenuItemViewSet(viewsets.ViewSet):
    """
    ViewSet for viewing and editing MenuItems.
    """
    permission_classes_by_action = {
        'list': [AllowAny],
        'retrieve': [AllowAny],
        'create': [IsAuthenticated, IsAdminUser], # Manager role (or admin)
        'update': [IsAuthenticated, IsAdminUser], # Manager role (or admin)
        'partial_update': [IsAuthenticated, IsAdminUser], # Manager role (or admin)
        'destroy': [IsAuthenticated, IsAdminUser], # Manager role (or admin)
    }

    def get_permissions(self):
        try:
            # return permission_classes depending on `action`
            return [permission() for permission in self.permission_classes_by_action[self.action]]
        except KeyError:
            # action is not set return default permission_classes
            return [permission() for permission in self.permission_classes]

    def list(self, request):
        """
        List all menu items, with optional filtering and pagination. Publicly accessible.
        """
        queryset = MenuItem.objects.select_related('category').all() # Optimize with select_related
        category_name = request.query_params.get('category') # Filter by category slug
        to_price = request.query_params.get('to_price') # Filter by price (less than or equal to)
        search = request.query_params.get('search') # Search by title (icontains)
        ordering = request.query_params.get('ordering') # Ordering by fields

        if category_name:
            queryset = queryset.filter(category__slug=category_name)
        if to_price:
            queryset = queryset.filter(price__lte=to_price)
        if search:
            queryset = queryset.filter(title__icontains=search)
        if ordering:
            queryset = queryset.order_by(ordering)

        serializer = MenuItemSerializer(queryset, many=True) # No pagination for now, add later if needed
        return Response(serializer.data)


    def retrieve(self, request, pk=None):
        """
        Retrieve a specific menu item. Publicly accessible.
        """
        queryset = MenuItem.objects.select_related('category').all() # Optimize with select_related
        menuitem = get_object_or_404(queryset, pk=pk)
        serializer = MenuItemSerializer(menuitem)
        return Response(serializer.data)

    def create(self, request):
        """
        Create a new menu item. Managers only.
        """
        serializer = MenuItemSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        """
        Update an existing menu item. Managers only.
        """
        queryset = MenuItem.objects.all()
        menuitem = get_object_or_404(queryset, pk=pk)
        serializer = MenuItemSerializer(menuitem, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, pk=None):
        """
        Partially update an existing menu item. Managers only.
        """
        queryset = MenuItem.objects.all()
        menuitem = get_object_or_404(queryset, pk=pk)
        serializer = MenuItemSerializer(menuitem, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        """
        Delete a menu item. Managers only.
        """
        queryset = MenuItem.objects.all()
        menuitem = get_object_or_404(queryset, pk=pk)
        menuitem.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
class CartViewSet(viewsets.ViewSet):
    """
    ViewSet for managing the current user's Cart.
    """
    permission_classes = [IsAuthenticated] # All cart actions require authentication

    def list(self, request):
        """
        Retrieve the current user's cart items.
        """
        cart_items = Cart.objects.filter(user=request.user) # Get cart items for current user
        serializer = CartItemSerializer(cart_items, many=True)
        return Response(serializer.data)

    def create(self, request):
        """
        Add a menu item to the current user's cart.
        Expects menuitem_id and quantity in request data.
        """
        menuitem_id = request.data.get('menuitem_id')
        quantity = request.data.get('quantity')

        if not menuitem_id or not quantity:
            return Response({"error": "Both menuitem_id and quantity are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            menuitem = MenuItem.objects.get(pk=menuitem_id)
        except MenuItem.DoesNotExist:
            return Response({"error": "MenuItem not found."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            quantity = int(quantity)
            if quantity <= 0:
                return Response({"error": "Quantity must be a positive integer."}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({"error": "Invalid quantity."}, status=status.HTTP_400_BAD_REQUEST)

        # Get or create cart item for the user and menuitem
        cart_item, created = Cart.objects.get_or_create(
            user=request.user,
            menuitem=menuitem,
            defaults={'quantity': 0, 'unit_price': menuitem.price, 'price': 0} # Initialize if creating
        )

        # Update quantity and price
        cart_item.quantity += quantity
        cart_item.price = cart_item.unit_price * cart_item.quantity
        cart_item.save()

        serializer = CartItemSerializer(cart_item)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK) # 201 if created, 200 if updated

    def update(self, request, pk=None): # pk is not really used for cart update in this design, but included for ViewSet consistency
        """
        Update a cart item (e.g., change quantity).
        Expects quantity in request data. Cart item is identified by menuitem_id in URL or body.
        """
        menuitem_id = request.data.get('menuitem_id') # Or get pk from URL if you prefer
        quantity = request.data.get('quantity')

        if not menuitem_id or not quantity:
            return Response({"error": "Both menuitem_id and quantity are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            menuitem = MenuItem.objects.get(pk=menuitem_id)
        except MenuItem.DoesNotExist:
            return Response({"error": "MenuItem not found."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            quantity = int(quantity)
            if quantity <= 0:
                return Response({"error": "Quantity must be a positive integer."}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({"error": "Invalid quantity."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            cart_item = Cart.objects.get(user=request.user, menuitem=menuitem)
        except Cart.DoesNotExist:
            return Response({"error": "Cart item not found in your cart."}, status=status.HTTP_404_NOT_FOUND)

        # Update quantity and price
        cart_item.quantity = quantity
        cart_item.price = cart_item.unit_price * cart_item.quantity
        cart_item.save()

        serializer = CartItemSerializer(cart_item)
        return Response(serializer.data)

    def destroy(self, request, pk=None): # pk here could be menuitem_id to remove from cart
        """
        Remove a menu item from the current user's cart.
        Expects menuitem_id in URL or request data (pk here could be menuitem_id).
        """
        menuitem_id_to_remove = request.data.get('menuitem_id') or pk # Try to get from body or URL pk

        if not menuitem_id_to_remove:
            return Response({"error": "menuitem_id is required to remove from cart."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            menuitem_to_remove = MenuItem.objects.get(pk=menuitem_id_to_remove)
        except MenuItem.DoesNotExist:
            return Response({"error": "MenuItem not found."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            cart_item = Cart.objects.get(user=request.user, menuitem=menuitem_to_remove)
            cart_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Cart.DoesNotExist:
            return Response({"error": "Cart item not found in your cart."}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['delete']) # Custom action for flushing cart
    def flush(self, request):
        """
        Flush (empty) the current user's cart.
        """
        Cart.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
from rest_framework.decorators import action

class OrderViewSet(viewsets.ViewSet):
    """
    ViewSet for managing Orders.
    Customers can place orders and view their order history.
    Managers can list, view, filter, assign delivery crew, and update order status.
    Delivery crew can view assigned orders and update order status to delivered.
    """
    permission_classes_by_action = {
        'list': [IsAuthenticated], # For all authenticated users (customers, managers, delivery crew) - will refine further
        'retrieve': [IsAuthenticated], # For all authenticated users - will refine further
        'create': [IsAuthenticated], # Customers placing orders
        'update': [IsAuthenticated, IsAdminUser], # Managers updating order details (initially admin only for simplicity)
        'partial_update': [IsAuthenticated, IsAdminUser], # Managers partially updating orders
        'destroy': [IsAuthenticated, IsAdminUser], # Managers deleting orders (admin only initially)
        'assign_delivery_crew': [IsAuthenticated, IsAdminUser], # Managers assigning delivery crew
        'update_order_status_to_delivered': [IsAuthenticated], # Delivery crew updating status
    }

    def get_permissions(self):
        try:
            return [permission() for permission in self.permission_classes_by_action[self.action]]
        except KeyError:
            return [permission() for permission in self.permission_classes]

    def list(self, request):
        """
        List orders based on user role.
        Customers: See their own order history.
        Managers/Delivery Crew: See all orders (with filtering later).
        """
        if request.user.groups.filter(name='Manager').exists() or request.user.is_superuser: # Managers and Admin can see all orders for now
            queryset = Order.objects.all()
            serializer = OrderSerializer(queryset, many=True)
            return Response(serializer.data)
        elif request.user.groups.filter(name='Delivery crew').exists(): # Delivery crew sees assigned orders (to be implemented filtering later)
            queryset = Order.objects.filter(delivery_crew=request.user) # For now, just delivery crew user's orders
            serializer = OrderSerializer(queryset, many=True)
            return Response(serializer.data)
        else: # Customers see their own orders
            queryset = Order.objects.filter(user=request.user)
            serializer = OrderSerializer(queryset, many=True)
            return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """
        Retrieve a specific order. Access based on user role and order ownership.
        """
        queryset = Order.objects.all()
        order = get_object_or_404(queryset, pk=pk)

        if request.user == order.user or request.user.groups.filter(name__in=['Manager', 'Delivery crew']).exists() or request.user.is_superuser: # Owner, Manager, Delivery crew can view
            serializer = OrderSerializer(order)
            return Response(serializer.data)
        else:
            return Response({"error": "You do not have permission to view this order."}, status=status.HTTP_403_FORBIDDEN)


    def create(self, request):
        """
        Place a new order (customer action - from cart).
        """
        cart_items = Cart.objects.filter(user=request.user)
        if not cart_items.exists():
            return Response({"error": "Your cart is empty."}, status=status.HTTP_400_BAD_REQUEST)

        order_total = sum(item.price for item in cart_items) # Calculate total order amount

        order = Order.objects.create(user=request.user, total=order_total, status=0) # Create Order object, status = Pending

        order_items_list = [] # Prepare to create OrderItems
        for cart_item in cart_items:
            order_item = OrderItem.objects.create(
                order=order,
                menuitem=cart_item.menuitem,
                quantity=cart_item.quantity,
                price=cart_item.price # Use price from cart at time of order
            )
            order_items_list.append(order_item)

        Cart.objects.filter(user=request.user).delete() # Empty the cart after order placed

        serializer = OrderSerializer(order) # Serialize the created Order
        return Response(serializer.data, status=status.HTTP_201_CREATED)


    def update(self, request, pk=None): # For managers to update order details (initially admin only)
        """
        Update an existing order (Manager action - initially admin only).
        """
        queryset = Order.objects.all()
        order = get_object_or_404(queryset, pk=pk)
        serializer = OrderSerializer(order, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def partial_update(self, request, pk=None): # For managers to partially update orders
        queryset = Order.objects.all()
        order = get_object_or_404(queryset, pk=pk)
        serializer = OrderSerializer(order, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def destroy(self, request, pk=None): # For managers to delete orders (initially admin only)
        queryset = Order.objects.all()
        order = get_object_or_404(queryset, pk=pk)
        order.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


    @action(detail=True, methods=['put']) # Custom action to assign delivery crew to an order (Manager only)
    def assign_delivery_crew(self, request, pk=None):
        """
        Assign delivery crew to an order (Manager action).
        Expects delivery_crew_id in request data.
        """
        if not request.user.groups.filter(name='Manager').exists() and not request.user.is_superuser: # Only managers can assign
            return Response({"error": "Only managers can assign delivery crew."}, status=status.HTTP_403_FORBIDDEN)

        delivery_crew_id = request.data.get('delivery_crew_id')
        if not delivery_crew_id:
            return Response({"error": "delivery_crew_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            delivery_crew_user = User.objects.filter(groups__name='Delivery crew').get(pk=delivery_crew_id) # Ensure user is in Delivery crew group
        except User.DoesNotExist:
            return Response({"error": "Delivery crew user not found."}, status=status.HTTP_400_BAD_REQUEST)

        order = self.get_object() # Helper to get Order instance based on pk (from ViewSet)
        order.delivery_crew = delivery_crew_user
        order.save()
        serializer = OrderSerializer(order)
        return Response(serializer.data)


    @action(detail=True, methods=['put']) # Custom action for delivery crew to update order status to delivered
    def update_order_status_to_delivered(self, request, pk=None):
        """
        Delivery crew updates order status to 'Delivered'.
        """
        if not request.user.groups.filter(name='Delivery crew').exists(): # Only delivery crew can update status
            return Response({"error": "Only delivery crew can update order status."}, status=status.HTTP_403_FORBIDDEN)

        order = self.get_object() # Helper to get Order instance
        if order.delivery_crew != request.user: # Ensure delivery crew is assigned to this order
            return Response({"error": "You are not assigned to this order."}, status=status.HTTP_403_FORBIDDEN)

        order.status = 2 # Delivered status code (see Order model STATUS_CHOICES)
        order.save()
        serializer = OrderSerializer(order)
        return Response(serializer.data)

    def get_object(self): # Helper method to get Order instance for detail actions (assign_delivery_crew, update_order_status_to_delivered)
        queryset = self.queryset
        if queryset is None:
            queryset = self.filter_queryset(self.get_queryset()) # Vertex API fix
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        obj = get_object_or_404(queryset, **filter_kwargs)
        self.check_object_permissions(self.request, obj) # Optional permission check for object level
        return obj