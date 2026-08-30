from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from trainers.models import Trainer, OwnedPokemon
from pokedex.models import Pokemon

class Command(BaseCommand):
    help = '给超级用户「小智」灌入全图鉴宝可梦'

    def handle(self, *args, **options):
        # 1. 获取超级用户
        try:
            user = User.objects.get(username='mianyinsheli')
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('❌ 用户 mianyinsheli 不存在，请先创建超级用户'))
            return

        # 2. 训练师
        trainer, created = Trainer.objects.get_or_create(
            user=user,
            defaults={'name': '小智'}
        )
        if not created and trainer.name != '小智':
            trainer.name = '小智'
            trainer.save()

        self.stdout.write(f'训练师: {trainer.name} (新创建: {created})')

        # 3. 全图鉴
        all_species = Pokemon.objects.all()
        total = all_species.count()
        self.stdout.write(f'图鉴总数: {total}')

        # 4. 批量创建
        created_count = 0
        for species in all_species:
            obj, is_new = OwnedPokemon.objects.get_or_create(
                trainer=trainer,
                species=species,
                defaults={
                    'level': 50,
                    'current_hp': species.base_hp or 50,
                    'exp': 0,
                    'is_active': True,
                    'nickname': species.name,
                }
            )
            if is_new:
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'✅ 完成！新增 {created_count} 只，训练师共拥有 {trainer.ownedpokemon_set.count()} 只'
            )
        )