from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from applications.comptes.views import connexion_vue, deconnexion_vue, admin_dashboard_vue
from applications.boxeurs.views import inscription_combattant_vue
from applications.scoring.views import tablette_juge_vue, enregistrer_score_api
from applications.combats.views import table_juge_principal_vue, valider_round_api, creer_combat_vue, lancer_match_api

from applications.affichage_tv.views import ecran_tv_broadcast_vue, api_statut_broadcast, api_changer_mode_tv, api_sse_broadcast

admin.site.site_header = "FÉDÉRATION NATIONALE DE MMA — CNP-MMA/DA"
admin.site.site_title = "Admin MMA Scoring JAES 2026"
admin.site.index_title = "Gestion des Combats MMA, Officiels & Scores"

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Authentication & Admin
    path('', connexion_vue, name='connexion'),
    path('deconnexion/', deconnexion_vue, name='deconnexion'),
    path('admin-dashboard/', admin_dashboard_vue, name='admin_dashboard'),
    path('inscription-combattant/', inscription_combattant_vue, name='inscription_combattant'),
    path('creer-combat/', creer_combat_vue, name='creer_combat'),


    # Tablette Juge
    path('tablette-juge/', tablette_juge_vue, name='tablette_juge'),
    path('api/enregistrer-score/', enregistrer_score_api, name='enregistrer_score_api'),
    
    # Table Juge Principal
    path('table-juge-principal/', table_juge_principal_vue, name='table_juge_principal'),
    path('api/valider-round/', valider_round_api, name='valider_round_api'),
    path('api/lancer-match/', lancer_match_api, name='lancer_match_api'),

    # Broadcast Arena TV
    path('broadcast-tv/', ecran_tv_broadcast_vue, name='ecran_broadcast'),
    path('api/broadcast-statut/', api_statut_broadcast, name='api_statut_broadcast'),
    path('api/broadcast-stream/', api_sse_broadcast, name='api_sse_broadcast'),
    path('api/changer-mode-tv/', api_changer_mode_tv, name='api_changer_mode_tv'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)