from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import CartViewSet, CategoryViewSet, GroupViewSet, MenuItemViewSet, OrderViewSet, DirectOrderCreateView

router = SimpleRouter()
router.register(r'categories', CategoryViewSet, basename='category') # 'categories' is the URL prefix
router.register(r'menu-items', MenuItemViewSet, basename='menuitem') #  'menuitems' is the URL prefix
router.register(r'cart/items', CartViewSet, basename='cart-item')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'groups', GroupViewSet, basename='group')

urlpatterns = [
    path('', include(router.urls)),
    path('direct-order/', DirectOrderCreateView.as_view(), name='direct-order-create'),
]