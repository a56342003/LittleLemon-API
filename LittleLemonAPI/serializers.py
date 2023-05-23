from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from django.contrib.auth.models import User, Group
from .models import Category, MenuItem, Cart, Order, OrderItem
from django.http import Http404

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id','title', 'slug']
        validators = [
            UniqueTogetherValidator(
                queryset=Category.objects.all(),
                fields=['title']
            ),
        ]

class MenuItemSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True)
    class Meta:
        model = MenuItem
        fields = [
            'id', 
            'title', 
            'price', 
            'featured',
            'category', 
            'category_id',
            ]
        validators = [UniqueTogetherValidator(queryset=MenuItem.objects.all(), message='The title is not unique.', fields=['title'])]

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'name']

class UserSerializer(serializers.ModelSerializer):
    groups = serializers.SerializerMethodField(read_only=True)

    def get_groups(self, obj):
        return GroupSerializer(obj.groups.all(), many=True).data
    
    class Meta:
        model = User
        fields = [
            'id',
            'username', 
            'first_name', 
            'last_name', 
            'email',
            'groups',
            ]

class CartSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        default=serializers.CurrentUserDefault()
    )
    menuitem = MenuItemSerializer(read_only=True)
    menuitem_id = serializers.IntegerField(write_only=True)
    unit_price = serializers.DecimalField(max_digits=6, decimal_places=2, read_only=True)
    quantity = serializers.IntegerField()
    price = serializers.SerializerMethodField()

    
    def get_price(self, obj):
        return obj.quantity * obj.unit_price

    def create(self, validated_data):
        menuitem_id = validated_data['menuitem_id']
        menuitem = get_object_or_404(MenuItem, id=menuitem_id, )
        validated_data['unit_price'] = menuitem.price
        validated_data['price'] = validated_data['quantity'] * validated_data['unit_price']
        cart = super().create(validated_data)
        return cart

    class Meta:
        model = Cart
        fields = [
            'id',
            'user',
            'menuitem_id',
            'menuitem',
            'unit_price',
            'quantity',
            'price',
        ]
        validators = [
            UniqueTogetherValidator(
                queryset=Cart.objects.all(),
                fields=['user', 'menuitem_id']
            ),
        ]
    
class OrderItemSerializer(serializers.ModelSerializer):
    order = serializers.PrimaryKeyRelatedField(
        read_only=True,
    )
    order_id = serializers.IntegerField(write_only=True)
    menuitem = MenuItemSerializer(read_only=True)
    menuitem_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = OrderItem
        fields = [
            'id',
            'order',
            'order_id',
            'menuitem',
            'menuitem_id',
            'quantity',
            'unit_price',
            'price',
        ]


class OrderSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        default=serializers.CurrentUserDefault()
    )
    delivery_crew = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(id=2),
        allow_null=True,
        default=None,
    )
    delivery_crew_id = serializers.IntegerField(write_only=True)
    orderitems = serializers.SerializerMethodField()

    def get_orderitems(self, obj):
        orderitems = OrderItem.objects.filter(order=obj)
        return OrderItemSerializer(orderitems, many=True).data
    
    def validate_delivery_crew_id(self, value):
        try:
            user = User.objects.get(id=value)
        except User.DoesNotExist:
            raise Http404()
        if not user.groups.filter(name='Delivery crew').exists():
            raise serializers.ValidationError('User does not belong to the Delivery crew group.')
        return value


    
    class Meta:
        model = Order
        fields = [
            'id',
            'user',
            'delivery_crew',
            'delivery_crew_id',
            'status',
            'total',
            'date',
            'orderitems',
        ]
