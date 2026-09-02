from django.db import models

# Create your models here.
from trainers.models import Trainer


class Item(models.Model):
    """道具定义（物种表）"""
    CATEGORY_CHOICES = [
        ('potion', '伤药'),
        ('pokeball', '精灵球'),
        ('heal', '状态治愈'),
    ]

    item_id = models.IntegerField(unique=True, null=True, blank=True)
    name = models.CharField(max_length=50, unique=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    price = models.IntegerField(default=0)
    effect_value = models.IntegerField(default=0, help_text='回复量/捕捉率加成等')
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=10, default='🧪', help_text='emoji 图标')

    def __str__(self):
        return f"{self.icon} {self.name}"


class TrainerItem(models.Model):
    """训练师的道具背包"""
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)

    class Meta:
        unique_together = ('trainer', 'item')

    def __str__(self):
        return f"{self.trainer.name} × {self.item.name} ({self.quantity})"