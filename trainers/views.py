from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import HttpResponse, redirect, render

from pokedex.models import Pokemon
from trainers.models import OwnedPokemon, Trainer


def trainer_profile(request):
    return HttpResponse("这是一个训练家页面")


def home(request):
    if request.user.is_authenticated:
        return render(request, "home.html")
    return redirect("login")


def login_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    error = ""
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        from django.contrib.auth import authenticate

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect("home")
        error = "用户名或密码错误"

    return render(request, "trainers/login.html", {"error": error})


def register_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    error = ""
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        password2 = request.POST.get("password2", "")

        if not username or not password:
            error = "用户名和密码不能为空"
        elif password != password2:
            error = "两次密码不一致"
        elif User.objects.filter(username=username).exists():
            error = "用户名已存在"
        else:
            user = User.objects.create_user(username=username, password=password)
            _init_new_trainer(user)
            login(request, user)
            return redirect("home")

    return render(request, "trainers/register.html", {"error": error})


def _init_new_trainer(user):
    """注册时自动创建 Trainer 并赠送 3 只初始宝可梦（御三家）"""
    trainer, _ = Trainer.objects.get_or_create(
        user=user,
        defaults={"name": user.username, "region": "关都"},
    )

    starter_ids = [1, 4, 7]
    for pid in starter_ids:
        try:
            species = Pokemon.objects.get(pokemon_id=pid)
            OwnedPokemon.objects.get_or_create(
                trainer=trainer,
                species=species,
                defaults={
                    "level": 5,
                    "current_hp": species.base_hp or 50,
                    "exp": 0,
                    "is_active": True,
                },
            )
        except Pokemon.DoesNotExist:
            pass


@login_required
def new_game(request):
    trainer = Trainer.objects.get(user=request.user)

    if request.method == "POST":
        selected_ids = request.POST.getlist("selected_pokemons")

        if not selected_ids:
            owned_pokemons = OwnedPokemon.objects.filter(trainer=trainer).select_related("species")
            return render(
                request, "new_game.html", {"owned_pokemons": owned_pokemons, "error": "请至少选择一只宝可梦！"}
            )

        if len(selected_ids) > 6:
            owned_pokemons = OwnedPokemon.objects.filter(trainer=trainer).select_related("species")
            return render(
                request, "new_game.html", {"owned_pokemons": owned_pokemons, "error": "队伍最多只能带 6 只宝可梦！"}
            )

        trainer.owned_pokemons.update(is_active=False)
        trainer.owned_pokemons.filter(id__in=selected_ids).update(is_active=True)

        first_op = trainer.owned_pokemons.filter(id=selected_ids[0]).select_related("species").first()
        return redirect(f"/battles/{first_op.species.id}/")

    owned_pokemons = OwnedPokemon.objects.filter(trainer=trainer).select_related("species")
    return render(request, "new_game.html", {"owned_pokemons": owned_pokemons})
