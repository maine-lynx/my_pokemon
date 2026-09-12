# battles/views.py
import random

from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from items.models import TrainerItem
from pokedex.models import Pokemon
from trainers.models import OwnedPokemon

# ============================================================================
# 伤害计算工具函数（官方公式）
# ============================================================================


def calc_stat(base, level):
    """HP 以外的能力值公式：(2×种族值 + 5) × 等级 / 100 + 5"""
    return (2 * base + 5) * level // 100 + 5


def calc_hp(base, level):
    """HP 能力值公式：(2×种族值 + 5) × 等级 / 100 + 等级 + 10"""
    return (2 * base + 5) * level // 100 + level + 10


def get_type_effectiveness(move_type_id, defender_type_ids):
    """
    计算属性克制倍率（优化版：使用ID集合避免N+1查询）
    move_type_id: 技能的 Type ID（整数）
    defender_type_ids: 防御方所有 Type ID 的列表/集合
    返回: 0, 0.25, 0.5, 1, 2, 4
    """
    if not move_type_id or not defender_type_ids:
        return 1.0

    from pokedex.models import Type

    multiplier = 1.0
    for def_type_id in defender_type_ids:
        try:
            def_type = Type.objects.get(id=def_type_id)
        except Type.DoesNotExist:
            continue

        # 免疫（0x）
        if def_type.immune.filter(id=move_type_id).exists():
            multiplier *= 0
        # 被克制（2x）
        elif def_type.weak_against.filter(id=move_type_id).exists():
            multiplier *= 2
        # 抵抗（0.5x）
        elif def_type.resist.filter(id=move_type_id).exists():
            multiplier *= 0.5

    return multiplier


