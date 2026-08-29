import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from applications.combats.models import Combat, Evenement

def ecran_tv_broadcast_vue(request):
    return render(request, 'affichage_tv/ecran_broadcast.html')

def api_statut_broadcast(request):
    combat = Combat.objects.filter(statut__in=['EN_COURS', 'BROADCAST', 'A_VENIR', 'TERMINE']).select_related('boxeur_rouge', 'boxeur_bleu', 'arbitre_central', 'juge_principal', 'evenement', 'categorie').order_by('-id').first()
    
    if not combat:
        # Fallback si aucun combat
        evenement = Evenement.objects.filter(est_actif=True).first()
        return JsonResponse({
            'actif': False,
            'mode_tv': 'ATTENTE_PUB',
            'evenement': {
                'titre': evenement.titre if evenement else "JEUX DE L'ALLIANCE DES ÉTATS DU SAHEL (JAES) 2026",
                'nom_discipline': evenement.nom_discipline if evenement else "MIXED MARTIAL ARTS (MMA)",
                'edition': evenement.edition if evenement else "Ouagadougou 2026",
                'lieu': evenement.lieu if evenement else "Palais des Sports",
            },
            'prochains_combats': []
        })

    # Obtenir la liste des 5 prochains combats qui suivent
    prochains_qs = Combat.objects.filter(id__gt=combat.id).select_related('boxeur_rouge', 'boxeur_bleu', 'categorie').order_by('numero_match')[:5]
    if not prochains_qs.exists():
        prochains_qs = Combat.objects.exclude(id=combat.id).select_related('boxeur_rouge', 'boxeur_bleu', 'categorie').order_by('numero_match')[:5]

    prochains_combats = []
    for pc in prochains_qs:
        prochains_combats.append({
            'id': pc.id,
            'numero_match': pc.numero_match,
            'categorie': pc.categorie.nom if pc.categorie else "--",
            'rouge_nom': f"{pc.boxeur_rouge.prenom} {pc.boxeur_rouge.nom}",
            'rouge_pays': pc.boxeur_rouge.pays,
            'bleu_nom': f"{pc.boxeur_bleu.prenom} {pc.boxeur_bleu.nom}",
            'bleu_pays': pc.boxeur_bleu.pays,
        })

    rounds_data = []
    tot_rouge = 0
    tot_bleu = 0
    round_actif_num = 1

    for r in combat.rounds.all():
        rounds_data.append({
            'numero': r.numero_round,
            'statut': r.statut,
            'valide': r.valide,
            'gagnant': r.coin_gagnant_round,
            'score_rouge': r.total_score_rouge,
            'score_bleu': r.total_score_bleu,
        })
        if r.statut == 'EN_COURS':
            round_actif_num = r.numero_round
        if r.coin_gagnant_round == 'ROUGE':
            tot_rouge += 1
        elif r.coin_gagnant_round == 'BLEU':
            tot_bleu += 1

    # Juges de table
    juges_list = []
    for j in combat.juges.all():
        juges_list.append({
            'nom': f"{j.first_name} {j.last_name}" if (j.first_name or j.last_name) else j.username,
            'fonction': j.fonction or "Juge Officiel",
            'photo': j.photo.url if j.photo else None
        })

    arb = combat.arbitre_central
    jp = combat.juge_principal

    officiels_data = {
        'arbitre_central': {
            'nom': f"{arb.prenom} {arb.nom}" if arb else "Arbitre Ring Officiel",
            'pays': arb.pays if arb else "Burkina Faso",
            'photo': arb.photo.url if (arb and arb.photo) else None
        },
        'juge_principal': {
            'nom': f"{jp.first_name} {jp.last_name}" if (jp and (jp.first_name or jp.last_name)) else (jp.username if jp else "Chef Juge Superviseur"),
            'fonction': jp.fonction if (jp and jp.fonction) else "Juge Principal (Chef de Table)",
            'photo': jp.photo.url if (jp and jp.photo) else None
        },
        'juges_table': juges_list
    }

    ev = combat.evenement
    data = {
        'actif': True,
        'combat_id': combat.id,
        'mode_tv': combat.mode_tv or 'ATTENTE_PUB',
        'image_ring_bg': combat.image_ring_bg.url if combat.image_ring_bg else None,
        'audio_victoire': combat.audio_victoire.url if combat.audio_victoire else None,
        'numero_match': combat.numero_match,
        'evenement': {
            'titre': ev.titre if ev else "JAES 2026",
            'nom_discipline': ev.nom_discipline if ev else "MIXED MARTIAL ARTS (MMA)",
            'edition': ev.edition if ev else "Ouagadougou 2026",
            'lieu': ev.lieu if ev else "Palais des Sports",
            'organisateur': ev.organisateur if ev else "Ministère MSJE",
            'federation': ev.federation if ev else "CNP-MMA/DA",
            'logo_discipline': ev.logo_discipline.url if (ev and ev.logo_discipline) else None,
            'logo_evenement': ev.logo_evenement.url if (ev and ev.logo_evenement) else None,
            'logo_ministere': ev.logo_ministere.url if (ev and ev.logo_ministere) else None,
            'logo_aes': ev.logo_aes.url if (ev and ev.logo_aes) else None,
        },
        'categorie': combat.categorie.nom if combat.categorie else "Toutes Catégories",
        'statut_combat': combat.statut,
        'round_actif_num': round_actif_num,
        'coin_vainqueur': combat.coin_vainqueur,
        'nom_vainqueur': str(combat.vainqueur) if combat.vainqueur else None,
        'boxeur_rouge': {
            'nom': f"{combat.boxeur_rouge.prenom} {combat.boxeur_rouge.nom}",
            'surnom': combat.boxeur_rouge.surnom or "",
            'club': combat.boxeur_rouge.club,
            'pays': combat.boxeur_rouge.pays,
            'poids': float(combat.boxeur_rouge.poids_pesee) if combat.boxeur_rouge.poids_pesee else None,
            'taille': combat.boxeur_rouge.taille_cm,
            'age': combat.boxeur_rouge.age,
            'photo': combat.boxeur_rouge.photo.url if combat.boxeur_rouge.photo else None,
        },
        'boxeur_bleu': {
            'nom': f"{combat.boxeur_bleu.prenom} {combat.boxeur_bleu.nom}",
            'surnom': combat.boxeur_bleu.surnom or "",
            'club': combat.boxeur_bleu.club,
            'pays': combat.boxeur_bleu.pays,
            'poids': float(combat.boxeur_bleu.poids_pesee) if combat.boxeur_bleu.poids_pesee else None,
            'taille': combat.boxeur_bleu.taille_cm,
            'age': combat.boxeur_bleu.age,
            'photo': combat.boxeur_bleu.photo.url if combat.boxeur_bleu.photo else None,
        },
        'officiels': officiels_data,
        'media_regie': {
            'image_url': combat.media_regie_image.url if combat.media_regie_image else None,
            'titre': combat.media_regie_titre or "HIGHLIGHT / ACTION DU MATCH"
        },
        'total_rouge': tot_rouge,
        'total_bleu': tot_bleu,
        'type_decision': combat.get_type_decision_display() if combat.type_decision else "Décision Officielle",
        'rounds': rounds_data,
        'prochains_combats': prochains_combats
    }

    return JsonResponse(data)

@csrf_exempt
@login_required
def api_changer_mode_tv(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            mode_tv = data.get('mode_tv')
            combat_id = data.get('combat_id')
            media_titre = data.get('media_titre')

            if combat_id:
                combat = Combat.objects.get(id=combat_id)
            else:
                combat = Combat.objects.filter(statut__in=['EN_COURS', 'BROADCAST', 'A_VENIR']).order_by('-id').first()

            if combat and mode_tv:
                combat.mode_tv = mode_tv
                if media_titre:
                    combat.media_regie_titre = media_titre
                combat.save()
                return JsonResponse({'statut': 'succes', 'mode_tv': combat.mode_tv, 'message': f'Mode TV mis à jour : {mode_tv}'})
        except Exception as e:
            return JsonResponse({'statut': 'erreur', 'message': str(e)}, status=400)

    return JsonResponse({'statut': 'erreur', 'message': 'Requête invalide'}, status=400)