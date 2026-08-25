from django.db import models

# Create your models here.
class Type(models.Model):
    """
    属性：火/草/水/电
    """
    #unique参数什么作用
    name = models.CharField(max_length=20,unique=True)
    #克制关系用ManyToMany存，为什么？
    strong_against = models.ManyToManyField("self",symmetrical=False,related_name='weak_against',blank=True)
    def __str__(self):
        return self.name

class Move(models.Model):
    """
    技能
    """
    name = models.CharField(max_length=50)
    type = models.ForeignKey(Type,on_delete=models.CASCADE)
    power = models.IntegerField(default=0)  #威力
    accuracy = models.IntegerField(default=100) #命中率
    pp = models.IntegerField(default=10)    #使用次数
    description = models.TextField(blank=True)  #什么作用？
    def __str__(self):
        return self.name

class Pokemon(models.Model):
    """
    宝可梦物种
    """
    name = models.CharField(max_length=50,unique=True)
    type = models.ManyToManyField(Type,related_name='pokemon')
    base_hp = models.IntegerField(default=50)
    base_attack = models.IntegerField(default=50)
    base_defense = models.IntegerField(default=50)
    base_speed = models.IntegerField(default=50)
    #blank是？
    moves = models.ManyToManyField(Move,related_name='learned_by',blank=True)
    evolution_of = models.ForeignKey(
    'self',
    blank=True,
    null=True,
    on_delete=models.SET_NULL,
    related_name='evolutions'   #专属名字，防止模型冲突
    )
    sprite_url = models.URLField(blank=True)    #前端精灵显示图片
    def __str__(self):
        return self.name