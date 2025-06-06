from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Cart, Category, MenuItem, Order, OrderItem
from .serializers import CartItemSerializer, CategorySerializer, DirectOrderInputSerializer, GroupSerializer, MenuItemSerializer, OrderSerializer
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


class MenuItemViewSet(viewsets.ViewSet):
    """
    ViewSet for viewing and editing MenuItems.
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

        serializer = MenuItemSerializer(queryset, many=True, context={'request': request}) # No pagination for now, add later if needed
        return Response(serializer.data)


    def retrieve(self, request, pk=None):
        """
        Retrieve a specific menu item. Publicly accessible.
        """
        queryset = MenuItem.objects.select_related('category').all() # Optimize with select_related
        menuitem = get_object_or_404(queryset, pk=pk)
        serializer = MenuItemSerializer(menuitem, context={'request': request})
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
        if not created: # If item already existed, update quantity
             cart_item.quantity += quantity
        else: # If newly created, set quantity
             cart_item.quantity = quantity

        cart_item.price = cart_item.unit_price * cart_item.quantity
        cart_item.save()

        # --- PASS CONTEXT TO CartItemSerializer ---
        serializer = CartItemSerializer(cart_item, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK) # 201 if created, 200 if updated

    def update(self, request, pk=None): # pk is not really used for cart update in this design, but included for ViewSet consistency
        """
        Update a cart item (e.g., change quantity).
        Expects quantity in request data. Cart item is identified by menuitem_id in URL or body.
        """
        menuitem_id = request.data.get('menuitem_id') # Or get pk from URL if you prefer
        quantity = request.data.get('quantity')

        if not quantity or not menuitem_id:
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

        serializer = CartItemSerializer(cart_item, context={'request': request})
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

    def update_by_menuitem(self, request, menuitem_id=None):
        """
        Update cart item using menuitem_id from URL path (RESTful approach).
        URL: PUT /api/cart/menu-items/{menuitem_id}/
        """
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
            menuitem = MenuItem.objects.get(pk=menuitem_id)
        except MenuItem.DoesNotExist:
            return Response({"error": "MenuItem not found."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            cart_item = Cart.objects.get(user=request.user, menuitem=menuitem)
        except Cart.DoesNotExist:
            return Response({"error": "Cart item not found in your cart."}, status=status.HTTP_404_NOT_FOUND)

        # Update quantity and price
        cart_item.quantity = quantity
        cart_item.price = cart_item.unit_price * cart_item.quantity
        cart_item.save()

        serializer = CartItemSerializer(cart_item, context={'request': request})
        return Response(serializer.data)

    def delete_by_menuitem(self, request, menuitem_id=None):
        """
        Delete cart item using menuitem_id from URL path (RESTful approach).
        URL: DELETE /api/cart/menu-items/{menuitem_id}/
        """
        try:
            menuitem = MenuItem.objects.get(pk=menuitem_id)
        except MenuItem.DoesNotExist:
            return Response({"error": "MenuItem not found."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            cart_item = Cart.objects.get(user=request.user, menuitem=menuitem)
            cart_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Cart.DoesNotExist:
            return Response({"error": "Cart item not found in your cart."}, status=status.HTTP_404_NOT_FOUND)
    
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