# pokedex/management/commands/import_from_csv.py
import csv
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from pokedex.models import Type, Move, Pokemon, PokemonMove


def prettify(identifier):
    """thunder-shock → Thunder Shock"""
    return ' '.join(word.capitalize() for word in identifier.split('-'))


class Command(BaseCommand):
    help = '从 PokéAPI 的 CSV 文件批量导入图鉴数据'

    def handle(self, *args, **options):
        # ========== 1. 预创建属性（Type）==========
        type_mapping = {
            1: 'normal', 2: 'fighting', 3: 'flying', 4: 'poison',
            5: 'ground', 6: 'rock', 7: 'bug', 8: 'ghost', 9: 'steel',
            10: 'fire', 11: 'water', 12: 'grass', 13: 'electric',
            14: 'psychic', 15: 'ice', 16: 'dragon', 17: 'dark', 18: 'fairy'
        }
        self.stdout.write('📌 创建属性（Type）...')
        type_objs = {}
        for tid, tname in type_mapping.items():
            t, created = Type.objects.get_or_create(name=tname)
            type_objs[tid] = t
        self.stdout.write(self.style.SUCCESS(f'✅ 属性就绪，共 {len(type_objs)} 个'))

        # ========== 2. 导入技能（Move）==========
        moves_path = os.path.join(settings.BASE_DIR, 'data', 'moves.csv')
        self.stdout.write('📌 导入技能（Move）...')
        moves = []
        with open(moves_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                tid = int(row.get('type_id') or 10)
                moves.append(Move(
                    move_id=int(row['id']),
                    name=prettify(row['identifier']),
                    type=type_objs.get(tid, type_objs[10]),
                    power=int(row.get('power') or 0),
                    accuracy=int(row.get('accuracy') or 100),
                    pp=int(row.get('pp') or 10),
                    priority=int(row.get('priority') or 0),
                    damage_class=int(row.get('damage_class_id') or 2),
                    generation_id=int(row.get('generation_id') or 1),
                ))
        Move.objects.bulk_create(moves, ignore_conflicts=True)
        self.stdout.write(self.style.SUCCESS(f'✅ 导入 {len(moves)} 个技能'))

        # ========== 3. 导入宝可梦（Pokemon）==========
        pokemon_path = os.path.join(settings.BASE_DIR, 'data', 'pokemon.csv')
        self.stdout.write('📌 导入宝可梦（Pokemon）...')
        pokemons = []
        with open(pokemon_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                pokemons.append(Pokemon(
                    pokemon_id=int(row['id']),
                    species_id=int(row.get('species_id') or 0),
                    name=prettify(row['identifier']),
                    height=int(row.get('height') or 0),
                    weight=int(row.get('weight') or 0),
                    base_experience=int(row.get('base_experience') or 0),
                    base_hp=50,
                    base_attack=50,
                    base_defense=50,
                    base_speed=50,
                ))
        Pokemon.objects.bulk_create(pokemons, ignore_conflicts=True)
        self.stdout.write(self.style.SUCCESS(f'✅ 导入 {len(pokemons)} 只宝可梦'))

        # ========== 建 ID 映射（避免循环查库）==========
        self.stdout.write('📌 建立 ID 映射...')
        pokemon_map = {p.pokemon_id: p.id for p in Pokemon.objects.all()}
        move_map = {m.move_id: m.id for m in Move.objects.all()}
        self.stdout.write(self.style.SUCCESS(f'✅ 映射就绪'))

        # ========== 4. 建立技能关联（PokemonMove）==========
        pm_path = os.path.join(settings.BASE_DIR, 'data', 'pokemon_moves.csv')
        self.stdout.write('📌 建立技能关联（只取升级学会）...')

        relations = []
        count = 0

        with open(pm_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if int(row.get('pokemon_move_method_id') or 0) != 1:
                    continue
                pid = int(row['pokemon_id'])
                mid = int(row['move_id'])
                if pid not in pokemon_map or mid not in move_map:
                    continue
                relations.append(PokemonMove(
                    pokemon_id=pokemon_map[pid],
                    move_id=move_map[mid],
                    learn_level=int(row.get('level') or 1),
                ))
                count += 1

                if len(relations) >= 5000:
                    PokemonMove.objects.bulk_create(relations, ignore_conflicts=True)
                    relations = []

        if relations:
            PokemonMove.objects.bulk_create(relations, ignore_conflicts=True)

        self.stdout.write(self.style.SUCCESS(f'✅ 建立 {count} 条技能关联'))
        self.stdout.write(self.style.SUCCESS('🎉 全部导入完成！'))