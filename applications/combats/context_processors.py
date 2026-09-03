from .models import Evenement, Combat
from applications.scoring.models import ScoreJuge

def evenement_actif(request):
    """
    Fournit l'événement actif et l'historique des combats pour les juges
    à tous les gabarits sans rien coder en dur.
    """
    evt = Evenement.objects.filter(est_actif=True).first()
    
    mes_combats_histoire = []
    if request.user.is_authenticated:
        combats_historique = Combat.objects.filter(statut__in=['TERMINE', 'EN_COURS']).select_related('boxeur_rouge', 'boxeur_bleu', 'categorie', 'vainqueur', 'juge_principal').prefetch_related('juges', 'rounds__scores_juges').order_by('numero_match')
        for idx, c in enumerate(combats_historique):
            scores_juge_c = ScoreJuge.objects.filter(round_combat__combat=c, juge=request.user).select_related('round_combat').order_by('round_combat__numero_round')
            est_juge_de_table = c.juges.filter(id=request.user.id).exists() if c.juges.exists() else True
            est_juge_principal = (c.juge_principal == request.user)
            
            if est_juge_principal and est_juge_de_table:
                role_affiche = "Juge Principal & Juge de Table"
            elif est_juge_principal:
                role_affiche = "Juge Principal (Chef de Table)"
            elif est_juge_de_table:
                role_affiche = "Juge de Table (Jury Officiel)"
            else:
                role_affiche = "Observateur / Officiel"

            mes_combats_histoire.append({
                'index': idx,
                'combat': c,
                'role_affiche': role_affiche,
                'est_juge_principal': est_juge_principal,
                'est_juge_de_table': est_juge_de_table,
                'mes_scores_rounds': list(scores_juge_c),
            })

    return {
        'evenement_actif': evt,
        'mes_combats_histoire': mes_combats_histoire
    }

