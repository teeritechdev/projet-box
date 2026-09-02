from django.test import TestCase, Client
from django.urls import reverse
from applications.comptes.models import Utilisateur, Role
from applications.boxeurs.models import Boxeur, Categorie, Pays
from applications.combats.models import Evenement, Combat, Round
from applications.scoring.models import ScoreJuge


class ScoringApiTestCase(TestCase):
    def setUp(self):
        self.role_juge = Role.objects.create(nom="Juge de Table", code="JUGE")
        self.juge = Utilisateur.objects.create_user(username="juge1", password="password123", role=self.role_juge)
        self.user_sans_droit = Utilisateur.objects.create_user(username="lambda", password="password123")

        self.pays = Pays.objects.create(nom="Burkina Faso", code_iso="BF")
        self.cat = Categorie.objects.create(nom="Welterweight -77kg", genre="Homme", poids_minimum=70.0, poids_maximum=77.0)

        self.rouge = Boxeur.objects.create(nom="OUEDRAOGO", prenom="Paul", club="AES Club", pays_fk=self.pays, categorie=self.cat)
        self.bleu = Boxeur.objects.create(nom="KABORE", prenom="Jean", club="Bobo MMA", pays_fk=self.pays, categorie=self.cat)

        self.evenement = Evenement.objects.create(titre="JAES 2026", nombre_rounds=3)
        self.combat = Combat.objects.create(
            evenement=self.evenement,
            numero_match=1,
            categorie=self.cat,
            boxeur_rouge=self.rouge,
            boxeur_bleu=self.bleu,
            statut='EN_COURS'
        )
        self.round_1 = self.combat.rounds.get(numero_round=1)
        self.round_1.statut = 'EN_COURS'
        self.round_1.save()

    def test_enregistrer_score_succes(self):
        """Test de la saisie d'un score valide par un juge."""
        client = Client()
        client.force_login(self.juge)

        response = client.post(
            reverse('enregistrer_score_api'),
            data={'round_id': self.round_1.id, 'score_rouge': 10, 'score_bleu': 9},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['statut'], 'succes')

        score = ScoreJuge.objects.get(round_combat=self.round_1, juge=self.juge)
        self.assertEqual(score.pts_rouge, 10)
        self.assertEqual(score.pts_bleu, 9)

    def test_enregistrer_score_update(self):
        """Test de la mise à jour d'un score déjà soumis."""
        client = Client()
        client.force_login(self.juge)

        ScoreJuge.objects.create(round_combat=self.round_1, juge=self.juge, pts_rouge=10, pts_bleu=9)

        response = client.post(
            reverse('enregistrer_score_api'),
            data={'round_id': self.round_1.id, 'score_rouge': 10, 'score_bleu': 8},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

        score = ScoreJuge.objects.get(round_combat=self.round_1, juge=self.juge)
        self.assertEqual(score.pts_bleu, 8)

    def test_enregistrer_score_round_inactif(self):
        """Rejet de la saisie si le round n'est pas EN_COURS."""
        self.round_1.statut = 'EN_ATTENTE'
        self.round_1.save()

        client = Client()
        client.force_login(self.juge)

        response = client.post(
            reverse('enregistrer_score_api'),
            data={'round_id': self.round_1.id, 'score_rouge': 10, 'score_bleu': 9},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("n'est pas actif", response.json()['message'])

    def test_enregistrer_score_securite(self):
        """Accès refusé pour un utilisateur n'ayant pas le rôle de juge."""
        client = Client()
        client.force_login(self.user_sans_droit)

        response = client.post(
            reverse('enregistrer_score_api'),
            data={'round_id': self.round_1.id, 'score_rouge': 10, 'score_bleu': 9},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)
