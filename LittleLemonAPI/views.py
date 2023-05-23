import datetime
from django.shortcuts import render, get_object_or_404
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.generics import RetrieveUpdateAPIView, DestroyAPIView, ListCreateAPIView, ListAPIView
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, BasePermission, IsAdminUser
from .models import Category, MenuItem, Cart, Order, OrderItem
from .serializers import MenuItemSerializer, UserSerializer, CartSerializer, OrderSerializer, OrderItemSerializer, CategorySerializer
from django.contrib.auth.models import User, Group

class IsManager(BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Manager').exists()

class IsManagerOrDeliveryCrew(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.groups.filter(name='Delivery crew').exists()
            or request.user.groups.filter(name='Manager').exists()
            )
    
class CategoryView(ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return []
        return [IsAdminUser()]

class MenuitemsView(ListCreateAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    ordering_fields = ['price','id']
    search_fields = ['title','category__title']


    def get_queryset(self):
        if self.request.method == 'GET':
            queryset = MenuItem.objects.all()
            category_name = self.request.query_params.get('category')
            if category_name:
                queryset = queryset.filter(category__title=category_name)
            return queryset
        return super().get_queryset()

    def get_permissions(self):
        if self.request.method == 'GET':
            return []
        elif self.request.method == 'POST':
            return [IsManager()]
        return []

class SingleMenuitemsView(RetrieveUpdateAPIView, DestroyAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return []
        elif self.request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            return [IsManager()]

class ManagerView(APIView):
    permission_classes = [IsManager]

    def get(self, request):
        manager = User.objects.filter(groups=1)
        serializer = UserSerializer(manager, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        username = request.data.get('username')
        if not username:
            raise ValidationError('username field is missing')
        else:
            user = get_object_or_404(User, username=username)
            serializer = UserSerializer(user)
            managers = Group.objects.get(name='Manager')
            managers.user_set.add(user)
            return Response({"messege": "ok"}, '201')

class DeleteManagerView(APIView):
    permission_classes = [IsManager]

    def delete(self, request, user_id):
        managers = User.objects.filter(groups=1)
        user = get_object_or_404(managers, id=user_id)
        managers = Group.objects.get(name='Manager')
        managers.user_set.remove(user)
        return Response({"messege": "success"})
    

class DeliveryCrewView(APIView):
    permission_classes = [IsManager]

    def get(self, request):
        deliveryCrews = User.objects.filter(groups=2)
        serializer = UserSerializer(deliveryCrews, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        username = request.data.get('username')
        if not username:
            raise ValidationError('username field is missing')
        else:
            user = get_object_or_404(User, username=username)
            serializer = UserSerializer(user)
            deliveryCrews = Group.objects.get(id=2)
            deliveryCrews.user_set.add(user)
            return Response({"messege": "ok"}, '201')

class DeleteDeliveryCrewView(APIView):
    permission_classes = [IsManager]

    def delete(self, request, user_id):
        deliveryCrews = User.objects.filter(groups=2)
        user = get_object_or_404(deliveryCrews, id=user_id)
        deliveryCrews = Group.objects.get(id=2)
        deliveryCrews.user_set.remove(user)
        return Response({"messege": "success"})
    

class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        carts = Cart.objects.filter(user=user)
        serializer = CartSerializer(carts, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = CartSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            serializer.save()
            return Response({"messege": "ok"}, '201')
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request):
        user = request.user
        carts = Cart.objects.filter(user=user)
        for cart in carts:
            cart.delete()
        return Response({"messege": "ok"}, '204')


class OrderView(ListAPIView):
    permission_classes = [IsAuthenticated]
    ordering_fields = ['total', 'id', 'user']
    search_fields = ['user', 'delivery_crew']
    serializer_class = OrderSerializer


    def get_queryset(self):
        if self.request.method == 'GET':
            user = self.request.user
            if user.groups.filter(name='Manager').exists():
                queryset = Order.objects.all()
            elif user.groups.filter(name='Delivery crew').exists():
                queryset = Order.objects.filter(delivery_crew=user)
            else:
                queryset = Order.objects.filter(user=user)
            status = self.request.query_params.get('status')
            if status != None:
                queryset = queryset.filter(status=status)
            return queryset
        return super().get_queryset()

    
    def post(self, request):
        user = request.user

        carts = Cart.objects.filter(user=user)

        if not carts:
            return Response({"messege": "You don't have anything in your cart."}, '400')
        
        total = sum([cart.price for cart in carts])
        order = Order(
            user=user, 
            delivery_crew=None, 
            status=0, 
            total=total, 
            date=datetime.date.today(),
            )
        order.save()
        
        data = []
        for cart in carts:
            data.append(
                {
                    'order_id': order.id,
                    'menuitem_id': cart.menuitem.id,
                    'quantity': cart.quantity,
                    'unit_price': cart.unit_price,
                    'price': cart.price
                }
            )
        serializer = OrderItemSerializer(data=data, many=True)
        if serializer.is_valid():
            serializer.save()
            for cart in carts:
                cart.delete()
            return Response({"messege": "ok"}, '201')
        order.delete()
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
class SingleOrderView(RetrieveUpdateAPIView, DestroyAPIView):
    serializer_class = OrderSerializer

    def partial_update(self, request, *args, **kwargs):
        if request.user.groups.filter(name='Manager').exists():
            return super().partial_update(request, *args, **kwargs)
        elif request.user.groups.filter(name='Delivery crew').exists():
            status_value = request.data.get('status')
            order = self.get_object()
            order.status = status_value
            order.save(update_fields=['status'])
            serializer = self.get_serializer(order)
            return Response(serializer.data)


    def get_queryset(self):
        if self.request.user.groups.filter(name='Manager').exists():
            return Order.objects.all()
        elif self.request.user.groups.filter(name='Delivery crew').exists():
            user = self.request.user
            return Order.objects.filter(delivery_crew=user)
        else:
            user = self.request.user
            return Order.objects.filter(user=user)
        
    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        elif self.request.method in ('PUT', 'DELETE'):
            return [IsManager()]
        elif self.request.method == 'PATCH':
            return [IsManagerOrDeliveryCrew()]
        else:
            return super().get_permissions()

    