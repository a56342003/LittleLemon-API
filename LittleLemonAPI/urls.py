from django.urls import path
from . import views

urlpatterns = [
    path('menu-items/', views.MenuitemsView.as_view()),
    path('menu-items/<int:pk>', views.SingleMenuitemsView.as_view()),
    path('groups/manager/users', views.ManagerView.as_view(),),
    path('groups/manager/users/<int:user_id>', views.DeleteManagerView.as_view()),
    path('groups/delivery-crew/users', views.DeliveryCrewView.as_view(),),
    path('groups/delivery-crew/users/<int:user_id>', views.DeleteDeliveryCrewView.as_view()),
    path('cart/menu-items/', views.CartView.as_view()),
    path('orders/', views.OrderView.as_view()),
    path('orders/<int:pk>', views.SingleOrderView.as_view()),
    path('categorys/', views.CategoryView.as_view()),
]