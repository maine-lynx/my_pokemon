from django.contrib import admin

# Register your models here.
from items.models import Item, TrainerItem


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'effect_value', 'icon')
    list_filter = ('category',)


@admin.register(TrainerItem)
class TrainerItemAdmin(admin.ModelAdmin):
    list_display = ('trainer', 'item', 'quantity')
    list_filter = ('item',)