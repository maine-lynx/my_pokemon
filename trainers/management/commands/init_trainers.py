# trainers/management/commands/init_trainers.py
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from pokedex.models import Pokemon
from trainers.models import OwnedPokemon, Trainer


class Command(BaseCommand):
    help = "初始化训练师及其宝可梦"

    def handle(self, *args, **options):
        # 1. 确保有超级用户
        user, _ = User.objects.get_or_create(username="mianyinsheli", defaults={"is_staff": True, "is_superuser": True})
        if not user.has_usable_password():
            user.set_password("qwer1234")  # ← 改成你的密码
            user.save()

        # 2. 创建训练师
        trainer, _ = Trainer.objects.get_or_create(
            user=user,
            defaults={
                "name": "小智",
                "region": "关都",
                "sprite_url": "",
                "money": 1000,
                "badges": 0,
            },
        )
        self.stdout.write(f"✅ 训练师 {trainer.name} 就绪")

        # 3. 分配初始宝可梦
        starter_ids = [1, 4, 7]  # 妙蛙种子、小火龙、杰尼龟
        for idx, pid in enumerate(starter_ids, start=1):
            species = Pokemon.objects.get(pokemon_id=pid)
            OwnedPokemon.objects.get_or_create(
                trainer=trainer,
                species=species,  # ← 改：pokemon → species
                defaults={
                    "level": 5,
                    "current_hp": 50,  # ← 必须显式传，模型里没默认值
                    "exp": 0,
                    "is_active": idx <= 6,  # 前6只设为出战
                },
            )
        self.stdout.write(self.style.SUCCESS(f"✅ 分配了 {len(starter_ids)} 只初始宝可梦"))

        # 4. 统计
        count = OwnedPokemon.objects.filter(trainer=trainer).count()
        self.stdout.write(self.style.SUCCESS(f"🎉 训练师共有 {count} 只宝可梦"))

        # 5. 验证技能自动复制是否生效
        for op in OwnedPokemon.objects.filter(trainer=trainer):
            move_count = op.moves.count()
            self.stdout.write(f"  {op.species.name} 会 {move_count} 个技能")
