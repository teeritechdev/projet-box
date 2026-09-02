# pyrefly: ignore [missing-import]
from django.contrib import admin
from .models import Boxeur, Categorie, Pays


@admin.register(Pays)
class PaysAdmin(admin.ModelAdmin):
    list_display = ('nom', 'code_iso', 'drapeau_emoji', 'est_membre_aes')
    list_filter = ('est_membre_aes',)
    search_fields = ('nom', 'code_iso')


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
    list_display = ('id', 'nom', 'prenom', 'surnom', 'club', 'pays_fk', 'categorie', 'poids_pesee', 'sexe')
    list_display_links = ('id', 'nom', 'prenom')
    list_filter = ('pays_fk', 'categorie', 'sexe', 'club')
    search_fields = ('nom', 'prenom', 'surnom', 'club', 'pays_fk__nom')
    readonly_fields = ('age',)
    fieldsets = (
        ('Identité du Combattant', {
            'fields': (('nom', 'prenom'), ('surnom', 'sexe'), ('date_naissance', 'age'), 'pays_fk')
        }),

        ('Caractéristiques Physiques & Catégorie', {
            'fields': (('poids_pesee', 'taille_cm'), 'categorie')
        }),
        ('Club & Équipe', {
            'fields': ('club', ('logo_club', 'photo'))
        }),
    )




    def save_model(self, request, obj, form, change):
        if obj.pays_fk:
            obj.pays = obj.pays_fk.nom
        super().save_model(request, obj, form, change)

