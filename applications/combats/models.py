# pyrefly: ignore [missing-import]
from django.db import models
# pyrefly: ignore [missing-import]
from django.conf import settings
from applications.boxeurs.models import Boxeur, Categorie
from applications.arbitres.models import ArbitreCentral

class Evenement(models.Model):
    titre = models.CharField(max_length=200, default="2ème édition des Jeux de l'Alliance des États du Sahel (JAES) 2026")
    nom_discipline = models.CharField(max_length=150, default="MIXED MARTIAL ARTS (MMA)")
    edition = models.CharField(max_length=100, default="Ouagadougou 2026")
    lieu = models.CharField(max_length=200, default="Palais des Sports de Ouagadougou (Burkina Faso)")
    organisateur = models.CharField(max_length=250, default="Ministère des Sports, de la Jeunesse et de l'Emploi MSJE / BURKINA FASO")
    federation = models.CharField(max_length=250, default="COMITÉ NATIONAL PROVISOIRE DE MMA ET DISCIPLINES ASSOCIÉES (CNP-MMA/DA)")
    
    # Logos dynamiques pour l'en-tête (Capture A)
    logo_discipline = models.ImageField(upload_to='logos_evenements/', blank=True, null=True, help_text="Logo Sports de Combat / MMA")
    logo_evenement = models.ImageField(upload_to='logos_evenements/', blank=True, null=True, help_text="Logo officiel des JAES 2026")
    logo_ministere = models.ImageField(upload_to='logos_evenements/', blank=True, null=True, help_text="Logo du Ministère MSJE Burkina Faso")
    logo_aes = models.ImageField(upload_to='logos_evenements/', blank=True, null=True, help_text="Logo Confédération AES")

    # Couleurs, bannière et drapeau arrière-plan dynamiques (Pas en dur)
    couleur_fond_header = models.CharField(max_length=50, default="#B91C1C", help_text="Couleur Hex/CSS de fond de l'en-tête (ex: #B91C1C pour Rouge Fédéral)")
    couleur_texte_header = models.CharField(max_length=50, default="#FFFFFF", help_text="Couleur Hex/CSS du texte de l'en-tête")
    image_banniere_header = models.ImageField(upload_to='bannieres_evenements/', blank=True, null=True, help_text="Image de bannière officielle pour l'en-tête (optionnelle)")
    drapeau_arriere_plan = models.ImageField(upload_to='drapeaux_evenements/', blank=True, null=True, help_text="Image du drapeau national/fédéral flottant pour l'arrière-plan de la page de connexion")

    date_evenement = models.DateTimeField(blank=True, null=True)
    duree_round_secondes = models.PositiveIntegerField(default=180)
    nombre_rounds = models.PositiveIntegerField(default=3)
    est_actif = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.titre} ({self.nom_discipline})"

class Combat(models.Model):
    CHOICES_STATUT = [
        ('A_VENIR', 'A venir'),
        ('EN_COURS', 'En cours'),
        ('TERMINE', 'Termine'),
        ('EN_PAUSE', 'En pause'),
    ]
    CHOICES_COIN = [
        ('ROUGE', 'Coin Rouge'),
        ('BLEU', 'Coin Bleu'),
        ('EGALITE', 'Egalite'),
    ]

    CHOICES_TYPE_VICTOIRE = [
        ('POINTS', 'Décision aux Points (10-Point Must)'),
        ('KO', 'K.O. (Knockout)'),
        ('TKO', 'T.K.O. (Technique K.O. / Arrêt Arbitre)'),
        ('SOUMISSION', 'Soumission (Clef / Étranglement)'),
        ('ABANDON', 'Abandon'),
        ('ARRET_MEDICAL', 'Arrêt Médical'),
        ('DISQUALIFICATION', 'Disqualification'),
    ]

    evenement = models.ForeignKey(Evenement, on_delete=models.CASCADE, related_name='combats')
    numero_match = models.PositiveIntegerField(default=1)
    categorie = models.ForeignKey(Categorie, on_delete=models.CASCADE)
    boxeur_rouge = models.ForeignKey(Boxeur, on_delete=models.CASCADE, related_name='combats_rouge')
    boxeur_bleu = models.ForeignKey(Boxeur, on_delete=models.CASCADE, related_name='combats_bleu')
    arbitre_central = models.ForeignKey(ArbitreCentral, on_delete=models.SET_NULL, null=True, blank=True)
    statut = models.CharField(max_length=20, choices=CHOICES_STATUT, default='A_VENIR')
    vainqueur = models.ForeignKey(Boxeur, on_delete=models.SET_NULL, null=True, blank=True, related_name='combats_gagnes')
    coin_vainqueur = models.CharField(max_length=10, choices=CHOICES_COIN, null=True, blank=True)
    type_decision = models.CharField(max_length=100, choices=CHOICES_TYPE_VICTOIRE, blank=True, null=True, default='POINTS')

    def __str__(self):
        return f"Match #{self.numero_match} : {self.boxeur_rouge} vs {self.boxeur_bleu}"

class Round(models.Model):
    CHOICES_STATUT = [
        ('EN_ATTENTE', 'En attente'),
        ('EN_COURS', 'En cours'),
        ('TERMINE', 'Termine'),
    ]
    CHOICES_COIN = [
        ('ROUGE', 'Coin Rouge'),
        ('BLEU', 'Coin Bleu'),
        ('EGALITE', 'Egalite'),
    ]

    combat = models.ForeignKey(Combat, on_delete=models.CASCADE, related_name='rounds')
    numero_round = models.PositiveIntegerField()
    statut = models.CharField(max_length=20, choices=CHOICES_STATUT, default='EN_ATTENTE')
    total_score_rouge = models.PositiveIntegerField(default=0)
    total_score_bleu = models.PositiveIntegerField(default=0)
    coin_gagnant_round = models.CharField(max_length=10, choices=CHOICES_COIN, null=True, blank=True)
    valide = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.combat} - Round {self.numero_round}"

class ScoreJury(models.Model):
    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name='scores_jury')
    juge = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='scores_attribues')
    points_rouge = models.PositiveIntegerField()
    points_bleu = models.PositiveIntegerField()
    date_saisie = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('round', 'juge')

    def __str__(self):
        return f"{self.juge.username} - {self.round} ({self.points_rouge}-{self.points_bleu})"
