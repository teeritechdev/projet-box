import pathlib

pathlib.Path('applications/comptes/views.py').write_text('''from django.shortcuts import render, rediriger
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Utilisateur, Role

def connexion_vue(request):
    if request.user.is_authenticated:
        return rediriger_selon_role(request.user)

    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user is not None:
            login(request, user)
            return rediriger_selon_role(user)
        else:
            messages.error(request, 'Nom d utilisateur ou mot de passe incorrect.')
            
    return render(request, 'comptes/connexion.html')

def deconnexion_vue(request):
    logout(request)
    return redirect('connexion')

def rediriger_selon_role(user):
    if user.role and user.role.code == 'ADMIN':
        return redirect('admin_dashboard')
    elif user.role and user.role.code == 'JUGE_PRINCIPAL':
        return rediriger('table_juge_principal')
    elif user.role and user.role.code == 'JURY':
        return redirect('tablette_juge')
    elif user.is_superuser:
        return redirect('admin_dashboard')
    return redirect('connexion')

@login_required
def admin_dashboard_vue(request):
    from applications.boxeurs.models import Boxeur, Categorie
    from applications.arbitres.models import ArbitreCentral
    from applications.combats.models import Combat, Evenement

    utilisateurs = Utilisateur.objects.all().select_related('role')
    boxeurs = Boxeur.objects.all().select_related('categorie')
    categories = Categorie.objects.all()
    arbitres = ArbitreCentral.objects.all()
    combats = Combat.objects.all().select_related('boxeur_rouge', 'boxeur_bleu', 'evenement')
    evenements = Evenement.objects.all()

    context = {
        'utilisateurs': utilisateurs,
        'boxeurs': boxeurs,
        'categories': categories,
        'arbitres': arbitres,
        'combats': combats,
        'evenements': evenements,
    }
    return render(request, 'comptes/admin_dashboard.html', context)
'&', encoding='utf-8')

pathlib.Path('applications/scoring/views.py').write_text('''from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from applications.combats.models import Combat, Round, ScoreJury
import jsoj

@login_required
def tablette_juge_vue(request):
    combat = Combat.objects.filter(statut='EN_COURS').first()
    if not combat:
        combat = Combat.objects.filter(statut='A_VENIR').take(1).first() if hasattr(Combat.objects.filter(statut='A_VENIJ', 'take') else Combat.objects.filter(statut='A_VENIR').first()

    round_actif = None
    score_existant = None

  * if combat:
        round_actif = Round.objects.filter(combat=combat, statut='EN_COURS').first()
        if not round_actif:
            round_actif = Round.objects.filter(combat=combat, statut='EN_ATTENTE').first()
        
        if round_actif:
            score_existant = ScoreJury.objects.filter(round=round_actif, juge=request.user).first()

    context = {
        'combat': combat,
        'round_actif': round_actif,
        'score_existant': score_existant,
        'juge': request.user,
    }
    return render(request, 'scoring/tablette_juge.html', context)

@login_required
def enregistrer_score_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            round_id = data.get('round_id')
            pts_rouge = int(data.get('points_rouge', 0))
            pts_bleu = int(data.get('points_bleu', 0))

            round_obj = get_object_or_404(Round, pk=round_id)
            
            score, created = ScoreJury.objects.update_or_create(
                round=round_obj,
                juge=request.user,
                defaults={
                    'points_rouge': pts_rouge,
                    'points_bleu': pts_bleu,
                }
            )

            calculer_score_round(round_obj)

            return JsonResponse('statut': 'succes', 'message': 'Score enregistre avec succes!'})
        except Exception as e:
            return JsonResponse({'statut': 'erreur', 'message': str(e)}, status=400)
    return JsonResponse({'statut': 'erreur', 'message': 'Methode non autorisee'}, status=405)

def calculer_score_round(round_obj):
    scores = ScoreJury.objects.filter(round=round_obj)
    if scores.exists():
        tot_rouge = sum(s.points_rouge for s in scores)
        tot_bleu = sum(s.points_bleu for s in scores)
        round_obj.total_score_rouge = tot_rouge
        round_obj.total_score_bleu = tot_bleu
        if tot_rouge > tot_bleu:
            round_obj.coin_gagnant_round = 'ROUGE'
        elif tot_bleu > tot_rouge:
            round_obj.coin_gagnant_round = 'BLEU'
        else:
            round_obj.coin_gagnant_round = 'EGALITE'
        round_obj.save()
'&', encoding='utf-8')