def calc_damage(
    attacker_level, attack_stat, defense_stat, move_power, move_type_id, attacker_type_ids, defender_type_ids
):
    """
    官方伤害公式（Gen3+）
    Damage = floor((2×L/5+2) × Power × A/D / 50) + 2
    再乘以 STAB × 属性克制 × 随机(0.85~1.0)
    """
    if move_power <= 0:
        return 0, False

    base_damage = ((2 * attacker_level // 5 + 2) * move_power * attack_stat // defense_stat) // 50 + 2

    # STAB：技能类型与攻击方任一属性相同
    stab = 1.5 if move_type_id in attacker_type_ids else 1.0
    effectiveness = get_type_effectiveness(move_type_id, defender_type_ids)
    random_factor = random.uniform(0.85, 1.0)

    damage = int(base_damage * stab * effectiveness * random_factor)
    is_super = effectiveness >= 2
    return max(1, damage), is_super


# ============================================================================
# 视图函数
# ============================================================================


def start_battle(request, wild_pokemon_id):
    try:
        wild_species = Pokemon.objects.get(pokemon_id=wild_pokemon_id)
    except Pokemon.DoesNotExist:
        return HttpResponse("野生宝可梦不存在")
    if not hasattr(request.user, "trainer"):
        return HttpResponse("你的账号没有关联训练师")
    player_pokemon = request.user.trainer.owned_pokemons.filter(is_active=True).first()
    if not player_pokemon:
        return HttpResponse("你没有活跃的宝可梦")

    wild_level = 5
    wild_max_hp = calc_hp(wild_species.base_hp, wild_level)

    battle_data = {
        "player_pokemon_id": player_pokemon.id,
        "player_name": player_pokemon.nickname or player_pokemon.species.name,
        "wild_species_id": wild_species.id,
        "wild_level": wild_level,
        "wild_name": wild_species.name,
        "player_hp": player_pokemon.current_hp,
        "wild_hp": wild_max_hp,
        "player_max_hp": player_pokemon.current_hp,
        "wild_max_hp": wild_max_hp,
        "turn": "player",
        "status": "ongoing",
        "log": [f"遭遇了野生的 {wild_species.name}！"],
    }

    request.session["battle"] = battle_data
    request.session.modified = True
    return redirect("battle_view")


def battle_view(request):
    battle = request.session.get("battle")
    if not battle or battle["status"] != "ongoing":
        species_ids = list(Pokemon.objects.values_list("pokemon_id", flat=True))
        if not species_ids:
            return redirect("home")
        wild_id = random.choice(species_ids)
        return redirect("start_battle", wild_pokemon_id=wild_id)

    player_pokemon = OwnedPokemon.objects.get(id=battle["player_pokemon_id"])
    wild_species = Pokemon.objects.get(id=battle["wild_species_id"])
    moves = player_pokemon.moves.all()

    trainer_items = []
    team = []
    if hasattr(request.user, "trainer"):
        trainer_items = TrainerItem.objects.filter(trainer=request.user.trainer, quantity__gt=0).select_related("item")
        team = (
            OwnedPokemon.objects.filter(trainer=request.user.trainer, is_active=True)
            .exclude(id=battle["player_pokemon_id"])
            .select_related("species")
        )
    return render(
        request,
        "battles/battle.html",
        {
            "battle": battle,
            "player_pokemon": player_pokemon,
            "wild_species": wild_species,
            "moves": moves,
            "trainer_items": trainer_items,
            "team": team,
        },
    )


# ... existing code ...


@require_POST
def switch_pokemon(request, pokemon_id):
    battle = request.session.get("battle")
    if not battle or battle.get("status") != "ongoing":
        return JsonResponse({"error": "战斗已结束或不存在"}, status=400)

    try:
        new_pokemon = OwnedPokemon.objects.get(id=pokemon_id, trainer=request.user.trainer, is_active=True)
    except OwnedPokemon.DoesNotExist:
        return JsonResponse({"error": "该宝可梦不属于你的队伍"}, status=400)

    if new_pokemon.current_hp <= 0:
        return JsonResponse({"error": "这只宝可梦已经倒下了，无法切换！"}, status=400)

    if new_pokemon.id == battle["player_pokemon_id"]:
        return JsonResponse({"error": "这只宝可梦已经在场上了！"}, status=400)

    log = []
    old_name = battle.get("player_name", "???")
    log.append(f"回来吧，{old_name}！")

    battle["player_pokemon_id"] = new_pokemon.id
    battle["player_hp"] = new_pokemon.current_hp
    battle["player_max_hp"] = new_pokemon.current_hp
    battle["player_name"] = new_pokemon.nickname or new_pokemon.species.name
    log.append(f"去吧，{battle['player_name']}！")

    wild = Pokemon.objects.get(id=battle["wild_species_id"])
    wild_atk = calc_stat(wild.base_attack, battle["wild_level"])
    player_def = calc_stat(new_pokemon.species.base_defense, new_pokemon.level)

    # 获取野生宝可梦的第一个类型的ID
    wild_first_type = wild.type.first()
    wild_type_id = wild_first_type.id if wild_first_type else None

    # 获取新宝可梦的所有类型ID列表
    new_pokemon_type_ids = list(new_pokemon.species.type.values_list("id", flat=True))

    wild_damage, _ = calc_damage(
        attacker_level=battle["wild_level"],
        attack_stat=wild_atk,
        defense_stat=player_def,
        move_power=40,
        move_type_id=wild_type_id,
        attacker_type_ids=list(wild.type.values_list("id", flat=True)),
        defender_type_ids=new_pokemon_type_ids,
    )
    battle["player_hp"] = max(0, battle["player_hp"] - wild_damage)
    log.append(f"野生 {wild.name} 趁机攻击！造成 {wild_damage} 点伤害！")

    if battle["player_hp"] <= 0:
        log.append(f"{battle['player_name']} 倒下了！")
        battle["status"] = "lost"

    request.session.modified = True
    request.session["battle"] = battle

    # 获取新宝可梦的技能列表
    new_moves = list(new_pokemon.moves.values("id", "name", "power"))

    # 获取更新后的队伍列表（排除当前在场宝可梦）
    team_list = []
    if hasattr(request.user, "trainer"):
        team_qs = (
            OwnedPokemon.objects.filter(trainer=request.user.trainer, is_active=True)
            .exclude(id=new_pokemon.id)
            .select_related("species")
        )
        for op in team_qs:
            team_list.append(
                {
                    "id": op.id,
                    "name": op.species.name,
                    "level": op.level,
                    "current_hp": op.current_hp,
                    "sprite_url": op.species.sprite_url,
                    "fainted": op.current_hp <= 0,
                }
            )

    return JsonResponse(
        {
            "log": log,
            "player_hp": battle["player_hp"],
            "player_max_hp": battle["player_max_hp"],
            "wild_hp": battle["wild_hp"],
            "status": battle.get("status", "ongoing"),
            "new_name": battle["player_name"],
            "new_level": new_pokemon.level,
            "new_exp": new_pokemon.exp,
            "new_exp_to_next": new_pokemon.exp_to_next_level,
            "new_sprite_url": new_pokemon.species.sprite_url,
            "moves": new_moves,
            "team": team_list,
        }
    )


@require_POST
def use_move(request, move_id):
    battle = request.session.get("battle")

    if not battle:
        return JsonResponse({"error": "战斗已结束或不存在"}, status=400)

    if battle.get("status") != "ongoing":
        return JsonResponse({"error": "战斗已结束"}, status=400)

    try:
        player = OwnedPokemon.objects.get(id=battle["player_pokemon_id"])
        wild = Pokemon.objects.get(id=battle["wild_species_id"])
        move = player.moves.get(id=move_id)
    except OwnedPokemon.DoesNotExist:
        return JsonResponse({"error": "宝可梦数据异常"}, status=400)
    except Exception:
        return JsonResponse({"error": "技能不存在"}, status=400)

    log = []

    # ---- 玩家攻击（官方公式）----
    if move.power <= 0:
        damage = 0
        log.append(f"{player.species.name} 使用了 {move.name}！但是没有效果...")
    else:
        player_atk = calc_stat(player.species.base_attack, player.level)
        wild_def = calc_stat(wild.base_defense, battle["wild_level"])

        # 获取类型ID列表
        move_type_id = move.type.id if move.type else None
        attacker_type_ids = list(player.species.type.values_list("id", flat=True))
        defender_type_ids = list(wild.type.values_list("id", flat=True))

        damage, is_super = calc_damage(
            attacker_level=player.level,
            attack_stat=player_atk,
            defense_stat=wild_def,
            move_power=move.power,
            move_type_id=move_type_id,
            attacker_type_ids=attacker_type_ids,
            defender_type_ids=defender_type_ids,
        )
        msg = f"{player.species.name} 使用了 {move.name}！造成 {damage} 点伤害！"
        if is_super:
            msg += " 效果拔群！"
        log.append(msg)

    battle["wild_hp"] = max(0, battle["wild_hp"] - damage)

    if battle["wild_hp"] <= 0:
        log.append(f"野生 {wild.name} 倒下了！获得经验值！")
        wild_level = battle["wild_level"]
        exp_gain = wild_level * 10
        player.exp += exp_gain
        log.append(f"{player.species.name} 获得了 {exp_gain} 点经验！")

        while player.exp >= player.exp_to_next_level:
            player.level += 1
            player.exp -= player.exp_to_next_level
            player.exp_to_next_level = int(player.exp_to_next_level * 1.5)
            player.current_hp += 10
            log.append(f"🎉 {player.species.name} 升到了 {player.level} 级！")

        player.save()
        battle["status"] = "won"
        request.session["battle"] = battle
        return JsonResponse(
            {
                "log": log,
                "player_hp": battle["player_hp"],
                "wild_hp": 0,
                "status": "won",
                "player_exp": player.exp,
                "exp_to_next": player.exp_to_next_level,
                "player_level": player.level,
            }
        )

    # ---- 野生宝可梦反击（官方公式）----
    wild_atk = calc_stat(wild.base_attack, battle["wild_level"])
    player_def = calc_stat(player.species.base_defense, player.level)

    # 获取野生宝可梦的类型ID
    wild_first_type = wild.type.first()
    wild_type_id = wild_first_type.id if wild_first_type else None
    wild_type_ids = list(wild.type.values_list("id", flat=True))
    player_type_ids = list(player.species.type.values_list("id", flat=True))

    wild_damage, wild_is_super = calc_damage(
        attacker_level=battle["wild_level"],
        attack_stat=wild_atk,
        defense_stat=player_def,
        move_power=40,
        move_type_id=wild_type_id,
        attacker_type_ids=wild_type_ids,
        defender_type_ids=player_type_ids,
    )
    battle["player_hp"] = max(0, battle["player_hp"] - wild_damage)
    msg = f"野生 {wild.name} 反击了！造成 {wild_damage} 点伤害！"
    if wild_is_super:
        msg += " 效果拔群！"
    log.append(msg)

    if battle["player_hp"] <= 0:
        log.append(f"{player.species.name} 倒下了！战斗失败...")
        battle["status"] = "lost"

    request.session.modified = True
    request.session["battle"] = battle

    return JsonResponse(
        {
            "log": log,
            "player_hp": battle["player_hp"],
            "wild_hp": battle["wild_hp"],
            "status": battle.get("status", "ongoing"),
        }
    )
