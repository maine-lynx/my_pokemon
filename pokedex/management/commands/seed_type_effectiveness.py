from django.core.management.base import BaseCommand

from pokedex.models import Type

# 克制关系：该属性对哪些属性造成 2x 伤害
SUPER_EFFECTIVE = {
    "一般": [],
    "火": ["草", "冰", "虫", "钢"],
    "水": ["火", "地面", "岩石"],
    "电": ["水", "飞行"],
    "草": ["水", "地面", "岩石"],
    "格斗": ["一般", "冰", "岩石", "恶", "钢"],
    "毒": ["草", "妖精"],
    "地面": ["火", "电", "毒", "岩石", "钢"],
    "飞行": ["草", "格斗", "虫"],
    "超能力": ["格斗", "毒"],
    "虫": ["草", "超能力", "恶"],
    "岩石": ["火", "冰", "飞行", "虫"],
    "幽灵": ["超能力", "幽灵"],
    "龙": ["龙"],
    "恶": ["超能力", "幽灵"],
    "钢": ["冰", "岩石", "妖精"],
    "冰": ["草", "地面", "飞行", "龙"],
    "妖精": ["格斗", "龙", "恶"],
}

# 抵抗关系：该属性受到哪些属性的攻击时只受 0.5x 伤害
RESIST = {
    "一般": [],
    "火": ["火", "草", "冰", "虫", "钢", "妖精"],
    "水": ["火", "水", "冰", "钢"],
    "电": ["电", "飞行", "钢"],
    "草": ["水", "电", "草", "地面"],
    "格斗": ["虫", "岩石", "恶"],
    "毒": ["草", "格斗", "毒", "虫", "妖精"],
    "地面": ["毒", "岩石"],
    "飞行": ["草", "格斗", "虫"],
    "超能力": ["格斗", "超能力"],
    "虫": ["草", "格斗", "地面"],
    "岩石": ["一般", "火", "毒", "飞行"],
    "幽灵": ["毒", "虫"],
    "龙": ["火", "水", "电", "草"],
    "恶": ["幽灵", "恶"],
    "钢": ["一般", "草", "冰", "飞行", "超能力", "虫", "岩石", "龙", "钢", "妖精"],
    "冰": ["冰"],
    "妖精": ["格斗", "虫", "恶"],
}

# 免疫关系：该属性受到哪些属性的攻击时不受伤害（0x）
IMMUNE = {
    "一般": ["幽灵"],
    "火": [],
    "水": [],
    "电": [],
    "草": [],
    "格斗": [],
    "毒": [],
    "地面": ["电"],
    "飞行": ["地面"],
    "超能力": [],
    "虫": [],
    "岩石": [],
    "幽灵": ["一般", "格斗"],
    "龙": [],
    "恶": ["超能力"],
    "钢": ["毒"],
    "冰": [],
    "妖精": ["龙"],
}


class Command(BaseCommand):
    help = "填充属性克制、抵抗、免疫关系"

    def handle(self, *args, **options):
        type_objs = {t.name: t for t in Type.objects.all()}

        all_names = set(SUPER_EFFECTIVE) | set(RESIST) | set(IMMUNE)
        missing = [n for n in all_names if n not in type_objs]
        if missing:
            self.stdout.write(self.style.WARNING(f"⚠️ 以下属性不存在，请先运行 translate_to_chinese：{missing}"))
            return

        # 先清空旧数据，避免重复
        for t in Type.objects.all():
            t.strong_against.clear()
            t.resist.clear()
            t.immune.clear()

        for type_name, targets in SUPER_EFFECTIVE.items():
            attacker = type_objs[type_name]
            for target in targets:
                attacker.strong_against.add(type_objs[target])

        for type_name, targets in RESIST.items():
            defender = type_objs[type_name]
            for target in targets:
                defender.resist.add(type_objs[target])

        for type_name, targets in IMMUNE.items():
            defender = type_objs[type_name]
            for target in targets:
                defender.immune.add(type_objs[target])

        self.stdout.write(self.style.SUCCESS("✅ 属性关系填充完成！"))

        for type_name in SUPER_EFFECTIVE:
            t = type_objs[type_name]
            strong = [d.name for d in t.strong_against.all()]
            weak = [a.name for a in t.weak_against.all()]
            resist = [d.name for d in t.resist.all()]
            resisted_by = [a.name for a in t.resisted_by.all()]
            immune = [d.name for d in t.immune.all()]
            immune_by = [a.name for a in t.immune_by.all()]
            self.stdout.write(f"  {type_name:6s}")
            self.stdout.write(f"    克制: {strong}")
            self.stdout.write(f"    被克制: {weak}")
            self.stdout.write(f"    抵抗: {resist}")
            self.stdout.write(f"    被抵抗: {resisted_by}")
            self.stdout.write(f"    免疫: {immune}")
            self.stdout.write(f"    被免疫: {immune_by}")
