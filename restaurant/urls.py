from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import CartViewSet, CategoryViewSet, MenuItemViewSet, OrderViewSet

router = SimpleRouter()
router.register(r'categories', CategoryViewSet, basename='category') # 'categories' is the URL prefix
router.register(r'menu-items', MenuItemViewSet, basename='menuitem') #  'menuitems' is the URL prefix
router.register(r'cart/items', CartViewSet, basename='cart-item')
router.register(r'orders', OrderViewSet, basename='order')

urlpatterns = [
    path('', include(router.urls)),
]