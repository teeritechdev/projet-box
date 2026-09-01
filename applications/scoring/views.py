import json
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from applications.combats.models import Combat, Round
from .models import ScoreJuge

@login_required
def tablette_juge_vue(request):
    combat_id = request.GET.get('combat_id')
    if combat_id:
        combat = Combat.objects.filter(id=combat_id).select_related('boxeur_rouge', 'boxeur_bleu', 'evenement', 'categorie').first()
    else:
        combat = Combat.objects.filter(statut='EN_COURS').select_related('boxeur_rouge', 'boxeur_bleu', 'evenement', 'categorie').first()
    
    if not combat:
        combat = Combat.objects.select_related('boxeur_rouge', 'boxeur_bleu', 'evenement', 'categorie').first()
    
    rounds = combat.rounds.all() if combat else []
    
    # Un round est actif sur la tablette SEULEMENT SI le combat est EN_COURS et le round est EN_COURS
    if combat and combat.statut == 'EN_COURS':
        round_actif = combat.rounds.filter(statut='EN_COURS').first()
    else:
        round_actif = None

    score_deja_soumis = False
    score_existant = None
    if round_actif:
        score_existant = ScoreJuge.objects.filter(round_combat=round_actif, juge=request.user).first()
        if score_existant:
            score_deja_soumis = True

    mes_scores_histoire = ScoreJuge.objects.filter(
        round_combat__combat=combat,
        juge=request.user
    ).select_related('round_combat').order_by('round_combat__numero_round') if combat else []

    context = {
        'combat': combat,
        'rounds': rounds,
        'round_actif': round_actif,
        'score_deja_soumis': score_deja_soumis,
        'score_existant': score_existant,
        'mes_scores_histoire': mes_scores_histoire,
        'juge': request.user,
    }
    return render(request, 'scoring/tablette_juge.html', context)


@login_required
def enregistrer_score_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        round_id = data.get('round_id')
        score_rouge = data.get('score_rouge') if data.get('score_rouge') is not None else data.get('points_rouge')
        score_bleu = data.get('score_bleu') if data.get('score_bleu') is not None else data.get('points_bleu')

        if not round_id or score_rouge is None or score_bleu is None:
            return JsonResponse({'statut': 'erreur', 'message': 'Données incomplètes.'}, status=400)

        round_obj = Round.objects.get(id=round_id)
        
        # Sécurité : Vérifier que le match n'est pas TERMINE et que le round est EN_COURS
        if round_obj.combat.statut == 'TERMINE':
            return JsonResponse({'statut': 'erreur', 'message': 'Ce match est officiellement terminé. Saisie impossible.'}, status=400)

        if round_obj.statut != 'EN_COURS':
            return JsonResponse({'statut': 'erreur', 'message': 'Ce round n\'est pas actif. Attendez que le Chef Juge le lance.'}, status=400)

        score_juge, created = ScoreJuge.objects.get_or_create(
            round_combat=round_obj,
            juge=request.user,
            defaults={'pts_rouge': score_rouge, 'pts_bleu': score_bleu}
        )

        if not created:
            score_juge.pts_rouge = score_rouge
            score_juge.pts_bleu = score_bleu
            score_juge.save()

        return JsonResponse({'statut': 'succes', 'message': 'Score enregistré avec succès !'})
    return JsonResponse({'statut': 'erreur', 'message': 'Requête invalide.'}, status=400)