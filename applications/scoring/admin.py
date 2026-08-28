from django.contrib import admin
from .models import ScoreJuge

@admin.register(ScoreJuge)
class ScoreJugeAdmin(admin.ModelAdmin):
    list_display = ('round_combat', 'juge', 'pts_rouge', 'pts_bleu', 'date_saisie')
    list_filter = ('juge', 'round_combat__combat')
    search_fields = ('juge__username', 'round_combat__combat__boxeur_rouge__nom', 'round_combat__combat__boxeur_bleu__nom')
    
    fieldsets = (
        ('Saisie Officielle du Score par le Juge', {
            'fields': (('round_combat', 'juge'), ('pts_rouge', 'pts_bleu'))
        }),
    )
