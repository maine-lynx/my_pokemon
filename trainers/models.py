from django.db import models

# Create your models here.
from django.contrib.auth.models import User
from pokedex.models import Pokemon, Move

class Trainer(models.Model):
    """训练师（关联 Django 自带 User）"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    money = models.IntegerField(default=1000)
    badges = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class OwnedPokemon(models.Model):
    """训练师拥有的宝可梦个体（有等级、当前HP等）"""
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE, related_name='pokemons')
    species = models.ForeignKey(Pokemon, on_delete=models.CASCADE)
    nickname = models.CharField(max_length=50, blank=True)
    level = models.IntegerField(default=5)
    current_hp = models.IntegerField()
    exp = models.IntegerField(default=0)
    is_active = models.BooleanField(default=False)  # 是否在战斗队伍中（最多6只）
    moves = models.ManyToManyField(Move, related_name='users_of_move', blank=True)  # 当前会的4个技能

    def save(self, *args, **kwargs):
        # 新建时自动设置当前HP为满血
        if not self.pk:
            self.current_hp = self.species.base_hp + self.level * 2
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nickname or self.species.name} (Lv.{self.level})"