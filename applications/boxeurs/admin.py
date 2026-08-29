from django.contrib import admin
from .models import Boxeur, Categorie

@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ('nom', 'genre', 'poids_minimum', 'poids_maximum')
    list_filter = ('genre',)
    search_fields = ('nom',)
    fieldsets = (
        ('Définition de la Catégorie', {
            'fields': (('nom', 'genre'), ('poids_minimum', 'poids_maximum'))
        }),
    )


@admin.register(Boxeur)
class BoxeurAdmin(admin.ModelAdmin):
    list_display = ('id', 'nom', 'prenom', 'surnom', 'club', 'pays', 'categorie', 'poids_pesee', 'sexe')
    list_display_links = ('id', 'nom', 'prenom')
    list_filter = ('categorie', 'sexe', 'pays', 'club')
    search_fields = ('nom', 'prenom', 'surnom', 'club', 'pays')
    
    fieldsets = (
        ('Identité du Combattant', {
            'fields': (('nom', 'prenom'), ('surnom', 'sexe'), ('age', 'pays'))
        }),
        ('Caractéristiques Physiques & Catégorie', {
            'fields': (('poids_pesee', 'taille_cm'), 'categorie')
        }),
        ('Club & Équipe', {
            'fields': ('club', ('logo_club', 'photo'))
        }),
    )
