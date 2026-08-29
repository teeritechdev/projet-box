from django.contrib import admin
from .models import ArbitreCentral

@admin.register(ArbitreCentral)
class ArbitreCentralAdmin(admin.ModelAdmin):
    list_display = ('id', 'nom', 'prenom', 'sexe', 'pays')
    list_display_links = ('id', 'nom', 'prenom')
    search_fields = ('nom', 'prenom', 'pays')
    list_filter = ('sexe', 'pays')
    
    fieldsets = (
        ('Identité de l\'Arbitre Central', {
            'fields': (('nom', 'prenom'), ('sexe', 'pays'), 'photo')
        }),
    )

