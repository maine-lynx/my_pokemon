#导入模型基类
from django.db import models

#注册登录模块
from django.contrib.auth.models import User
#从图鉴app导入宝可梦的物种，技能
from pokedex.models import Pokemon, Move

#相当于数据库中的一张表，表名trainer_trainer
class Trainer(models.Model):
    """训练师（关联 Django 自带 User）"""
    #一对一关系，如过User被删除，对应的trainer也被删除
    #数据库层面，新建一列id，作为主键，保证不重复
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    #Field字段，相当于python中的属性
    name = models.CharField(max_length=50)
    money = models.IntegerField(default=1000)
    badges = models.IntegerField(default=0)
    #类似python实例方法
    def __str__(self):
        return self.name


class OwnedPokemon(models.Model):
    """训练师拥有的宝可梦个体（有等级、当前HP等）"""
    #多对一关系，关联删除，，支持反向查询trainer.pokemons.all()该训练家的所有宝可梦
    #数据库层面：新建一个triner列作为主键
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE, related_name='pokemons')
    #关联到“物种”（Pokemon表 ）
    species = models.ForeignKey(Pokemon, on_delete=models.CASCADE)
    #昵称，可选
    nickname = models.CharField(max_length=50, blank=True)
    #等级
    level = models.IntegerField(default=5)
    #当前血量，
    current_hp = models.IntegerField()  #为什么没有默认值
    #经验值
    exp = models.IntegerField(default=0)
    # 是否在战斗队伍中（最多6只）
    is_active = models.BooleanField(default=False)
    #数据库层面：新建了一张中间表，用来记录多对多的两边关系，相当于python的一个列表
    moves = models.ManyToManyField(Move, related_name='users_of_move', blank=True)  # 当前会的4个技能
    #重写save方法
    def save(self, *args, **kwargs):
        #self.pk是主键（Primary Key）
        is_new = self.pk is None  # 判断是不是第一次创建
        #必须先save，因为ManyToMany必须要实例有主键才能建立
        super().save(*args, **kwargs)

        if is_new:
            # 创建完成后，自动把物种（Pokemon）会的技能复制给这只个体
            for move in self.species.moves.all():
                self.moves.add(move)
    def __str__(self):
        return f"{self.nickname or self.species.name} (Lv.{self.level})"