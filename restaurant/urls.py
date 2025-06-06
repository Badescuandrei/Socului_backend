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
    # Better REST design: Update cart items using menuitem_id in URL
    path('cart/menu-items/<int:menuitem_id>/', CartViewSet.as_view({
        'put': 'update_by_menuitem',
        'patch': 'update_by_menuitem',
        'delete': 'delete_by_menuitem'
    }), name='cart-menuitem-update'),
]