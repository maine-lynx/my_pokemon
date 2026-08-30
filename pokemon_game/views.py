from django.shortcuts import render
from pokedex.models import Pokemon
from trainers.models import Trainer, OwnedPokemon


def home(request):
    """游戏首页"""
    return render(request, 'pokemon_game/home.html')


def new_game(request):
    """选择宝可梦页面"""
    # 情况1：如果已登录且该用户有训练师，显示他拥有的宝可梦
    if request.user.is_authenticated:
        trainer = Trainer.objects.filter(user=request.user).first()
        if trainer:
            owned = OwnedPokemon.objects.filter(trainer=trainer).select_related('species')
            if owned.exists():
                return render(request, 'pokemon_game/new_game.html', {
                    'owned_pokemons': owned,
                })

    # 情况2：没登录 / 没训练师数据 → 回退显示图鉴前三只（保证页面不报错）
    starters = Pokemon.objects.filter(id__in=[1, 4, 7])
    return render(request, 'pokemon_game/new_game.html', {
        'starters': starters,
    })