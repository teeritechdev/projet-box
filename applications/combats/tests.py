from django.test import TestCase, Client
from django.urls import reverse
from applications.comptes.models import Utilisateur, Role
from applications.boxeurs.models import Boxeur, Categorie, Pays
from applications.arbitres.models import ArbitreCentral
from applications.combats.models import Evenement, Combat, Round
from applications.scoring.models import ScoreJuge
from applications.combats.views import calculer_decision_carte_par_carte


class CombatDecisionTestCase(TestCase):
    def setUp(self):
        self.role_admin = Role.objects.create(nom="Administrateur", code="ADMIN")
        self.role_jp = Role.objects.create(nom="Juge Principal", code="JUGE_PRINCIPAL")
        self.role_juge = Role.objects.create(nom="Juge de Table", code="JUGE")

        self.user_jp = Utilisateur.objects.create_user(
            username="jp1", password="password123", role=self.role_jp, first_name="Chef", last_name="Juge"
        )
        self.juge1 = Utilisateur.objects.create_user(username="juge1", password="password123", role=self.role_juge)
        self.juge2 = Utilisateur.objects.create_user(username="juge2", password="password123", role=self.role_juge)
        self.juge3 = Utilisateur.objects.create_user(username="juge3", password="password123", role=self.role_juge)
        self.user_lambda = Utilisateur.objects.create_user(username="lambda", password="password123", role=self.role_juge)

        self.pays_bf = Pays.objects.create(nom="Burkina Faso", code_iso="BF", drapeau_emoji="🇧🇫")
        self.cat_70 = Categorie.objects.create(nom="Lightweight -70kg", genre="Homme", poids_minimum=65.0, poids_maximum=70.0)

        self.rouge = Boxeur.objects.create(nom="SANOU", prenom="Ibrahim", club="AES Gym", pays_fk=self.pays_bf, categorie=self.cat_70)
        self.bleu = Boxeur.objects.create(nom="TRAORE", prenom="Moussa", club="Sahel Club", pays_fk=self.pays_bf, categorie=self.cat_70)

        self.evenement = Evenement.objects.create(titre="JAES 2026", nombre_rounds=3)
        self.combat = Combat.objects.create(
            evenement=self.evenement,
            numero_match=1,
            categorie=self.cat_70,
            boxeur_rouge=self.rouge,
            boxeur_bleu=self.bleu,
            juge_principal=self.user_jp,
            statut='A_VENIR'
        )
        self.combat.juges.set([self.juge1, self.juge2, self.juge3])

    def test_decision_unanime_ud(self):
        """Test une décision unanime (UD) où les 3 juges donnent le coin rouge gagnant."""
        rounds = self.combat.rounds.order_by('numero_round')
        self.assertEqual(rounds.count(), 3)

        # Round 1
        ScoreJuge.objects.create(round_combat=rounds[0], juge=self.juge1, pts_rouge=10, pts_bleu=9)
        ScoreJuge.objects.create(round_combat=rounds[0], juge=self.juge2, pts_rouge=10, pts_bleu=9)
        ScoreJuge.objects.create(round_combat=rounds[0], juge=self.juge3, pts_rouge=10, pts_bleu=9)

        # Round 2
        ScoreJuge.objects.create(round_combat=rounds[1], juge=self.juge1, pts_rouge=10, pts_bleu=9)
        ScoreJuge.objects.create(round_combat=rounds[1], juge=self.juge2, pts_rouge=10, pts_bleu=9)
        ScoreJuge.objects.create(round_combat=rounds[1], juge=self.juge3, pts_rouge=10, pts_bleu=9)

        # Round 3
        ScoreJuge.objects.create(round_combat=rounds[2], juge=self.juge1, pts_rouge=10, pts_bleu=9)
        ScoreJuge.objects.create(round_combat=rounds[2], juge=self.juge2, pts_rouge=10, pts_bleu=9)
        ScoreJuge.objects.create(round_combat=rounds[2], juge=self.juge3, pts_rouge=10, pts_bleu=9)

        coin_v, vainq, qualif, details = calculer_decision_carte_par_carte(self.combat)
        self.assertEqual(coin_v, 'ROUGE')
        self.assertEqual(vainq, self.rouge)
        self.assertIn("Décision Unanime", qualif)

    def test_decision_partagee_sd(self):
        """Test une décision partagée (SD) : 2 juges pour Rouge, 1 juge pour Bleu."""
        rounds = self.combat.rounds.order_by('numero_round')

        for r in rounds:
            ScoreJuge.objects.create(round_combat=r, juge=self.juge1, pts_rouge=10, pts_bleu=9)
            ScoreJuge.objects.create(round_combat=r, juge=self.juge2, pts_rouge=10, pts_bleu=9)
            ScoreJuge.objects.create(round_combat=r, juge=self.juge3, pts_rouge=9, pts_bleu=10)

        coin_v, vainq, qualif, details = calculer_decision_carte_par_carte(self.combat)
        self.assertEqual(coin_v, 'ROUGE')
        self.assertEqual(vainq, self.rouge)
        self.assertIn("Décision Partagée", qualif)

    def test_decision_majoritaire_md(self):
        """Test une décision majoritaire (MD) : 2 juges pour Rouge, 1 juge Égalité."""
        rounds = self.combat.rounds.order_by('numero_round')

        for r in rounds:
            ScoreJuge.objects.create(round_combat=r, juge=self.juge1, pts_rouge=10, pts_bleu=9)
            ScoreJuge.objects.create(round_combat=r, juge=self.juge2, pts_rouge=10, pts_bleu=9)

        ScoreJuge.objects.create(round_combat=rounds[0], juge=self.juge3, pts_rouge=10, pts_bleu=9)
        ScoreJuge.objects.create(round_combat=rounds[1], juge=self.juge3, pts_rouge=9, pts_bleu=10)
        ScoreJuge.objects.create(round_combat=rounds[2], juge=self.juge3, pts_rouge=10, pts_bleu=10)

        coin_v, vainq, qualif, details = calculer_decision_carte_par_carte(self.combat)
        self.assertEqual(coin_v, 'ROUGE')
        self.assertEqual(vainq, self.rouge)
        self.assertIn("Décision Majoritaire", qualif)

    def test_departage_par_cumul_points(self):
        """Test le départage par la somme de tous les rounds (ex: 82 pts vs 81 pts -> Vainqueur Rouge)."""
        rounds = self.combat.rounds.order_by('numero_round')

        # Juge 10 (juge1) : 8-10, 8-8, 10-8 -> 26-26 (Nul)
        ScoreJuge.objects.create(round_combat=rounds[0], juge=self.juge1, pts_rouge=8, pts_bleu=10)
        ScoreJuge.objects.create(round_combat=rounds[1], juge=self.juge1, pts_rouge=8, pts_bleu=8)
        ScoreJuge.objects.create(round_combat=rounds[2], juge=self.juge1, pts_rouge=10, pts_bleu=8)

        # Juge 11 (juge2) : 10-10, 9-9, 9-10 -> 28-29 (Bleu)
        ScoreJuge.objects.create(round_combat=rounds[0], juge=self.juge2, pts_rouge=10, pts_bleu=10)
        ScoreJuge.objects.create(round_combat=rounds[1], juge=self.juge2, pts_rouge=9, pts_bleu=9)
        ScoreJuge.objects.create(round_combat=rounds[2], juge=self.juge2, pts_rouge=9, pts_bleu=10)

        # Juge 12 (juge3) : 9-8, 9-9, 10-9 -> 28-26 (Rouge)
        ScoreJuge.objects.create(round_combat=rounds[0], juge=self.juge3, pts_rouge=9, pts_bleu=8)
        ScoreJuge.objects.create(round_combat=rounds[1], juge=self.juge3, pts_rouge=9, pts_bleu=9)
        ScoreJuge.objects.create(round_combat=rounds[2], juge=self.juge3, pts_rouge=10, pts_bleu=9)

        # Total Rouge = 26 + 28 + 28 = 82 pts
        # Total Bleu = 26 + 29 + 26 = 81 pts
        coin_v, vainq, qualif, details = calculer_decision_carte_par_carte(self.combat)
        self.assertEqual(coin_v, 'ROUGE')
        self.assertEqual(vainq, self.rouge)
        self.assertIn("82-81 pts", qualif)

    def test_lancer_match_api_securite(self):
        """Test du lancement de match via API avec sécurité des rôles."""
        client = Client()

        # 1. Non authentifié -> Redirection login
        response = client.post(reverse('lancer_match_api'), data={'combat_id': self.combat.id}, content_type='application/json')
        self.assertEqual(response.status_code, 302)

        # 2. Authentifié sans rôle de chef juge / admin -> HTTP 403
        client.force_login(self.user_lambda)
        response = client.post(reverse('lancer_match_api'), data={'combat_id': self.combat.id}, content_type='application/json')
        self.assertEqual(response.status_code, 403)

        # 3. Authentifié Juge Principal -> Succès HTTP 200
        client.force_login(self.user_jp)
        response = client.post(reverse('lancer_match_api'), data={'combat_id': self.combat.id}, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['statut'], 'succes')

        self.combat.refresh_from_db()
        self.assertEqual(self.combat.statut, 'EN_COURS')
