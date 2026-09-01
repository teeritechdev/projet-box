import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'configuration.settings')
django.setup()

import django.utils.timezone
from applications.comptes.models import Role, Utilisateur
from applications.boxeurs.models import Categorie, Boxeur
from applications.arbitres.models import ArbitreCentral
from applications.combats.models import Evenement, Combat, Round

print("== SEEDING INITIAL DATA ==")

r_admin, _ = Role.objects.get_or_create(code='ADMIN', defaults={'nom': 'Administrateur'})
r_chief, _ = Role.objects.get_or_create(code='JUGE_PRINCIPAL', defaults={'nom': 'Juge Principal'})
r_jury, _ = Role.objects.get_or_create(code='JURY', defaults={'nom': 'Membre du Jury'})

# Optionnel: création de comptes de test désactivée à la demande de l'utilisateur
# Les comptes personnels réels (admin, jugep, juge10, juge11, juge12) sont conservés dans la base.

ref, _ = ArbitreCentral.objects.get_or_create(nom='OUEDRAOGN', prenom='Issouf')

c1, _ = Categorie.objects.get_or_create(nom='Poids Leger', defaults={'genre': 'Homme', 'poids_minimum': 56.0, 'poids_maximum': 60.0})
c2, _ = Categorie.objects.get_or_create(nom='Poids Moyen', defaults={'genre': 'Homme', 'poids_minimum': 69.0, 'poids_maximum': 75.0})

b1, _ = Boxeur.objects.get_or_create(nom='OUEDRAOGO', prenom='Ibrahim', defaults={'surnom': 'Le Cobra', 'sexe': 'Masculin', 'pays': 'Burkina Faso', 'club': 'RC Bobo Boxe', 'age': 24, 'taille_cm': 178, 'poids_pesee': 59.2, 'categorie': c1})
b2, _ = Boxeur.objects.get_or_create(nom='KONE', prenom='Bakary', defaults={'surnom': 'L Impact', 'sexe': 'Masculin', 'pays': "Cote d Ivoire", 'club': 'Abidjan Ring', 'age': 26, 'taille_cm': 180, 'poids_pesee': 59.8, 'categorie': c1})

evt, _ = Evenement.objects.get_or_create(titre='CHAMPIONNAT NATIONAL DE BOXE 2026', defaults={'edition': 'Grande Finale 2026', 'date_evenement': django.utils.timezone.now(), 'lieu': 'Palais des Sports de Ouaga 2000', 'duree_round_secondes': 180, 'nombre_rounds': 3, 'est_actif': True})

cmb, _ = Combat.objects.get_or_create(evenement=evt, numero_match=1, defaults={'categorie': c1, 'boxeur_rouge': b1, 'boxeur_bleu': b2, 'arbitre_central': ref, 'statut': 'EN_COURS'})

for r_num in range(1, 4):
    Round.objects.get_or_create(combat=cmb, numero_round=r_num, defaults={'statut': 'EN_COURS' if r_num == 1 else 'EN_ATTENTE'})

print("== SEEDING COMPLETE!! DATA SAVED DNAMICALLY INDB ==")