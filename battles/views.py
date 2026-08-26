# battles/views.py
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from trainers.models import OwnedPokemon
import random

def start_battle(request, wild_pokemon_id):
    """遭遇野生宝可梦，初始化战斗"""
    wild = OwnedPokemon.objects.get(id=wild_pokemon_id)

    # 获取当前用户的训练家
    if not hasattr(request.user, 'trainer'):
        return HttpResponse("你的账号没有关联训练师")
    player_pokemon = request.user.trainer.pokemons.filter(is_active=True).first()
    if not player_pokemon:
        return HttpResponse("你没有活跃的宝可梦")

    # 把战斗状态存进 session
    request.session['battle'] = {
        'player_pokemon_id': player_pokemon.id,
        'wild_pokemon_id': wild.id,
        'player_hp': player_pokemon.current_hp,
        'wild_hp': wild.current_hp,
        'player_max_hp': player_pokemon.current_hp,  # ← 新增：记录满血值
        'wild_max_hp': wild.current_hp,              # ← 新增：记录满血值
        'turn': 'player',
        'status': 'ongoing',                          # ← 新增：初始状态
        'log': [f"遭遇了野生的 {wild.species.name}！"],
    }
    return redirect('battle_view')


def battle_view(request):
    """战斗页面"""
    battle = request.session.get('battle')
    if not battle:
        return redirect('home')

    player_pokemon = OwnedPokemon.objects.get(id=battle['player_pokemon_id'])
    wild_pokemon = OwnedPokemon.objects.get(id=battle['wild_pokemon_id'])

    return render(request, 'battles/battle.html', {
        'battle': battle,
        'player_pokemon': player_pokemon,
        'wild_pokemon': wild_pokemon,
    })


@require_POST
def use_move(request, move_id):
    """使用技能（AJAX 调用）"""
    battle = request.session.get('battle')

    # 防御：session 不存在
    if not battle:
        return JsonResponse({'error': '战斗已结束或不存在'}, status=400)

    # 防御：战斗已经结束了
    if battle.get('status') != 'ongoing':
        return JsonResponse({'error': '战斗已结束'}, status=400)

    try:
        player = OwnedPokemon.objects.get(id=battle['player_pokemon_id'])
        wild = OwnedPokemon.objects.get(id=battle['wild_pokemon_id'])
        move = player.moves.get(id=move_id)  # 如果技能不属于这只宝可梦会抛异常
    except OwnedPokemon.DoesNotExist:
        return JsonResponse({'error': '宝可梦数据异常'}, status=400)
    except Exception:
        return JsonResponse({'error': '技能不存在'}, status=400)

    log = []

    # 玩家攻击
    damage = move.power + player.level * 2
    battle['wild_hp'] = max(0, battle['wild_hp'] - damage)
    log.append(f"{player.species.name} 使用了 {move.name}！造成 {damage} 点伤害！")

    # 检查野生宝可梦是否倒下
    if battle['wild_hp'] <= 0:
        log.append(f"野生 {wild.species.name} 倒下了！获得经验值！")
        battle['status'] = 'won'
        request.session['battle'] = battle
        return JsonResponse({
            'log': log,
            'player_hp': battle['player_hp'],   # ← 补上！之前漏了
            'wild_hp': 0,
            'status': 'won'
        })

    # 野生宝可梦反击（简单AI）
    wild_damage = wild.species.base_attack + wild.level
    battle['player_hp'] = max(0, battle['player_hp'] - wild_damage)
    log.append(f"野生 {wild.species.name} 反击了！造成 {wild_damage} 点伤害！")

    if battle['player_hp'] <= 0:
        log.append(f"{player.species.name} 倒下了！战斗失败...")
        battle['status'] = 'lost'

    request.session.modified = True
    request.session['battle'] = battle

    return JsonResponse({
        'log': log,
        'player_hp': battle['player_hp'],
        'wild_hp': battle['wild_hp'],
        'status': battle.get('status', 'ongoing'),
    })