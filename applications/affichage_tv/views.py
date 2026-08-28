from django.shortcuts import render
from django.http import JsonResponse
from applications.combats.models import Combat

def ecran_tv_broadcast_vue(request):
    return render(request, 'affichage_tv/ecran_broadcast.html')

def api_statut_broadcast(request):
    combat = Combat.objects.filter(statut__in=['EN_COURS', 'BROADCAST', 'TERMINE']).select_related('boxeur_rouge', 'boxeur_bleu', 'arbitre_central', 'evenement', 'categorie').order_by('-id').first()
    
    if not combat:
        return JsonResponse({'actif': False})

    rounds_data = []
    tot_rouge = 0
    tot_bleu = 0

    for r in combat.rounds.all():
        rounds_data.append({
            'numero': r.numero_round,
            'valide': r.valide,
            'gagnant': r.coin_gagnant_round
        })
        if r.coin_gagnant_round == 'ROUGE':
            tot_rouge += 1
        elif r.coin_gagnant_round == 'BLEU':
            tot_bleu += 1

    data = {
        'actif': True,
        'combat_id': combat.id,
        'evenement': combat.evenement.titre if combat.evenement else "CHAMPIONNAT DE BOXE",
        'categorie': combat.categorie.nom if combat.categorie else "TOUTES CATEGORIES",
        'arbitre_central': str(combat.arbitre_central) if combat.arbitre_central else "Arbitre Officiel",
        'statut_combat': combat.statut,
        'coin_vainqueur': combat.coin_vainqueur,
        'nom_vainqueur': str(combat.vainqueur) if combat.vainqueur else None,
        'boxeur_rouge': {
            'nom': str(combat.boxeur_rouge),
            'club': combat.boxeur_rouge.club,
            'pays': combat.boxeur_rouge.pays,
        },
        'boxeur_bleu': {
            'nom': str(combat.boxeur_bleu),
            'club': combat.boxeur_bleu.club,
            'pays': combat.boxeur_bleu.pays,
        },
        'total_rouge': tot_rouge,
        'total_bleu': tot_bleu,
        'type_decision': combat.get_type_decision_display() if combat.type_decision else "Décision Officielle",
        'rounds': rounds_data
    }

    return JsonResponse(data)