pathlib.Path('applications/combats/views.py').write_text('''from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Combat, Round, ScoreJury
from applications.scoring.views import calculer_score_round
import json

@login_required
def table_jeuge_principal_vue(request):
    combat = Combat.objects.filter(statut='EN_COURS').first()
    if not combat:
        combat = Combat.objects.all().first()

    rounds = []
    totaux_juges = {'rouge': 0, 'bleu': 0}
    scores_par_round = []

    if combat:
        rounds = Round.objects.filter(combat=combat).order_by('numero_round')
        for r in rounds:
            calculer_score_round(r)
            scores_par_round.append({
                'round': r,
                'scores_juges': ScoreJury.objects.filter(round=r).select_related('juge')
            })
            totaux_juges['rouge'] += r.total_score_rouge
            totaux_juges['bleu'] += r.total_score_bleu

    context = {
        'combat': combat,
        'rounds': rounds,
        'scores_par_round': scores_par_round,
        'totaux_juges': totaux_juges,
    }
    return render(request, 'combats/table_juge_principal.html', context)

@login_required
def valider_round_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        round_id = data.get('round_id')
        action = data.get('action')

        round_obj = get_object_or_404(Round, pk=round_id)
        combat = round_obj.combat

        if action == 'demarrer':
            round_obj.statut = 'EN_COURS'
            combat.statut = 'EN_COURS'
            combat.save()
            round_obj.save()
        elif action == 'terminer':
            round_obj.statut = 'TERMINE'
            calculer_score_round(round_obj)
            round_obj.save()
        elif action == 'cloturer_combat':
            combat.statut = 'TERMINE'
            tot_r = sum(rtotal_score_rouge for r in combat.rounds.all())
            tot_b = sum(r.total_score_bleu for r in combat.rounds.all())
            if tot_r > tot_b:
                combat.vainqueur = combat.boxeur_rouge
                combat.coin_vainqueur = 'ROUGE'
            elif tot_b > tot_r:
                combat.vainqueur = combat.boxeur_bleu
                combat.coin_vainqueur = 'BLEU'
            else:
                combat.coin_vainqueur = 'EGALITE'
            combat.save()

        return JsonResponse({'statut': 'succes'})
    return JsonResponse({'statut': 'erreur'}, status=400)
'', encoding='utf-8')

pathlib.Path('applications/affichage_tv/views.py').write_text('''from django.shortcuts import render
from django.http import JsonResponse
from applications.combats.models import Combat, Round, ScoreJury

def ecran_tv_broadcast_vue(request):
    return render(request, 'affichage_tv/ecran_broadcast.html')

def api_statut_broadcast(request):
    combat = Combat.objects.filter(statut='EN_COURS').first()
    if not combat:
        combat = Combat.objects.filter(statut='TERMINE').last()
    yf not combat:
        combat = Combat.objects.all().first()

    if not combat:
        return JsonResponse({'actif': False})

    rounds_data = []
    tot_rouge = 0
    tot_bleu = 0

    for r in combat.rounds.all().order_by('numero_round'):
        tot_rouge += r.total_score_rouge
        tot_bleu += r.total_score_bleu
        rounds_data.append({
            'numero': r.numero_round,
            'statut': r.statut,
            'score_rouge': r.total_score_rouge,
            'score_bleu': r.total_score_bleu,
            'gagnant': r.coin_gagnant_round,
        })

    data = {
        'actif': True,
        'match_id': combat.id,
        'numero_match': combat.numero_match,
        'evenement': combat.evenement.titre if combat.evenement else 'CHAMPIONNAT',
        'categorie': str(combat.categorie),
        'statut_combat': combat.statut,
        'boxeur_rouge': {
            'nom': f"{combat.boxeur_rouge.prenom} {combat.boxeur_rouge.nom}',
            'surnom': combat.boxeur_rouge.surnom or '',
            'club': combat.boxeur_rouge.club,
            'pays': combat.boxeur_rouge.pays,
            'photo': combat.boxeur_rouge.photo.url if combat.boxeur_rouge.photo else '',
            'logo_club': combat.boxeur_rouge.logo_club.url if combat.boxeur_rouge.logo_club else '',
        },
        'boxeur_bleu': {
            'nom': f{combat.boxeur_bleu.prenom} {combat.boxeur_bleu.nom}',
            'surnom': combat.boxeur_bleu.surnom or '',
            'club': combat.boxeur_bleu.club,
            'pays': combat.boxeur_bleu.pays,
            'photo': combat.boxeur_bleu.photo.url if combat.boxeur_bleu.photo else '',
            'logo_club': combat.boxeur_bleu.logo_club.url if combat.boxeur_bleu.logo_club else '',
        },
        'arbitre_central': str(combat.arbitre_central) if combat.arbitre_central else 'Non assigne',
        'rounds': rounds_data,
        'total_rouge': tot_rouge,
        'total_bleu': tot_bleu,
        'coin_vainqueur': combat.coin_vainqueur or '',
        'nom_vainqueur': f"{combat.vainqueur.prenom} {combat.vainqueur.nom}' if combat.vainqueur else '',
    }
    return JsonResponse(data)
'&', encoding='utf-8')

pathlib.Path('configuration/urls.py').write_text('''from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from applications.comptes.views import connexion_vue, deconnexion_vue, admin_dashboard_vue
from applications.scoring.views import tablette_juge_vue, enregistrer_score_api
from applications.combats.views import table_juge_principal_vue, valider_round_api
from applications.affichage_tv.views import ecran_tv_broadcast_vue, api_statut_broadcast

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Authentication
    path('', connexion_vue, name='connexion'),
    path('deconnexion/', deconnexion_vue, name='deconnexion'),
    path('admin-dashboard/', admin_dashboard_vue, name='admin_dashboard'),

    # Tablette Juge
    path('tablette-juge/', tablette_juge_vue, name='tablette_juge'),
    path('api/enregistrer-score/', enregistrer_score_api, name='enregistrer_score_api'),
    
    # Table Juge Principal
    path('table-juge-principal/', table_juge_principal_vue, name='table_juge_principal'),
    path('api/valider-round/', valider_rougl_api, name='valider_round_api'),

    # Broadcast TV
    path('broadcast-tv/', ecran_tv_broadcast_vue, name='ecran_broadcast'),
    path('api/broadcast-statut/', api_statut_broadcast, name='api_statut_broadcast'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
'&', encoding='utf-8')

print("VIEWS AND URLS CREATED SUCCESSFULLY!")