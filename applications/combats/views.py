import json
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
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
    tous_les_combats = Combat.objects.all().select_related('boxeur_rouge', 'boxeur_bleu', 'categorie').order_by('numero_match')

    combat_id = request.GET.get('combat_id')
    if combat_id:
        combat = Combat.objects.filter(id=combat_id).select_related('boxeur_rouge', 'boxeur_bleu', 'arbitre_central', 'evenement', 'categorie').first()
    else:
        combat = Combat.objects.filter(statut='EN_COURS').select_related('boxeur_rouge', 'boxeur_bleu', 'arbitre_central', 'evenement', 'categorie').first()
    
    if combat:
        from applications.affichage_tv.views import set_combat_diffusion_actif
        set_combat_diffusion_actif(combat.id)

    from django.db.models import Q

    juges = combat.juges.all() if (combat and combat.juges.exists()) else Utilisateur.objects.filter(
        Q(role__code__in=['JUGE', 'JURY', '01']) | Q(role__nom__icontains='juge') | Q(role__nom__icontains='jury')
    ).distinct()
    rounds = combat.rounds.all().prefetch_related('scores_juges') if combat else []

    scores_par_round = []
    totaux_juges = {'rouge': 0, 'bleu': 0}

    nb_juges_totaux = juges.count() if juges.exists() else 3
    aucun_round_en_cours = not combat.rounds.filter(statut='EN_COURS').exists() if combat else True

    for r in rounds:
        scores_list = list(r.scores_juges.all())
        nb_valides = len(scores_list)
        est_complet = (nb_valides >= 3) or (nb_juges_totaux > 0 and nb_valides >= nb_juges_totaux)

        # Vérifier le séquencement du round précédent
        if r.numero_round == 1:
            round_precedent_valide = True
        else:
            prev_r = combat.rounds.filter(numero_round=r.numero_round - 1).first()
            round_precedent_valide = (prev_r is not None and prev_r.statut == 'TERMINE' and prev_r.valide)

        # Un round ne peut être lancé QUE SI le match est EN_COURS, le round précédent est VALIDE, et aucun round n'est EN_COURS
        peut_etre_lance = (combat.statut == 'EN_COURS') and round_precedent_valide and (r.statut == 'EN_ATTENTE') and aucun_round_en_cours

        scores_par_round.append({
            'round': r,
            'scores_juges': scores_list,
            'nb_valides': nb_valides,
            'est_complet': est_complet,
            'round_precedent_valide': round_precedent_valide,
            'peut_etre_lance': peut_etre_lance,
        })
        if r.coin_gagnant_round == 'ROUGE':
            totaux_juges['rouge'] += 1
        elif r.coin_gagnant_round == 'BLEU':
            totaux_juges['bleu'] += 1

    round_actif = combat.rounds.filter(statut='EN_COURS').first() if combat else None
    tous_rounds_valides = (rounds.count() > 0) and not rounds.filter(valide=False).exists() if combat else False

    context = {
        'combat': combat,
        'tous_les_combats': tous_les_combats,
        'juges': juges,
        'nb_juges_totaux': nb_juges_totaux,
        'scores_par_round': scores_par_round,
        'totaux_juges': totaux_juges,
        'round_actif': round_actif,
        'tous_rounds_valides': tous_rounds_valides,
    }
    return render(request, 'combats/table_juge_principal.html', context)



