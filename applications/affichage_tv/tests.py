from django.test import TestCase, Client
from django.urls import reverse
from applications.comptes.models import Utilisateur, Role
from applications.boxeurs.models import Boxeur, Categorie, Pays
from applications.combats.models import Evenement, Combat


class BroadcastApiTestCase(TestCase):
    def setUp(self):
        self.role_admin = Role.objects.create(nom="Administrateur", code="ADMIN")
        self.admin_user = Utilisateur.objects.create_user(username="admin1", password="password123", role=self.role_admin)
        self.user_lambda = Utilisateur.objects.create_user(username="lambda", password="password123")

        self.pays = Pays.objects.create(nom="Burkina Faso", code_iso="BF")
        self.cat = Categorie.objects.create(nom="Middleweight -84kg", genre="Homme", poids_minimum=77.0, poids_maximum=84.0)

        self.rouge = Boxeur.objects.create(nom="ZONGO", prenom="Alassane", club="Ouaga Gym", pays_fk=self.pays, categorie=self.cat)
        self.bleu = Boxeur.objects.create(nom="COMPAORE", prenom="Salif", club="Bobo Fight", pays_fk=self.pays, categorie=self.cat)

        self.evenement = Evenement.objects.create(titre="JAES 2026", nombre_rounds=3)
        self.combat = Combat.objects.create(
            evenement=self.evenement,
            numero_match=1,
            categorie=self.cat,
            boxeur_rouge=self.rouge,
            boxeur_bleu=self.bleu,
            statut='EN_COURS',
            mode_tv='PRESENTATION_COMBATTANTS'
        )

    def test_api_statut_broadcast(self):
        """Test de l'API de statut broadcast pour l'écran TV."""
        client = Client()
        response = client.get(reverse('api_statut_broadcast'))
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertTrue(data['actif'])
        self.assertEqual(data['mode_tv'], 'PRESENTATION_COMBATTANTS')
        self.assertEqual(data['boxeur_rouge']['nom'], 'Alassane ZONGO')
        self.assertEqual(data['boxeur_bleu']['nom'], 'Salif COMPAORE')

    def test_api_changer_mode_tv_securite(self):
        """Test du changement de mode TV régie avec contrôle de sécurité."""
        client = Client()

        # Non connecté -> Redirection login
        response = client.post(
            reverse('api_changer_mode_tv'),
            data={'combat_id': self.combat.id, 'mode_tv': 'COMBAT_EN_COURS'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 302)

        # Utilisateur sans privilèges -> HTTP 403
        client.force_login(self.user_lambda)
        response = client.post(
            reverse('api_changer_mode_tv'),
            data={'combat_id': self.combat.id, 'mode_tv': 'COMBAT_EN_COURS'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)

        # Administrateur -> Succès HTTP 200
        client.force_login(self.admin_user)
        response = client.post(
            reverse('api_changer_mode_tv'),
            data={'combat_id': self.combat.id, 'mode_tv': 'COMBAT_EN_COURS'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['mode_tv'], 'COMBAT_EN_COURS')

        self.combat.refresh_from_db()
        self.assertEqual(self.combat.mode_tv, 'COMBAT_EN_COURS')
