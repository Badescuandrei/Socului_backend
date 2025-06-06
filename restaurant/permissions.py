from rest_framework import permissions

class IsManager(permissions.BasePermission):
    """
    Permission class to allow only users in the 'Manager' group.
    """
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Manager').exists() or request.user.is_superuser # Include is_superuser for admin access

class IsDeliveryCrew(permissions.BasePermission):
    """
    Permission class to allow only users in the 'Delivery crew' group.
    """
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Delivery crew').exists() or request.user.groups.filter(name='Manager').exists() or request.user.is_superuser # Delivery crew, Managers, and Admin allowed