from django.core.management.base import BaseCommand
from items.models import Item, TrainerItem
from trainers.models import Trainer


class Command(BaseCommand):
    help = '初始化道具数据并给训练师发放初始道具'

    def handle(self, *args, **options):
        items_data = [
            {'item_id': 1, 'name': '伤药', 'category': 'potion', 'price': 200,
             'effect_value': 50, 'description': '回复 50 点 HP', 'icon': '🧪'},
            {'item_id': 2, 'name': '高级伤药', 'category': 'potion', 'price': 700,
             'effect_value': 200, 'description': '回复 200 点 HP', 'icon': '💊'},
            {'item_id': 3, 'name': '精灵球', 'category': 'pokeball', 'price': 300,
             'effect_value': 10, 'description': '用于捕捉野生宝可梦', 'icon': '🔴'},
            {'item_id': 4, 'name': '超级球', 'category': 'pokeball', 'price': 800,
             'effect_value': 25, 'description': '更高捕捉率的精灵球', 'icon': '🔵'},
        ]

        self.stdout.write('📌 创建道具...')
        item_objs = {}
        for data in items_data:
            obj, created = Item.objects.get_or_create(
                item_id=data['item_id'],
                defaults=data
            )
            item_objs[data['item_id']] = obj
            status = '新建' if created else '已存在'
            self.stdout.write(f'  {data["icon"]} {data["name"]} ({status})')

        self.stdout.write(self.style.SUCCESS(f'✅ 道具就绪，共 {len(item_objs)} 种'))

        trainers = Trainer.objects.all()
        if not trainers.exists():
            self.stdout.write(self.style.WARNING('⚠️ 没有训练师，跳过道具发放'))
            return

        for trainer in trainers:
            for iid, qty in [(1, 5), (2, 2), (3, 10), (4, 3)]:
                TrainerItem.objects.get_or_create(
                    trainer=trainer, item=item_objs[iid],
                    defaults={'quantity': qty}
                )
            self.stdout.write(
                self.style.SUCCESS(f'✅ {trainer.name} 获得初始道具')
            )