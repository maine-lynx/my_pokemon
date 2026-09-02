from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from items.models import Item, TrainerItem


def bag_view(request):
    """背包页面：展示训练师拥有的所有道具"""
    if not hasattr(request.user, 'trainer'):
        return redirect('home')

    trainer = request.user.trainer
    trainer_items = TrainerItem.objects.filter(
        trainer=trainer, quantity__gt=0
    ).select_related('item')

    return render(request, 'items/bag.html', {
        'trainer': trainer,
        'trainer_items': trainer_items,
    })


@require_POST
def use_item(request, item_id):
    """
    战斗中使用道具（AJAX 接口）
    伤药：回复 HP
    精灵球：尝试捕捉野生宝可梦
    """
    battle = request.session.get('battle')
    if not battle or battle.get('status') != 'ongoing':
        return JsonResponse({'error': '当前无法使用道具'}, status=400)

    if not hasattr(request.user, 'trainer'):
        return JsonResponse({'error': '没有关联训练师'}, status=400)

    trainer = request.user.trainer

    try:
        trainer_item = TrainerItem.objects.get(
            trainer=trainer, item_id=item_id, quantity__gt=0
        )
    except TrainerItem.DoesNotExist:
        return JsonResponse({'error': '道具不存在或数量不足'}, status=400)

    item = trainer_item.item
    log = []

    if item.category == 'potion':
        from trainers.models import OwnedPokemon
        player = OwnedPokemon.objects.get(id=battle['player_pokemon_id'])
        max_hp = battle['player_max_hp']
        before = battle['player_hp']
        healed = min(item.effect_value, max_hp - before)
        battle['player_hp'] = before + healed
        player.current_hp = battle['player_hp']
        player.save()
        log.append(f"使用了 {item.name}！回复了 {healed} 点 HP！")

    elif item.category == 'pokeball':
        from pokedex.models import Pokemon
        from trainers.models import OwnedPokemon
        wild_species = Pokemon.objects.get(id=battle['wild_species_id'])
        wild_level = battle['wild_level']
        wild_hp = battle['wild_hp']
        wild_max_hp = battle['wild_max_hp']

        hp_ratio = wild_hp / wild_max_hp if wild_max_hp > 0 else 1
        catch_rate = max(5, int((1 - hp_ratio) * 60 + item.effect_value - wild_level))
        import random
        success = random.randint(1, 100) <= catch_rate

        if success:
            new_pokemon, created = OwnedPokemon.objects.get_or_create(
                trainer=trainer,
                species=wild_species,
                defaults={
                    'level': wild_level,
                    'current_hp': wild_hp,
                    'exp': 0,
                    'is_active': False,
                    'nickname': wild_species.name,
                }
            )
            if not created:
                new_pokemon.level = max(new_pokemon.level, wild_level)
                new_pokemon.save()

            battle['status'] = 'caught'
            battle['wild_hp'] = 0
            log.append(f"扔出了 {item.name}！... ... ...")
            log.append(f"✅ 成功捕获了野生 {wild_species.name}！")
        else:
            log.append(f"扔出了 {item.name}！... ... ...")
            log.append(f"❌ 野生 {wild_species.name} 挣脱了！")

            wild_damage = wild_species.base_attack + wild_level
            battle['player_hp'] = max(0, battle['player_hp'] - wild_damage)
            log.append(f"野生 {wild_species.name} 反击了！造成 {wild_damage} 点伤害！")

            if battle['player_hp'] <= 0:
                log.append(f"你的宝可梦倒下了！战斗失败...")
                battle['status'] = 'lost'

    else:
        return JsonResponse({'error': '该道具暂时无法使用'}, status=400)

    trainer_item.quantity -= 1
    trainer_item.save()

    request.session['battle'] = battle
    request.session.modified = True

    return JsonResponse({
        'log': log,
        'player_hp': battle['player_hp'],
        'wild_hp': battle['wild_hp'],
        'status': battle.get('status', 'ongoing'),
        'item_remaining': trainer_item.quantity,
    })