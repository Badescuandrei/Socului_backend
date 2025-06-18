from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Cart, Category, MenuItem, Order, OrderItem, OptionChoice
from .serializers import (
    CartItemSerializer, CategorySerializer, DirectOrderInputSerializer, 
    GroupSerializer, MenuItemSerializer, MenuItemDetailSerializer, OrderSerializer
)
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.decorators import api_view, permission_classes, action
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User, Group
from .permissions import IsManager, IsDeliveryCrew # Import custom permission classes
from django.contrib.auth.models import Group
from decimal import Decimal
from django.db import transaction
from rest_framework_api_key.permissions import HasAPIKey

# Create groups if they don't exist (run only once on app startup)
def create_groups():
    Group.objects.get_or_create(name='Manager')
    Group.objects.get_or_create(name='Delivery crew')

create_groups() # Call the function to ensure groups are created on app startup

class CategoryViewSet(viewsets.ViewSet):
    """
    ViewSet for viewing and editing Categories.
    """
    permission_classes_by_action = {
        'list': [AllowAny],
        'retrieve': [AllowAny],
        'create': [IsAuthenticated, IsManager], # Use IsManager instead of IsAdminUser
        'update': [IsAuthenticated, IsManager], # Use IsManager instead of IsAdminUser
        'partial_update': [IsAuthenticated, IsManager], # Use IsManager instead of IsAdminUser
        'destroy': [IsAuthenticated, IsManager], # Use IsManager instead of IsAdminUser
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
        serializer = CategorySerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """
        Retrieve a specific category. Publicly accessible.
        """
        queryset = Category.objects.all()
        category = get_object_or_404(queryset, pk=pk)
        serializer = CategorySerializer(category, context={'request': request})
        return Response(serializer.data)

    def create(self, request):
        """
        Create a new category. Managers only.
        """
        serializer = CategorySerializer(data=request.data, context={'request': request})
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
        serializer = CategorySerializer(category, data=request.data, context={'request': request})
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
        serializer = CategorySerializer(category, data=request.data, partial=True, context={'request': request}) # partial=True for partial updates
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


class MenuItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing MenuItems.
    - List view is lightweight and for public browsing.
    - Detail view includes all customization options.
    """
    queryset = MenuItem.objects.all()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return MenuItemDetailSerializer
        return MenuItemSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # For list view, only show available, standalone items
        if self.action == 'list':
            queryset = queryset.filter(is_standalone_item=True, is_available=True)
            # Apply existing filters from original code
            category_name = self.request.query_params.get('category')
            to_price = self.request.query_params.get('to_price')
            search = self.request.query_params.get('search')
            ordering = self.request.query_params.get('ordering')

            if category_name:
                queryset = queryset.filter(category__slug=category_name)
            if to_price:
                queryset = queryset.filter(price__lte=to_price)
            if search:
                queryset = queryset.filter(title__icontains=search)
            if ordering:
                queryset = queryset.order_by(ordering)

        # For retrieve view, prefetch related options for efficiency
        elif self.action == 'retrieve':
            queryset = queryset.prefetch_related(
                'option_groups__choices__item'
            )
        
        return queryset.select_related('category')


    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated, IsManager]
        return [permission() for permission in permission_classes]

    def retrieve(self, request, pk=None):
        """
        Retrieve a specific menu item. Publicly accessible.
        """
        queryset = MenuItem.objects.select_related('category').all() # Optimize with select_related
        menuitem = get_object_or_404(queryset, pk=pk)
        serializer = MenuItemDetailSerializer(menuitem, context={'request': request})
        return Response(serializer.data)

    def create(self, request):
        """
        Create a new menu item. Managers only.
        """
        serializer = MenuItemSerializer(data=request.data, context={'request': request})
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
        serializer = MenuItemSerializer(menuitem, data=request.data, context={'request': request})
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
        serializer = MenuItemSerializer(menuitem, data=request.data, partial=True, context={'request': request})
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
        cart_items = Cart.objects.filter(user=request.user).select_related('menuitem', 'menuitem__category') # Get cart items for current user
        serializer = CartItemSerializer(cart_items, many=True, context={'request': request})
        return Response(serializer.data)

    def create(self, request):
        """
        Add a menu item to the cart with selected options.
        If an identical item (same menuitem and same options) already exists
        in the cart, its quantity is increased. Otherwise, a new cart item is created.
        """
        serializer = CartItemSerializer(data=request.data, context={'request': self.request})
        serializer.is_valid(raise_exception=True)
        
        menuitem = serializer.validated_data['menuitem']
        quantity = serializer.validated_data['quantity']
        selected_options = serializer.validated_data.get('selected_options', [])

        # Calculate total price for the item
        unit_price = menuitem.price
        options_price = sum(option.price_adjustment for option in selected_options)
        total_price = (unit_price + options_price) * quantity

        # --- Smart Cart Item Logic ---
        # Look for an existing cart item with the exact same options
        cart_item = None
        existing_items = Cart.objects.filter(user=request.user, menuitem=menuitem)
        for item in existing_items:
            if set(item.selected_options.all()) == set(selected_options):
                cart_item = item
                break

        if cart_item:
            # Item exists, update quantity and price
            cart_item.quantity += quantity
            # Recalculate price for the updated total quantity
            cart_item.price = (cart_item.unit_price + options_price) * cart_item.quantity
            cart_item.save()
            # Update serializer instance with the updated object
            serializer = CartItemSerializer(cart_item, context={'request': self.request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            # Item does not exist, create a new one
            cart_item = Cart.objects.create(
                user=request.user,
                menuitem=menuitem,
                quantity=quantity,
                unit_price=unit_price + options_price, # Store unit price including options
                price=total_price,
            )
            cart_item.selected_options.set(selected_options)
            serializer = CartItemSerializer(cart_item, context={'request': self.request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        """
        Retrieve a specific cart item by its ID.
        URL: GET /api/cart/items/{cart_item_id}/
        """
        try:
            cart_item = Cart.objects.get(user=request.user, pk=pk)
            serializer = CartItemSerializer(cart_item, context={'request': request})
            return Response(serializer.data)
        except Cart.DoesNotExist:
            return Response({"error": "Cart item not found in your cart."}, status=status.HTTP_404_NOT_FOUND)

    def update(self, request, pk=None):
        """
        Update a cart item quantity using cart item ID from URL.
        URL: PUT /api/cart/items/{cart_item_id}/
        """
        if not pk:
            return Response({"error": "Cart item ID is required in URL."}, status=status.HTTP_400_BAD_REQUEST)
            
        quantity = request.data.get('quantity')
        if not quantity:
            return Response({"error": "Quantity is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            quantity = int(quantity)
            if quantity <= 0:
                return Response({"error": "Quantity must be a positive integer."}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({"error": "Invalid quantity."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            cart_item = Cart.objects.get(user=request.user, pk=pk)
        except Cart.DoesNotExist:
            return Response({"error": "Cart item not found in your cart."}, status=status.HTTP_404_NOT_FOUND)

        # Update quantity and price
        cart_item.quantity = quantity
        cart_item.price = cart_item.unit_price * cart_item.quantity
        cart_item.save()

        serializer = CartItemSerializer(cart_item, context={'request': request})
        return Response(serializer.data)

    def partial_update(self, request, pk=None):
        """
        Partially update a cart item (same as update for cart items).
        """
        return self.update(request, pk)

    def destroy(self, request, pk=None):
        """
        Deletes a specific item from the cart, identified by its Cart ID (pk).
        """
        try:
            cart_item = Cart.objects.get(user=request.user, pk=pk)
            cart_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Cart.DoesNotExist:
            return Response({"error": "Cart item not found."}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['delete'])
    def flush(self, request):
        """
        Clear all items from the current user's cart.
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
    lookup_url_kwarg = 'pk'  # Explicitly define lookup_url_kwarg
    lookup_field = 'pk'     # Explicitly define lookup_field
    queryset = Order.objects.all()
    permission_classes_by_action = {
        'list': [IsAuthenticated], # For all authenticated users (customers, managers, delivery crew) - will refine further
        'retrieve': [IsAuthenticated], # For all authenticated users - will refine further
        'create': [IsAuthenticated], # Customers placing orders
        'update': [IsAuthenticated, IsManager], # Use IsManager for manager-only update
        'partial_update': [IsAuthenticated, IsManager], # Use IsManager for manager-only partial update
        'destroy': [IsAuthenticated, IsManager], # Use IsManager for manager-only delete
        'assign_delivery_crew': [IsAuthenticated, IsManager], # Use IsManager for assign_delivery_crew
        'update_order_status_to_delivered': [IsAuthenticated, IsDeliveryCrew], # Use IsDeliveryCrew for delivery crew status update
    }

    def get_permissions(self):
        try:
            return [permission() for permission in self.permission_classes_by_action[self.action]]
        except KeyError:
            return [permission() for permission in self.permission_classes]

    def list(self, request):
        """
        List orders based on user role, with optional filtering by status for managers.
         Customers: See their own order history.
         Managers/Delivery Crew: See all orders (with filtering by status for managers).
        """
        queryset = Order.objects.all() # Start with all orders queryset
        status_filter_str = request.query_params.get('status') # Get status as string from query params (important for validation)
        status_filter = None # Initialize status_filter to None

        if request.user.groups.filter(name='Manager').exists() or request.user.is_superuser: # Managers and Admin can see all orders, with filtering
            if status_filter_str: # If status filter is provided
                valid_status_choices = [str(code) for code, label in Order.STATUS_CHOICES] # Get valid status codes as strings
                if status_filter_str in valid_status_choices: # Validate against valid choices (as strings)
                    status_filter = int(status_filter_str) # Convert to integer for filtering
                    queryset = queryset.filter(status=status_filter) # Filter queryset by status value
                else:
                    return Response({"error": f"Invalid status value. Allowed values are: {', '.join(valid_status_choices)}"}, status=status.HTTP_400_BAD_REQUEST) # Return 400 for invalid status

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
        Creates an order from the user's cart.
        """
        user = request.user
        cart_items = Cart.objects.filter(user=user)

        if not cart_items.exists():
            return Response({"error": "Your cart is empty."}, status=status.HTTP_400_BAD_REQUEST)

        # Use a transaction to ensure atomicity
        with transaction.atomic():
            # Calculate total price
            total = sum(item.price for item in cart_items)

            # Create the order
            order = Order.objects.create(user=user, total=total, status=0)

            # Create order items from cart items
            for item in cart_items:
                order_item = OrderItem.objects.create(
                    order=order,
                    menuitem=item.menuitem,
                    quantity=item.quantity,
                    price=item.price,
                )
                # --- CRUCIAL STEP: Copy selected options ---
                order_item.selected_options.set(item.selected_options.all())

            # Clear the cart
            cart_items.delete()

        serializer = OrderSerializer(order, context={'request': request})
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
        if not (request.user.groups.filter(name='Manager').exists() or request.user.groups.filter(name='Delivery crew').exists()): # Only delivery crew can update status
            return Response({"error": "Only delivery crew or managers can update order status."}, status=status.HTTP_403_FORBIDDEN)

        order = self.get_object() # Helper to get Order instance

        if request.user.groups.filter(name='Delivery crew').exists(): # Check for Delivery Crew *specifically*
            if order.delivery_crew != request.user: # Delivery crew assignment check
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
    
class GroupViewSet(viewsets.ViewSet):
    """
    ViewSet for listing groups and managing user group assignments (Manager role).
    """
    lookup_url_kwarg = 'pk'  # Explicitly define lookup_url_kwarg
    lookup_field = 'pk' 
    permission_classes = [IsAuthenticated, IsAdminUser] # Only managers and admins can access these endpoints

    def list(self, request):
        """
        List all available groups (e.g., Manager, Delivery crew).
        """
        queryset = Group.objects.all()
        serializer = GroupSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['put']) # Custom action to add a user to a group (Manager action)
    def add_user(self, request, pk=None): # pk will be group ID
        """
        Add a user to a group.
        Expects 'user_id' in request data.
        """
        group = self.get_object() # Get the group instance based on pk (group ID)

        username = request.data.get('username') # Expect username instead of user_id for easier use (can change to user_id if preferred)
        if not username:
            return Response({"error": "Username is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_400_BAD_REQUEST)

        group.user_set.add(user) # Add user to the group (using User.groups ManyToManyField)
        return Response({"message": f"User '{user.username}' added to group '{group.name}'."}, status=status.HTTP_200_OK)


    @action(detail=True, methods=['delete']) # Custom action to remove a user from a group (Manager action)
    def remove_user(self, request, pk=None): # pk will be group ID
        """
        Remove a user from a group.
        Expects 'username' in request data.
        """
        group = self.get_object() # Get the group instance based on pk (group ID)

        username = request.data.get('username') # Expect username in request data
        if not username:
            return Response({"error": "Username is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_400_BAD_REQUEST)

        group.user_set.remove(user) # Remove user from the group
        return Response({"message": f"User '{user.username}' removed from group '{group.name}'."}, status=status.HTTP_200_OK)


    def get_object(self): # Helper method to get Group instance for detail actions (add/remove user)
        queryset = Group.objects.all() # Get all groups queryset
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        obj = get_object_or_404(queryset, **filter_kwargs)
        self.check_object_permissions(self.request, obj) # Optional permission check (not really needed for GroupViewSet in this example as permission is on ViewSet level)
        return obj  
    

class DirectOrderCreateView(APIView):
    """
    View to create an order directly from payload data for voice orders.
    Sets user to None and is_voice_order to True.
    """
    permission_classes = [HasAPIKey]

    def post(self, request, *args, **kwargs):
        input_serializer = DirectOrderInputSerializer(data=request.data)
        if not input_serializer.is_valid():
            return Response(input_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = input_serializer.validated_data
        items_data = validated_data['items']

        try:
            # --- Optional: Try to find existing user by phone ---
            # existing_user = User.objects.filter(profile__phone=validated_data['customer_phone']).first() # Requires a Profile model or similar
            # user_to_assign = existing_user # Assign if found, otherwise None below is fine
            # --- End Optional ---

            with transaction.atomic():
                total_price = Decimal(0)
                menu_items_map = {}
                order_item_instances = []

                # Validate items and calculate total price (same logic as before)
                for item_data in items_data:
                    menuitem_id = item_data['menuitem_id']
                    quantity = item_data['quantity']
                    if menuitem_id not in menu_items_map:
                         try:
                             menu_item = MenuItem.objects.get(pk=menuitem_id)
                             menu_items_map[menuitem_id] = menu_item
                         except MenuItem.DoesNotExist:
                             return Response({"error": f"MenuItem with id {menuitem_id} not found."}, status=status.HTTP_400_BAD_REQUEST)
                    else:
                         menu_item = menu_items_map[menuitem_id]
                    item_total = menu_item.price * quantity
                    total_price += item_total
                    order_item_instances.append(OrderItem(menuitem=menu_item, quantity=quantity, price=item_total))

                # --- Create Order, setting user=None and is_voice_order=True ---
                order = Order.objects.create(
                    user=None, # Assign None for voice orders
                    # user=user_to_assign, # Use this if implementing optional user lookup
                    total=total_price,
                    status=0,
                    customer_name=validated_data['customer_name'],
                    customer_phone=validated_data['customer_phone'],
                    delivery_address=validated_data['delivery_address'],
                    is_voice_order=True # Set the flag
                )
                # --- End Order Creation ---

                for oi in order_item_instances:
                    oi.order = order
                OrderItem.objects.bulk_create(order_item_instances)

                response_serializer = OrderSerializer(order)
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            print(f"Error creating direct order: {e}")
            return Response({"error": "An internal error occurred while creating the order."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)