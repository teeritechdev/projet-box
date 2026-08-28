import json
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from applications.combats.models import Combat, Round
from .models import ScoreJuge

@login_required
def tablette_juge_vue(request):
    combat = Combat.objects.filter(statut__in=['EN_COURS', 'BROADCAST']).select_related('boxeur_rouge', 'boxeur_bleu', 'evenement').first()
    if not combat:
        combat = Combat.objects.select_related('boxeur_rouge', 'boxeur_bleu', 'evenement').first()
    
    rounds = combat.rounds.all() if combat else []
    round_actif = combat.rounds.filter(statut='EN_COURS').first() if combat else None
    if not round_actif and combat:
        round_actif = combat.rounds.filter(statut='EN_ATTENTE').first()
    
    context = {
        'combat': combat,
        'rounds': rounds,
        'round_actif': round_actif,
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
            return JsonResponse({'statut': 'erreur', 'message': 'Données incompletas.'}, status=400)

        round_obj = Round.objects.get(id=round_id)
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