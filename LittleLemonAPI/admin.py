from django.contrib import admin
from .models import Category, MenuItem, Cart, Order, OrderItem
# Register your models here.

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'slug', 'title')
    list_filter = ('title',)
    search_fields = ['title']

class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'price', 'featured')
    search_fields = ['title']


class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'menuitem', 'quantity', 'unit_price', 'price']
    search_fields = ['user']

class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'delivery_crew', 'status', 'total', 'date']
    search_fields = ['user']

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'delivery_crew':
            kwargs['required'] = False
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'menuitem', 'quantity', 'price']
    


admin.site.register(Category, CategoryAdmin)
admin.site.register(MenuItem, MenuItemAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem, OrderItemAdmin)