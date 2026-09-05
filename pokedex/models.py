from django.db import models


# Create your models here.
# 创建一张表，表名Type
class Type(models.Model):
    """
    属性：火/草/水/电
    """

    # 创建一列存储属性名称，unique参数保证数据库层面不重复，重复直接拒绝
    name = models.CharField(max_length=20, unique=True)
    # 克制关系用ManyToMany存（相当于一个对象列表或集合），克制关系是一张网，多对多
    strong_against = models.ManyToManyField(
        "self",  # 自关联，Type关联Type，自己关联自己
        symmetrical=False,  # 单向关联，不对称，A克制B，不代表B克制A
        related_name="weak_against",  # 反向访问名，从被克制的方向查找回来
        blank=True,  # Django表单层面允许不填（即可以不克制任何关系）
    )

    # django后台显示时调用这个方法
    def __str__(self):
        return self.name


class Move(models.Model):
    """
    技能
    """

    # 技能id
    move_id = models.IntegerField(unique=True, null=True, blank=True)
    # 相当于创建一个Move表中的一个str类型的列name
    name = models.CharField(max_length=100)
    # 相当于一个对象引用另一个对象，引用一个Type对象
    # 数据库层面：Move表里存储一个type_id列，指向Type表的主键
    # on_delete=models.CASCADE:如果关联的Type被删除，所有这个Type的Move也一起删除
    type = models.ForeignKey(Type, on_delete=models.CASCADE)
    # 相当于创建一个整数类型的列名power，accuracy，pp
    power = models.IntegerField(default=0)  # 威力
    accuracy = models.IntegerField(default=100)  # 命中率
    pp = models.IntegerField(default=10)  # 使用次数
    # 优先级
    priority = models.IntegerField(default=0)
    # 1，2，3：物理，特殊，变化
    damage_class = models.IntegerField(default=2)
    # 在 damage_class 下面加一行
    generation_id = models.IntegerField(null=True, blank=True)
    # TextField相当于长字符串，没有长度限制
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Pokemon(models.Model):
    """
    宝可梦物种
    """

    pokemon_id = models.IntegerField(unique=True, null=True, blank=True)
    # 在 pokemon_id 下面加一行
    species_id = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(default=0)
    weight = models.IntegerField(default=0)
    base_experience = models.IntegerField(default=0)
    name = models.CharField(max_length=50, unique=True)
    type = models.ManyToManyField(Type, related_name="pokemon")
    base_hp = models.IntegerField(default=50)
    base_attack = models.IntegerField(default=50)
    base_defense = models.IntegerField(default=50)
    base_speed = models.IntegerField(default=50)
    moves = models.ManyToManyField(Move, through="PokemonMove", related_name="learned_by")
    evolution_of = models.ForeignKey(
        "self",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="evolutions",  # 专属名字，防止模型冲突
    )
    sprite_url = models.URLField(blank=True)  # 前端精灵显示图片

    def __str__(self):
        return self.name


class PokemonMove(models.Model):
    """
    自定义中间表：记录宝可梦学会技能的等级
    """

    pokemon = models.ForeignKey(Pokemon, on_delete=models.CASCADE)
    move = models.ForeignKey(Move, on_delete=models.CASCADE)
    learn_level = models.IntegerField(default=1)

    class Meta:
        unique_together = ("pokemon", "move")  # 防止同一技能重复关联

    def __str__(self):
        return f"{self.pokemon.name} → {self.move.name} (Lv.{self.learn_level})"
