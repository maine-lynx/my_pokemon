from django.contrib.auth.decorators import login_required
from django.shortcuts import HttpResponse, redirect, render

from trainers.models import OwnedPokemon, Trainer


# Create your views here.
def trainer_profile(request):
    return HttpResponse("这是一个训练家页面")


def home(request):
    return render(request, "home.html")


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

        # 更新队伍
        trainer.owned_pokemons.update(is_active=False)
        trainer.owned_pokemons.filter(id__in=selected_ids).update(is_active=True)

        first_op = trainer.owned_pokemons.filter(id=selected_ids[0]).select_related("species").first()
        return redirect(f"/battles/{first_op.species.id}/")

    owned_pokemons = OwnedPokemon.objects.filter(trainer=trainer).select_related("species")
    return render(request, "new_game.html", {"owned_pokemons": owned_pokemons})
