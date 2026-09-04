import json
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from applications.combats.models import Combat, Round
from .models import ScoreJuge

from applications.affichage_tv.views import get_combat_diffusion_actif

@login_required
def tablette_juge_vue(request):
    combat_id = request.GET.get('combat_id')
    combat = get_combat_diffusion_actif(combat_id)
    
    # Vérifier l'attribution officielle du juge connecté
    est_juge_attribue = False
    if combat:
        if request.user.is_superuser or request.user.is_staff:
            est_juge_attribue = True
        elif combat.juges.exists():
            est_juge_attribue = combat.juges.filter(id=request.user.id).exists()
        else:
            est_juge_attribue = True

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

    # Historique personnel de tous les combats du gala pour le juge avec détection du rôle
    combats_historique = Combat.objects.all().select_related('boxeur_rouge', 'boxeur_bleu', 'categorie', 'vainqueur', 'juge_principal').prefetch_related('juges', 'rounds__scores_juges').order_by('numero_match')
    
    mes_combats_histoire = []
    for idx, c in enumerate(combats_historique):
        scores_juge_c = ScoreJuge.objects.filter(round_combat__combat=c, juge=request.user).select_related('round_combat').order_by('round_combat__numero_round')
        est_juge_de_table = c.juges.filter(id=request.user.id).exists() if c.juges.exists() else True
        est_juge_principal = (c.juge_principal == request.user)
        
        # Déterminer le rôle exact du juge sur ce match
        if est_juge_principal and est_juge_de_table:
            role_affiche = "Juge Principal & Juge de Table"
        elif est_juge_principal:
            role_affiche = "Juge Principal (Chef de Table)"
        elif est_juge_de_table:
            role_affiche = "Juge de Table (Jury Officiel)"
        else:
            role_affiche = "Observateur / Officiel"

        # Détail complet round par round pour le grid de la modal (incluant KO / TKO / Arrêt prématuré)
        rounds_c = c.rounds.all().order_by('numero_round')
        rounds_detail = []
        for r_item in rounds_c:
            score_obj = ScoreJuge.objects.filter(round_combat=r_item, juge=request.user).first()
            if score_obj:
                rounds_detail.append({
                    'round': r_item,
                    'statut_affichage': 'SCORED',
                    'pts_rouge': score_obj.pts_rouge,
                    'pts_bleu': score_obj.pts_bleu,
                    'label': 'Transmis avec succès'
                })
            elif c.statut == 'TERMINE':
                if c.round_fin and r_item.numero_round == c.round_fin:
                    label_arr = f"Arrêt ({c.decision_qualification or c.type_decision or 'K.O.'})"
                    if c.temps_fin_round:
                        label_arr += f" à {c.temps_fin_round}"
                    rounds_detail.append({
                        'round': r_item,
                        'statut_affichage': 'ARRET_KO',
                        'label': label_arr
                    })
                elif c.round_fin and r_item.numero_round > c.round_fin:
                    rounds_detail.append({
                        'round': r_item,
                        'statut_affichage': 'NON_DISPUTE',
                        'label': f"Non disputé (Fin R{c.round_fin})"
                    })
                else:
                    rounds_detail.append({
                        'round': r_item,
                        'statut_affichage': 'ARRET_KO',
                        'label': f"Combat arrêté ({c.decision_qualification or 'K.O.'})"
                    })
            else:
                rounds_detail.append({
                    'round': r_item,
                    'statut_affichage': 'EN_ATTENTE',
                    'label': 'En attente'
                })

        mes_combats_histoire.append({
            'index': idx,
            'combat': c,
            'role_affiche': role_affiche,
            'est_juge_principal': est_juge_principal,
            'est_juge_de_table': est_juge_de_table,
            'mes_scores_rounds': list(scores_juge_c),
            'rounds_detail': rounds_detail,
        })


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
        'mes_combats_histoire': mes_combats_histoire,
        'juge': request.user,
        'est_juge_attribue': est_juge_attribue,
    }
    return render(request, 'scoring/tablette_juge.html', context)


def est_autorise_scoring(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    if user.role:
        code = str(user.role.code).upper()
        nom = str(user.role.nom).lower()
        if code in ['JUGE', 'JURY', 'JUGE_PRINCIPAL', 'ADMIN', '01'] or 'juge' in nom or 'jury' in nom or 'admin' in nom:
            return True
    return False


@login_required
def enregistrer_score_api(request):
    if not est_autorise_scoring(request.user):
        return JsonResponse({'statut': 'erreur', 'message': 'Accès refusé : privilèges insuffisants.'}, status=403)

    if request.method == 'POST':
        data = json.loads(request.body)
        round_id = data.get('round_id')
        score_rouge = data.get('score_rouge')
        if score_rouge is None:
            score_rouge = data.get('points_rouge')
        if score_rouge is None:
            score_rouge = data.get('pts_rouge')

        score_bleu = data.get('score_bleu')
        if score_bleu is None:
            score_bleu = data.get('points_bleu')
        if score_bleu is None:
            score_bleu = data.get('pts_bleu')

        if not round_id or score_rouge is None or score_bleu is None:
            return JsonResponse({'statut': 'erreur', 'message': 'Données incomplètes.'}, status=400)

        round_obj = Round.objects.get(id=round_id)
        combat = round_obj.combat
        
        # Sécurité 1 : Vérifier que le match n'est pas TERMINE et que le round est EN_COURS
        if combat.statut == 'TERMINE':
            return JsonResponse({'statut': 'erreur', 'message': 'Ce match est officiellement terminé. Saisie impossible.'}, status=400)

        if round_obj.statut != 'EN_COURS':
            return JsonResponse({'statut': 'erreur', 'message': 'Ce round n\'est pas actif. Attendez que le Chef Juge le lance.'}, status=400)

        # Sécurité 2 : Contrôle strict de l'attribution officielle des 3 juges
        if combat.juges.exists() and not (request.user.is_superuser or request.user.is_staff or combat.juges.filter(id=request.user.id).exists()):
            return JsonResponse({'statut': 'erreur', 'message': 'Vous n\'êtes pas attribué comme juge de table pour ce combat.'}, status=403)

        # Sécurité 3 : Limite stricte de 3 juges de table par round (Sauf si le juge modifie sa propre note déjà saisie)
        deja_soumis_par_moi = ScoreJuge.objects.filter(round_combat=round_obj, juge=request.user).exists()
        if not deja_soumis_par_moi and round_obj.scores_juges.count() >= 3:
            return JsonResponse({'statut': 'erreur', 'message': 'Les 3 juges de table ont déjà soumis leurs notes pour ce round.'}, status=400)

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