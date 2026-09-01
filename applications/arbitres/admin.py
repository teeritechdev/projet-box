from django.contrib import admin
from .models import ArbitreCentral

@admin.register(ArbitreCentral)
class ArbitreCentralAdmin(admin.ModelAdmin):
    list_display = ('id', 'nom', 'prenom', 'sexe', 'pays_fk', 'age')
    list_display_links = ('id', 'nom', 'prenom')
    search_fields = ('nom', 'prenom', 'pays_fk__nom')
    list_filter = ('sexe', 'pays_fk')
    
    readonly_fields = ('age',)
    fieldsets = (
        ('Identité de l\'Arbitre Central', {
            'fields': (('nom', 'prenom'), ('sexe', 'pays_fk'), ('date_naissance', 'age'), 'photo')
        }),
    )



    def save_model(self, request, obj, form, change):
        if obj.pays_fk:
            obj.pays = obj.pays_fk.nom
        super().save_model(request, obj, form, change)


