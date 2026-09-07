# pokedex/management/commands/translate_to_chinese.py
import time

import requests
from django.core.management.base import BaseCommand

from pokedex.models import Move, Pokemon, Type

TYPE_CN_MAP = {
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
    help = "从 PokeAPI 获取宝可梦和技能的中文名称"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="只查询不写入，用于调试",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="只处理前 N 条（0=全部）",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="打印每条记录的详细处理过程",
        )

    def handle(self, *args, **options):
        self.dry_run = options["dry_run"]
        self.limit = options["limit"]
        self.verbose = options["verbose"]

        if self.dry_run:
            self.stdout.write(self.style.WARNING("🔍 DRY-RUN 模式：不会写入数据库\n"))

        self._translate_types()
        self._translate_pokemon()
        self._translate_moves()

    def _fetch_with_retry(self, session, url, label):
        """带重试和详细错误分类的 HTTP 请求，返回 JSON dict 或 None"""
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = session.get(url, timeout=10)

                if resp.status_code == 404:
                    self.stdout.write(self.style.WARNING(f"  ⚠️ {label}: 404 资源不存在 ({url})"))
                    return None
                if resp.status_code == 429:
                    wait = RETRY_DELAY * attempt * 3
                    self.stdout.write(self.style.WARNING(f"  ⏳ {label}: 被限流(429)，等待 {wait}s 后重试..."))
                    time.sleep(wait)
                    continue
                if resp.status_code != 200:
                    self.stdout.write(self.style.WARNING(f"  ⚠️ {label}: HTTP {resp.status_code}（第{attempt}次）"))
                    if attempt < MAX_RETRIES:
                        time.sleep(RETRY_DELAY * attempt)
                        continue
                    return None

                try:
                    data = resp.json()
                except ValueError:
                    self.stdout.write(self.style.ERROR(f"  ❌ {label}: 响应不是合法 JSON"))
                    return None

                if not isinstance(data, dict):
                    self.stdout.write(self.style.ERROR(f"  ❌ {label}: 响应格式异常: {type(data).__name__}"))
                    return None

                return data

            except requests.exceptions.Timeout:
                self.stdout.write(self.style.WARNING(f"  ⏳ {label}: 请求超时（第{attempt}/{MAX_RETRIES}次）"))
            except requests.exceptions.ConnectionError:
                self.stdout.write(self.style.WARNING(f"  🔌 {label}: 连接失败（第{attempt}/{MAX_RETRIES}次）"))
            except requests.exceptions.RequestException as e:
                self.stdout.write(self.style.ERROR(f"  ❌ {label}: 网络异常: {e}"))
                return None

            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * attempt)

        self.stdout.write(self.style.ERROR(f"  ❌ {label}: 重试 {MAX_RETRIES} 次后放弃"))
        return None

    @staticmethod
    def _extract_zh_name(data):
        """从 PokeAPI 的 names 数组中提取 zh-Hans 名称，返回 str 或空字符串"""
        names = data.get("names")
        if not names or not isinstance(names, list):
            return ""
        for entry in names:
            if not isinstance(entry, dict):
                continue
            lang = entry.get("language")
            if isinstance(lang, dict) and lang.get("name", "").lower() == "zh-hans":
                return entry.get("name", "")
        return ""

    def _translate_types(self):
        """翻译属性名称（本地映射，不走 API）"""
        self.stdout.write("📌 翻译属性名称...")
        updated = 0
        for type_obj in Type.objects.all():
            cn_name = TYPE_CN_MAP.get(type_obj.name)
            if not cn_name or cn_name == type_obj.name:
                if self.verbose:
                    self.stdout.write(f"  [SKIP] {type_obj.name} — 无需翻译")
                continue
            if self.verbose:
                self.stdout.write(f"  [OK] {type_obj.name} → {cn_name}")
            if not self.dry_run:
                type_obj.name = cn_name
                type_obj.save(update_fields=["name"])
            updated += 1
        self.stdout.write(self.style.SUCCESS(f"✅ 属性翻译完成，更新了 {updated} 个"))

    def _translate_pokemon(self):
        """获取宝可梦中文名"""
        self.stdout.write("📌 翻译宝可梦名称...")
        qs = Pokemon.objects.all()
        if self.limit:
            qs = qs[: self.limit]
        total = len(qs) if self.limit else Pokemon.objects.count()
        updated = 0
        skipped = 0
        failed = 0
        session = requests.Session()

        for i, pokemon in enumerate(qs, 1):
            label = f"宝可梦#{pokemon.pokemon_id}({pokemon.name})"
            url = f"https://pokeapi.co/api/v2/pokemon-species/{pokemon.pokemon_id}/"

            if self.verbose:
                self.stdout.write(f"  [{i}/{total}] 请求: {url}")

            data = self._fetch_with_retry(session, url, label)

            if data is None:
                failed += 1
                continue

            cn_name = self._extract_zh_name(data)

            if not cn_name:
                self.stdout.write(self.style.WARNING(f"  ⚠️ {label}: API 返回中无 zh-Hans 名称"))
                if self.verbose:
                    available = [
                        e.get("language", {}).get("name", "?") for e in data.get("names", []) if isinstance(e, dict)
                    ]
                    self.stdout.write(f"     可用语言: {available}")
                skipped += 1
                continue

            if cn_name == pokemon.name:
                if self.verbose:
                    self.stdout.write(f"  [SKIP] {label}: 已经是 {cn_name}")
                skipped += 1
                continue

            if self.verbose:
                self.stdout.write(f"  [OK] {label}: {pokemon.name} → {cn_name}")

            if not self.dry_run:
                pokemon.name = cn_name
                pokemon.save(update_fields=["name"])
            updated += 1

            if i % 50 == 0:
                self.stdout.write(f"  进度: {i}/{total} | 更新 {updated} | 跳过 {skipped} | 失败 {failed}")
                time.sleep(0.5)

        self.stdout.write(
            self.style.SUCCESS(f"✅ 宝可梦翻译完成！共 {total} 只 | 更新 {updated} | 跳过 {skipped} | 失败 {failed}")
        )

    def _translate_moves(self):
        """获取技能中文名"""
        self.stdout.write("📌 翻译技能名称...")
        qs = Move.objects.all()
        if self.limit:
            qs = qs[: self.limit]
        total = len(qs) if self.limit else Move.objects.count()
        updated = 0
        skipped = 0
        failed = 0
        no_move_id = 0
        session = requests.Session()

        for i, move in enumerate(qs, 1):
            if not move.move_id:
                no_move_id += 1
                continue

            label = f"技能#{move.move_id}({move.name})"
            url = f"https://pokeapi.co/api/v2/move/{move.move_id}/"

            if self.verbose:
                self.stdout.write(f"  [{i}/{total}] 请求: {url}")

            data = self._fetch_with_retry(session, url, label)

            if data is None:
                failed += 1
                continue

            cn_name = self._extract_zh_name(data)

            if not cn_name:
                self.stdout.write(self.style.WARNING(f"  ⚠️ {label}: API 返回中无 zh-Hans 名称"))
                skipped += 1
                continue

            if cn_name == move.name:
                if self.verbose:
                    self.stdout.write(f"  [SKIP] {label}: 已经是 {cn_name}")
                skipped += 1
                continue

            if self.verbose:
                self.stdout.write(f"  [OK] {label}: {move.name} → {cn_name}")

            if not self.dry_run:
                move.name = cn_name
                move.save(update_fields=["name"])
            updated += 1

            if i % 50 == 0:
                self.stdout.write(f"  进度: {i}/{total} | 更新 {updated} | 跳过 {skipped} | 失败 {failed}")
                time.sleep(0.5)

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ 技能翻译完成！共 {total} 个 | 更新 {updated} | 跳过 {skipped} | 失败 {failed} | 无move_id {no_move_id}"
            )
        )
