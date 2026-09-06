# pokedex/management/commands/fill_sprite_urls.py
from django.core.management.base import BaseCommand

from pokedex.models import Pokemon

POKEAPI_SPRITE_BASE = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{id}.png"


class Command(BaseCommand):
    help = "为所有宝可梦填充 PokeAPI 官方精灵图片 URL"

    def handle(self, *args, **options):
        updated = 0
        for pokemon in Pokemon.objects.all():
            url = POKEAPI_SPRITE_BASE.format(id=pokemon.pokemon_id)
            if pokemon.sprite_url != url:
                pokemon.sprite_url = url
                pokemon.save(update_fields=["sprite_url"])
                updated += 1

        total = Pokemon.objects.count()
        self.stdout.write(self.style.SUCCESS(f"✅ 完成！共 {total} 只，更新了 {updated} 只的 sprite_url"))
