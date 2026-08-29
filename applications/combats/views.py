import json
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Combat, Round, Evenement
from applications.boxeurs.models import Boxeur, Categorie
from applications.arbitres.models import ArbitreCentral
from applications.scoring.models import ScoreJuge
from applications.comptes.models import Utilisateur

@login_required
def creer_combat_vue(request):
    if request.method == 'POST':
        evenement_id = request.POST.get('evenement')
        numero_match = request.POST.get('numero_match')
        categorie_id = request.POST.get('categorie')
        boxeur_rouge_id = request.POST.get('boxeur_rouge')
        boxeur_bleu_id = request.POST.get('boxeur_bleu')
        arbitre_id = request.POST.get('arbitre_central')
        juge_principal_id = request.POST.get('juge_principal')
        juges_ids = request.POST.getlist('juges')
        date_combat = request.POST.get('date_combat') or None
        heure_combat = request.POST.get('heure_combat') or None

        if boxeur_rouge_id and boxeur_bleu_id and boxeur_rouge_id == boxeur_bleu_id:
            messages.error(request, "Le boxeur du coin rouge et du coin bleu ne peuvent pas être la même personne !")
        elif not boxeur_rouge_id or not boxeur_bleu_id or not categorie_id or not evenement_id:
            messages.error(request, "Veuillez remplir tous les champs obligatoires (Événement, Catégorie, Boxeur Rouge, Boxeur Bleu).")
        else:
            combat = Combat.objects.create(
                evenement_id=evenement_id,
                numero_match=numero_match or 1,
                categorie_id=categorie_id,
                boxeur_rouge_id=boxeur_rouge_id,
                boxeur_bleu_id=boxeur_bleu_id,
                arbitre_central_id=arbitre_id if arbitre_id else None,
                juge_principal_id=juge_principal_id if juge_principal_id else None,
                date_combat=date_combat,
                heure_combat=heure_combat,
                statut='A_VENIR'
            )
            if juges_ids:
                combat.juges.set(juges_ids)
            
            messages.success(request, f"Match #{combat.numero_match} ({combat.boxeur_rouge} vs {combat.boxeur_bleu}) créé avec succès !")
            return redirect('admin_dashboard')

    evenements = Evenement.objects.all()
    categories = Categorie.objects.all()
    boxeurs = Boxeur.objects.all()
    arbitres = ArbitreCentral.objects.all()
    from django.db.models import Q
    juges_principaux = Utilisateur.objects.filter(
        Q(role__code='JUGE_PRINCIPAL') | Q(role__nom__icontains='principal') | Q(role__nom__icontains='juge')
    ).distinct()
    juges_table = Utilisateur.objects.filter(
        Q(role__code__in=['JUGE', 'JURY', '01']) | Q(role__nom__icontains='juge') | Q(role__nom__icontains='jury')
    ).distinct()

    dernier_combat = Combat.objects.order_by('-numero_match').first()
    prochain_numero = (dernier_combat.numero_match + 1) if dernier_combat else 1

    context = {
        'evenements': evenements,
        'categories': categories,
        'boxeurs': boxeurs,
        'arbitres': arbitres,
        'juges_principaux': juges_principaux,
        'juges_table': juges_table,
        'prochain_numero': prochain_numero,
    }
    return render(request, 'combats/creer_combat.html', context)

@login_required
def table_juge_principal_vue(request):
    combat = Combat.objects.filter(statut__in=['EN_COURS', 'BROADCAST']).select_related('boxeur_rouge', 'boxeur_bleu', 'arbitre_central', 'evenement').first()
    if not combat:
        combat = Combat.objects.select_related('boxeur_rouge', 'boxeur_bleu', 'arbitre_central', 'evenement').first()

    from django.db.models import Q
    juges = combat.juges.all() if (combat and combat.juges.exists()) else Utilisateur.objects.filter(
        Q(role__code__in=['JUGE', 'JURY', '01']) | Q(role__nom__icontains='juge') | Q(role__nom__icontains='jury')
    ).distinct()
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
            combat.statut = 'EN_COURS'
            combat.mode_tv = 'LANCEMENT_ROUND'
            combat.save()
                
            return JsonResponse({'statut': 'succes', 'message': f'Round {round_obj.numero_round} démarré !'})

        elif (action in ['terminer', 'valider_round']) and round_id:
            round_obj = Round.objects.get(id=round_id)
            round_obj.statut = 'TERMINE'
            round_obj.valide = True
            calculer_score_round(round_obj)
            
            combat = round_obj.combat
            rounds_restants = combat.rounds.filter(statut__in=['EN_ATTENTE', 'EN_COURS']).exclude(id=round_obj.id)
            if not rounds_restants.exists():
                combat.mode_tv = 'DECISION_RECAP'
            else:
                combat.mode_tv = 'COMBAT_EN_COURS'
            combat.save()

            return JsonResponse({'statut': 'succes', 'message': f'Round {round_obj.numero_round} validé !'})

        elif action in ['cloturer_combat', 'proclamer']:
            combat_id = data.get('combat_id')
            if not combat_id and round_id:
                round_obj = Round.objects.get(id=round_id)
                combat_id = round_obj.combat_id

            combat = Combat.objects.get(id=combat_id)
            combat.statut = 'TERMINE'
            combat.mode_tv = 'PROCLAMATION_VAINQUEUR'
            
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