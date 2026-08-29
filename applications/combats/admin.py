from django.contrib import admin
from .models import Evenement, Combat, Round

@admin.register(Evenement)
class EvenementAdmin(admin.ModelAdmin):
    list_display = ('id', 'titre', 'nom_discipline', 'edition', 'lieu', 'est_actif')
    list_filter = ('est_actif', 'nom_discipline')
    search_fields = ('titre', 'edition', 'lieu', 'federation', 'organisateur')
    fieldsets = (
        ('Branding & Identification de l\'Événement (Capture A)', {
            'fields': (('titre', 'nom_discipline'), ('edition', 'lieu'), 'est_actif')
        }),
        ('Organismes & Fédérations Tutelles', {
            'fields': (('federation', 'organisateur'),)
        }),
        ('Thème de Couleur, Bannière & Drapeau (Pas de code en dur)', {
            'fields': (('couleur_fond_header', 'couleur_texte_header'), ('image_banniere_header', 'drapeau_arriere_plan'))
        }),
        ('Logos Officiels pour l\'En-tête (Pas de code en dur)', {
            'fields': (('logo_discipline', 'logo_evenement'), ('logo_ministere', 'logo_aes'))
        }),
        ('Paramètres des Combats', {
            'fields': (('duree_round_secondes', 'nombre_rounds'), 'date_evenement')
        }),
    )

class RoundInline(admin.TabularInline):
    model = Round
    extra = 0

@admin.register(Combat)
class CombatAdmin(admin.ModelAdmin):
    list_display = ('id', 'numero_match', 'date_combat', 'heure_combat', 'evenement', 'boxeur_rouge', 'boxeur_bleu', 'categorie', 'arbitre_central', 'statut', 'coin_vainqueur')
    list_display_links = ('id', 'numero_match', 'boxeur_rouge', 'boxeur_bleu')
    list_filter = ('statut', 'date_combat', 'categorie', 'evenement', 'coin_vainqueur')
    search_fields = ('boxeur_rouge__nom', 'boxeur_rouge__prenom', 'boxeur_bleu__nom', 'boxeur_bleu__prenom')
    filter_horizontal = ('juges',)
    inlines = [RoundInline]
    
    fieldsets = (
        ('Programmation du Match (Date & Heure)', {
            'fields': (('numero_match', 'evenement'), ('date_combat', 'heure_combat'))
        }),
        ('Officiels du Ring (Arbitre & Juges du Match)', {
            'fields': ('arbitre_central', 'juges')
        }),
        ('Les Combattants (Coin Rouge vs Coin Bleu)', {
            'fields': (('boxeur_rouge', 'boxeur_bleu'), 'categorie')
        }),
        ('Statut & Résultat Officiel', {
            'fields': (('statut', 'coin_vainqueur'), ('type_decision', 'vainqueur'))
        }),
    )


@admin.register(Round)
class RoundAdmin(admin.ModelAdmin):
    list_display = ('id', 'combat', 'numero_round', 'statut', 'valide', 'total_score_rouge', 'total_score_bleu', 'coin_gagnant_round')
    list_filter = ('statut', 'valide', 'combat')
    search_fields = ('combat__boxeur_rouge__nom', 'combat__boxeur_bleu__nom')
    
    fieldsets = (
        ('Détails du Round', {
            'fields': (('combat', 'numero_round'), ('statut', 'valide'))
        }),
        ('Scores Cumulés', {
            'fields': (('total_score_rouge', 'total_score_bleu'), 'coin_gagnant_round')
        }),
    )
