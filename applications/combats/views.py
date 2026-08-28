import json
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Combat, Round
from applications.scoring.models import ScoreJuge
from applications.comptes.models import Utilisateur

@login_required
def table_juge_principal_vue(request):
    combat = Combat.objects.filter(statut__in=['EN_COURS', 'BROADCAST']).select_related('boxeur_rouge', 'boxeur_bleu', 'arbitre_central', 'evenement').first()
    if not combat:
        combat = Combat.objects.select_related('boxeur_rouge', 'boxeur_bleu', 'arbitre_central', 'evenement').first()

    juges = Utilisateur.objects.filter(role__code='JURY')
    rounds = combat.rounds.all().prefetch_related('scores_juges') if combat else []

    scores_par_round = []
    totaux_juges = {'rouge': 0, 'bleu': 0}

    for r in rounds:
        scores_list = list(r.scores_juges.all())
        scores_par_round.append({
            'round': r,
            'scores_juges': scores_list
        })
        if r.coin_gagnant_round == 'ROUGE':
            totaux_juges['rouge'] += 1
        elif r.coin_gagnant_round == 'BLEU':
            totaux_juges['bleu'] += 1

    context = {
        'combat': combat,
        'juges': juges,
        'scores_par_round': scores_par_round,
        'totaux_juges': totaux_juges,
    }
    return render(request, 'combats/table_juge_principal.html', context)

@login_required
def valider_round_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        action = data.get('action')
        round_id = data.get('round_id')

        if action == 'demarrer' and round_id:
            round_obj = Round.objects.get(id=round_id)
            round_obj.statut = 'EN_COURS'
            round_obj.save()
            
            combat = round_obj.combat
            if combat.statut != 'EN_COURS':
                combat.statut = 'EN_COURS'
                combat.save()
                
            return JsonResponse({'statut': 'succes', 'message': f'Round {round_obj.numero_round} démarré !'})

        elif (action in ['terminer', 'valider_round']) and round_id:
            round_obj = Round.objects.get(id=round_id)
            round_obj.statut = 'TERMINE'
            round_obj.valide = True
            calculer_score_round(round_obj)
            return JsonResponse({'statut': 'succes', 'message': f'Round {round_obj.numero_round} validé !'})

        elif action == 'cloturer_combat':
            combat_id = data.get('combat_id')
            if not combat_id and round_id:
                round_obj = Round.objects.get(id=round_id)
                combat_id = round_obj.combat_id

            combat = Combat.objects.get(id=combat_id)
            combat.statut = 'TERMINE'
            
            tot_rouge = 0
            tot_bleu = 0
            for r in combat.rounds.all():
                if r.coin_gagnant_round == 'ROUGE':
                    tot_rouge += 1
                elif r.coin_gagnant_round == 'BLEU':
                    tot_bleu += 1
            
            if tot_rouge > tot_bleu:
                combat.coin_vainqueur = 'ROUGE'
                combat.vainqueur = combat.boxeur_rouge
            elif tot_bleu > tot_rouge:
                combat.coin_vainqueur = 'BLEU'
                combat.vainqueur = combat.boxeur_bleu
            else:
                combat.coin_vainqueur = 'EGALITE'
            
            combat.save()
            return JsonResponse({'statut': 'succes', 'message': 'Combat terminé ! Vainqueur proclamé.'})

    return JsonResponse({'statut': 'erreur', 'message': 'Action invalide.'}, status=400)

def calculer_score_round(round_obj):
    scores = round_obj.scores_juges.all()
    if not scores:
        round_obj.save()
        return
    tot_r = sum(s.pts_rouge for s in scores)
    tot_b = sum(s.pts_bleu for s in scores)
    
    round_obj.total_score_rouge = tot_r
    round_obj.total_score_bleu = tot_b

    if tot_r > tot_b:
        round_obj.coin_gagnant_round = 'ROUGE'
    elif tot_b > tot_r:
        round_obj.coin_gagnant_round = 'BLEU'
    else:
        round_obj.coin_gagnant_round = 'EGALITE'
    round_obj.save()