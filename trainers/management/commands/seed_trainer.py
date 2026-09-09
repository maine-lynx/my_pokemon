from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from pokedex.models import Pokemon
from trainers.models import OwnedPokemon, Trainer


class Command(BaseCommand):
    help = "给指定用户灌入全图鉴宝可梦"

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            type=str,
            default="mianyinsheli",
            help="目标用户名（默认 mianyinsheli）",
        )

    def handle(self, *args, **options):
        username = options["username"]
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ 用户 {username} 不存在，请先创建"))
            return

        trainer, created = Trainer.objects.get_or_create(user=user, defaults={"name": username})
        if not created and trainer.name != username:
            trainer.name = username
            trainer.save()

        self.stdout.write(f"训练师: {trainer.name} (新创建: {created})")

        all_species = Pokemon.objects.all()
        total = all_species.count()
        self.stdout.write(f"图鉴总数: {total}")

        created_count = 0
        for species in all_species:
            _, is_new = OwnedPokemon.objects.get_or_create(
                trainer=trainer,
                species=species,
                defaults={
                    "level": 50,
                    "current_hp": species.base_hp or 50,
                    "exp": 0,
                    "is_active": True,
                    "nickname": species.name,
                },
            )
            if is_new:
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(f"✅ 完成！新增 {created_count} 只，训练师共拥有 {trainer.owned_pokemons.count()} 只")
        )
