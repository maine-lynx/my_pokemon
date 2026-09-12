import time

import requests
from django.core.management.base import BaseCommand

from pokedex.models import Pokemon, Type

POKEAPI_BASE = "https://pokeapi.co/api/v2"

CN_TYPE_MAP = {
    "normal": "一般",
    "fighting": "格斗",
    "flying": "飞行",
    "poison": "毒",
    "ground": "地面",
    "rock": "岩石",
    "bug": "虫",
    "ghost": "幽灵",
    "steel": "钢",
    "fire": "火",
    "water": "水",
    "grass": "草",
    "electric": "电",
    "psychic": "超能力",
    "ice": "冰",
    "dragon": "龙",
    "dark": "恶",
    "fairy": "妖精",
}

MAX_RETRIES = 3
RETRY_DELAY = 2


class Command(BaseCommand):
    help = "从 PokeAPI 获取并导入宝可梦类型数据"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="只查询不写入")
        parser.add_argument("--limit", type=int, default=0, help="只处理前 N 只（0=全部）")

    def _fetch_with_retry(self, session, url, label):
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = session.get(url, timeout=15)
                if resp.status_code == 429:
                    wait = RETRY_DELAY * attempt * 3
                    self.stdout.write(f"  ⏳ {label}: 限流，等待 {wait}s...")
                    time.sleep(wait)
                    continue
                if resp.status_code != 200:
                    if attempt < MAX_RETRIES:
                        time.sleep(RETRY_DELAY * attempt)
                        continue
                    return None
                return resp.json()
            except requests.RequestException as e:
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY * attempt)
                else:
                    self.stdout.write(self.style.WARNING(f"  ❌ {label}: {e}"))
                    return None
        return None

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        limit = options["limit"]

        if dry_run:
            self.stdout.write(self.style.WARNING("🔍 DRY-RUN 模式\n"))

        # 建立 Type 映射（英文名 -> Type 对象）
        type_objs = {}
        for en_name, cn_name in CN_TYPE_MAP.items():
            t = Type.objects.filter(name=cn_name).first()
            if t:
                type_objs[en_name] = t
            else:
                self.stdout.write(self.style.WARNING(f"  ⚠️ 类型 '{cn_name}' 不存在"))

        self.stdout.write(f"  找到 {len(type_objs)} 个类型对象")

        # 获取所有宝可梦
        qs = Pokemon.objects.all().order_by("pokemon_id")
        if limit:
            qs = qs[:limit]
        total = qs.count()
        self.stdout.write(f"📌 开始处理 {total} 只宝可梦...")

        assigned = 0
        skipped = 0
        failed = 0
        session = requests.Session()

        for i, pokemon in enumerate(qs, 1):
            pid = pokemon.pokemon_id
            label = f"#{pid} {pokemon.name}"

            url = f"{POKEAPI_BASE}/pokemon/{pid}/"
            data = self._fetch_with_retry(session, url, label)

            if not data:
                failed += 1
                continue

            types_data = data.get("types", [])
            if not types_data:
                skipped += 1
                continue

            # 按 slot 排序，slot 1 是主属性
            types_data.sort(key=lambda x: x.get("slot", 1))

            types_to_add = []
            for entry in types_data:
                type_info = entry.get("type", {})
                en_name = type_info.get("name", "")
                if en_name in type_objs:
                    types_to_add.append(type_objs[en_name])

            if not types_to_add:
                skipped += 1
                continue

            if not dry_run:
                pokemon.type.clear()
                for t in types_to_add:
                    pokemon.type.add(t)

            assigned += 1

            if i % 50 == 0:
                self.stdout.write(f"  进度: {i}/{total} | 已分配 {assigned} | 跳过 {skipped} | 失败 {failed}")
                time.sleep(0.5)

        self.stdout.write(
            self.style.SUCCESS(f"✅ 完成！共 {total} 只 | 分配 {assigned} | 跳过 {skipped} | 失败 {failed}")
        )

        # 验证
        self.stdout.write("\n=== 验证 ===")
        for p in Pokemon.objects.filter(type__isnull=False).order_by("pokemon_id")[:10]:
            types = [t.name for t in p.type.all()]
            self.stdout.write(f"  {p.name} (#{p.pokemon_id}): {types}")

        no_type = Pokemon.objects.filter(type__isnull=True).count()
        self.stdout.write(f"\n  有类型: {total - no_type} / {total}")
        if no_type > 0:
            self.stdout.write(self.style.WARNING(f"  ⚠️ {no_type} 只宝可梦没有类型"))