def est_juge_principal_ou_admin(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    if user.role:
        code = str(user.role.code).upper()
        nom = str(user.role.nom).lower()
        if code in ['JUGE_PRINCIPAL', 'ADMIN'] or 'principal' in nom or 'admin' in nom:
            return True
    return False


@login_required
def lancer_match_api(request):
    if not est_juge_principal_ou_admin(request.user):
        return JsonResponse({'statut': 'erreur', 'message': 'Accès refusé : privilèges insuffisants.'}, status=403)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            combat_id = data.get('combat_id')
            if combat_id:
                # 1. Remettre les autres combats 'EN_COURS' en statut 'A_VENIR'
                Combat.objects.filter(statut='EN_COURS').exclude(id=combat_id).update(statut='A_VENIR')

                # 2. Définir le combat sélectionné comme le combat officiel EN_COURS
                combat = Combat.objects.get(id=combat_id)
                if combat.statut == 'TERMINE':
                    return JsonResponse({
                        'statut': 'erreur',
                        'message': f'Le Match #{combat.numero_match} est déjà terminé et clôturé. Impossible de le relancer !'
                    }, status=400)

                combat.statut = 'EN_COURS'
                combat.mode_tv = 'COMBAT_EN_COURS'
                combat.save()


                from applications.affichage_tv.views import set_combat_diffusion_actif
                set_combat_diffusion_actif(combat.id)


                return JsonResponse({
                    'statut': 'succes',
                    'combat_id': combat.id,
                    'numero_match': combat.numero_match,
                    'message': f'Match #{combat.numero_match} ({combat.boxeur_rouge.nom} VS {combat.boxeur_bleu.nom}) officiellement lancé !'
                })
        except Exception as e:
            return JsonResponse({'statut': 'erreur', 'message': str(e)}, status=400)

    return JsonResponse({'statut': 'erreur', 'message': 'Requête invalide'}, status=400)


@login_required
def valider_round_api(request):
    if not est_juge_principal_ou_admin(request.user):
        return JsonResponse({'statut': 'erreur', 'message': 'Accès refusé : privilèges insuffisants.'}, status=403)

    if request.method == 'POST':
        data = json.loads(request.body)
        action = data.get('action')
        round_id = data.get('round_id')

        if action == 'demarrer' and round_id:
            round_obj = Round.objects.get(id=round_id)
            combat = round_obj.combat

            # Règle 1: Le match doit impérativement être lancé
            if combat.statut != 'EN_COURS':
                return JsonResponse({
                    'statut': 'erreur',
                    'message': 'Impossible de démarrer un round : vous devez d\'abord cliquer sur "LANCER CE MATCH" !'
                }, status=400)

            # Règle 2: Le round précédent doit être validé par le Chef Juge
            if round_obj.numero_round > 1:
                prev_r = combat.rounds.filter(numero_round=round_obj.numero_round - 1).first()
                if not prev_r or prev_r.statut != 'TERMINE' or not prev_r.valide:
                    return JsonResponse({
                        'statut': 'erreur',
                        'message': f'Impossible de démarrer le Round {round_obj.numero_round} : le Round {round_obj.numero_round - 1} doit être validé par le Chef Juge d\'abord !'
                    }, status=400)

            # Règle 3: Un seul round actif à la fois
            if combat.rounds.filter(statut='EN_COURS').exclude(id=round_obj.id).exists():
                return JsonResponse({
                    'statut': 'erreur',
                    'message': 'Un autre round est actuellement en cours. Veuillez le valider d\'abord.'
                }, status=400)

            round_obj.statut = 'EN_COURS'
            round_obj.save()

            combat.mode_tv = 'LANCEMENT_ROUND'
            combat.save()
                
            return JsonResponse({'statut': 'succes', 'message': f'Round {round_obj.numero_round} démarré !'})


        elif (action in ['terminer', 'valider_round']) and round_id:
            round_obj = Round.objects.get(id=round_id)
            nb_valides = round_obj.scores_juges.count()
            
            # Contrôle strict : Les 3 juges doivent impérativement avoir soumis leurs notes
            if nb_valides < 3:
                return JsonResponse({
                    'statut': 'erreur',
                    'message': f'Validation impossible : seuls {nb_valides}/3 juges ont transmis leurs notes !'
                }, status=400)

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


        elif action == 'arret_premature':
            combat_id = data.get('combat_id')
            if not combat_id and round_id:
                round_obj = Round.objects.get(id=round_id)
                combat_id = round_obj.combat_id

            combat = Combat.objects.get(id=combat_id)

            # Règle stricte : Interdiction de déclarer un arrêt prématuré KO/TKO si tous les rounds sont déjà validés par le jury !
            if combat.rounds.count() > 0 and not combat.rounds.filter(valide=False).exists():
                return JsonResponse({
                    'statut': 'erreur',
                    'message': 'Tous les rounds de ce combat ont été validés par le jury ! Le combat est allé au bout du temps réglementaire et doit être clôturé aux points.'
                }, status=400)

            coin_v = data.get('coin_vainqueur')  # 'ROUGE' ou 'BLEU'

            type_dec = data.get('type_decision', 'KO')  # 'KO', 'TKO', 'SOUMISSION', 'ABANDON', 'ARRET_MEDICAL', 'DISQUALIFICATION'
            round_num = data.get('round_fin')
            temps_chrono = data.get('temps_fin_round')
            tech = data.get('technique', '')

            combat.statut = 'TERMINE'
            combat.mode_tv = 'DECISION_RECAP'
            combat.type_decision = type_dec

            combat.coin_vainqueur = coin_v
            
            # Fermer tous les rounds actifs de ce combat
            combat.rounds.filter(statut='EN_COURS').update(statut='TERMINE')
            
            if coin_v == 'ROUGE':
                combat.vainqueur = combat.boxeur_rouge
            elif coin_v == 'BLEU':
                combat.vainqueur = combat.boxeur_bleu

            if round_num:
                combat.round_fin = round_num
                r_arr = combat.rounds.filter(numero_round=round_num).first()
                if r_arr:
                    r_arr.statut = 'TERMINE'
                    r_arr.save()
            
            if temps_chrono:
                combat.temps_fin_round = temps_chrono

            label_dec = dict(Combat.CHOICES_TYPE_VICTOIRE).get(type_dec, type_dec)
            combat.decision_qualification = label_dec
            combat.details_decision = tech if tech else f"Victoire par {label_dec}"
            combat.save()

            return JsonResponse({'statut': 'succes', 'message': f'Combat arrêté ! Victoire par {label_dec}.'})

        elif action in ['cloturer_combat', 'proclamer']:
            combat_id = data.get('combat_id')
            if not combat_id and round_id:
                round_obj = Round.objects.get(id=round_id)
                combat_id = round_obj.combat_id

            combat = Combat.objects.get(id=combat_id)
            combat.statut = 'TERMINE'
            combat.mode_tv = 'DECISION_RECAP'
            combat.type_decision = 'POINTS'


            # Fermer tous les rounds actifs de ce combat
            combat.rounds.filter(statut='EN_COURS').update(statut='TERMINE')

            coin_v, vainq_obj, qualif, details_c = calculer_decision_carte_par_carte(combat)
            combat.coin_vainqueur = coin_v
            combat.vainqueur = vainq_obj
            combat.decision_qualification = qualif
            combat.details_decision = details_c
            
            dernier_r = combat.rounds.order_by('numero_round').last()
            if dernier_r:
                combat.round_fin = dernier_r.numero_round
                combat.temps_fin_round = "Fin du combat"

            combat.save()
            return JsonResponse({'statut': 'succes', 'message': f'Combat terminé ! {qualif} ({details_c}).'})


    return JsonResponse({'statut': 'erreur', 'message': 'Action invalide.'}, status=400)


def calculer_decision_carte_par_carte(combat):
    """
    Calcule la décision aux points (Unanime, Partagée, Majoritaire ou Égalité)
    en comptabilisant les cartes individuelles des juges de table sur l'ensemble des rounds.
    """
    rounds = combat.rounds.all()
    vrais_juges_scores = {}  # juge_id: {'rouge': 0, 'bleu': 0}

    for r in rounds:
        for s in r.scores_juges.all():
            j_id = s.juge_id
            if j_id not in vrais_juges_scores:
                vrais_juges_scores[j_id] = {'rouge': 0, 'bleu': 0}
            vrais_juges_scores[j_id]['rouge'] += s.pts_rouge
            vrais_juges_scores[j_id]['bleu'] += s.pts_bleu

    if not vrais_juges_scores:
        # Fallback par total des rounds si pas de juges individuels enregistrés
        tot_rouge = sum(1 for r in rounds if r.coin_gagnant_round == 'ROUGE')
        tot_bleu = sum(1 for r in rounds if r.coin_gagnant_round == 'BLEU')
        if tot_rouge > tot_bleu:
            return 'ROUGE', combat.boxeur_rouge, 'Décision aux Points', f'{tot_rouge}-{tot_bleu} Rounds'
        elif tot_bleu > tot_rouge:
            return 'BLEU', combat.boxeur_bleu, 'Décision aux Points', f'{tot_bleu}-{tot_rouge} Rounds'
        else:
            return 'EGALITE', None, 'Égalité aux Points', 'Égalité'

    votes_rouge = 0
    votes_bleu = 0
    votes_egalite = 0
    cartes_list = []

    for j_id, sc in vrais_juges_scores.items():
        cartes_list.append(f"{sc['rouge']}-{sc['bleu']}")
        if sc['rouge'] > sc['bleu']:
            votes_rouge += 1
        elif sc['bleu'] > sc['rouge']:
            votes_bleu += 1
        else:
            votes_egalite += 1

    details_cartes = ", ".join(cartes_list)
    total_juges = len(vrais_juges_scores)

    if votes_rouge > votes_bleu and votes_rouge >= votes_egalite:
        coin_v = 'ROUGE'
        v_obj = combat.boxeur_rouge
        if votes_rouge == total_juges:
            qualif = "Décision Unanime (UD)"
        elif votes_bleu > 0:
            qualif = "Décision Partagée (SD)"
        else:
            qualif = "Décision Majoritaire (MD)"
    elif votes_bleu > votes_rouge and votes_bleu >= votes_egalite:
        coin_v = 'BLEU'
        v_obj = combat.boxeur_bleu
        if votes_bleu == total_juges:
            qualif = "Décision Unanime (UD)"
        elif votes_rouge > 0:
            qualif = "Décision Partagée (SD)"
        else:
            qualif = "Décision Majoritaire (MD)"
    else:
        coin_v = 'EGALITE'
        v_obj = None
        qualif = "Égalité (Draw)"

    return coin_v, v_obj, qualif, details_cartes


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