# battles/views.py
import random

from django.shortcuts import render, redirect
#render：读取一个HTML模板文件，将变量填进去，返回给浏览器
#redirect:重定向，去访问另一个url
from django.http import JsonResponse, HttpResponse
#JsonResponse：类比json.dumps()+设置Content-Type为application/json
#把字典转化成json字符串，前端JS收到后可直接response。json（）解析
#HttpResponse：返回一个纯文本字符串
from django.views.decorators.http import require_POST
#require_POST:类比装饰器，相当于if require.method != "POST":return error
from pokedex.models import Pokemon
from trainers.models import OwnedPokemon

#一个接受请求对象，返回响应对象的函数
def start_battle(request, wild_pokemon_id):
    """
    :param request:装了浏览器所有的信息（Cookie、用户、表单等）
        request.user    当前登录对象
        request.session：    服务器为每个用户单独维护的字典（跨请求保留）
    :param wild_pokemon_id:url中的那个数字
    :return:
    初始化一场战斗，把状态存到session里，然后初始化一场战斗
    """
    try:
        #获取属性
        wild_species = Pokemon.objects.get(id=wild_pokemon_id)
    except Pokemon.DoesNotExist:
        return HttpResponse("野生宝可梦不存在")
    # 检查当前用户有没有绑定训练师
    #类比if not user.trainer:return error
    if not hasattr(request.user, 'trainer'):
        return HttpResponse("你的账号没有关联训练师")
    #.filter:类比列表推导式[p for p in pokemons if p.is_active]
    #.first():取第一个
    player_pokemon = request.user.trainer.pokemons.filter(is_active=True).first()
    if not player_pokemon:
        return HttpResponse("你没有活跃的宝可梦")
    #动态生成野生宝可梦战斗属性
    wild_level = 5
    wild_hp = wild_species.base_hp+wild_level*2 #示例公式
    # 把战斗状态存进 session，类比全局字典
    # django自动序列化存到数据库，下次请求还能取出来
    battle_data = {
        'player_pokemon_id': player_pokemon.id,#只存储id，对象没法序列化
        'wild_species_id': wild_species.id,
        'wild_level': wild_level,
        'wild_name': wild_species.name,
        'player_hp': player_pokemon.current_hp,
        'wild_hp': wild_hp,
        'player_max_hp': player_pokemon.current_hp,
        'wild_max_hp': wild_hp,
        'turn': 'player',
        'status': 'ongoing',
        'log': [f"遭遇了野生的 {wild_species.name}！"],
    }

    # ✅ 关键修改：直接赋值给 session 键，并标记修改
    request.session['battle'] = battle_data
    request.session.modified = True
    #重定向，去访问battle_view
    return redirect('battle_view')


def battle_view(request):
    """战斗页面
    类比理解：
        从session中读取战斗数据
        从数据库中从新查找完整对象（session只存了id）
        把数据填充到HTML模板，返回给浏览器
    """
    #从session中获取数据
    battle = request.session.get('battle')
    #第一场战斗开始，或者上一场战斗结束
    if not battle or battle['status'] != 'ongoing':
        #随机挑选一直宝可梦重新开始
        species_ids= list(Pokemon.objects.values_list('id', flat=True))
        if not species_ids:
            return redirect("home")
        wild_id = random.choice(species_ids)
        return redirect("start_battle", wild_pokemon_id=wild_id)

    #战斗进行中，正常渲染
    player_pokemon = OwnedPokemon.objects.get(id=battle['player_pokemon_id'])
    wild_species = Pokemon.objects.get(id=battle['wild_species_id'])
    #render类比：
    #   html = template.render（参数）
    #   return html
    return render(request, 'battles/battle.html', {
        'battle': battle,
        'player_pokemon': player_pokemon,
        'wild_species': wild_species,
    })


@require_POST
def use_move(request, move_id):
    """
    使用技能（AJAX接口，给前端调用的）
    类比理解：
        这是一个API接口，不是给人看的
        前端JS调用：fetch（”/battles/move/1“，{method：”POST“}）
        这个函数计算伤害，放回json，前端JS拿到后更新页面血条和日志
    """
    battle = request.session.get('battle')

    # 防御：session 不存在
    if not battle:
        return JsonResponse({'error': '战斗已结束或不存在'}, status=400)

    # 防御：战斗已经结束了
    if battle.get('status') != 'ongoing':
        return JsonResponse({'error': '战斗已结束'}, status=400)

    try:
        player = OwnedPokemon.objects.get(id=battle['player_pokemon_id'])
        wild = Pokemon.objects.get(id=battle['wild_species_id'])
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
        log.append(f"野生 {wild.name} 倒下了！获得经验值！")
        battle['status'] = 'won'
        request.session['battle'] = battle  #写回session
        return JsonResponse({
            'log': log,
            'player_hp': battle['player_hp'],   # ← 补上！之前漏了
            'wild_hp': 0,
            'status': 'won'
        })

    # 野生宝可梦反击（简单AI）
    wild_damage = wild.base_attack + battle["wild_level"]
    battle['player_hp'] = max(0, battle['player_hp'] - wild_damage)
    log.append(f"野生 {wild.name} 反击了！造成 {wild_damage} 点伤害！")

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