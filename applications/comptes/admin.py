from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Utilisateur, Role

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'nom')
    search_fields = ('code', 'nom')

@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    list_display = ('id', 'username', 'first_name', 'last_name', 'fonction', 'email', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active', 'is_superuser')
    search_fields = ('username', 'first_name', 'last_name', 'fonction', 'email')

    fieldsets = (
        ('Identifiants de Connexion', {
            'fields': ('username', 'password')
        }),
        ('Informations Personnelles & Fonction', {
            'fields': (('first_name', 'last_name'), ('fonction', 'email'))
        }),
        ('Rôle & Droits d\'Accès (Simplifié)', {
            'fields': ('role', ('is_active', 'is_staff', 'is_superuser'))
        }),
    )

