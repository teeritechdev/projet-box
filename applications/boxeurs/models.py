from django.db import models

class Categorie(models.Model):
    nom = models.CharField(max_length=100)
    genre = models.CharField(max_length=20, choices=[('Homme', 'Homme'), ('Femme', 'Femme')], default='Homme')
    poids_minimum = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    poids_maximum = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f"{self.nom} ({self.genre})"

class Boxeur(models.Model):
    CHOICES_SEXE = [('Masculin', 'Masculin'), ('Féminin', 'Féminin')]

    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    surnom = models.CharField(max_length=100, blank=True, null=True)
    sexe = models.CharField(max_length=20, choices=CHOICES_SEXE, default='Masculin')
    pays = models.CharField(max_length=100, default='Burkina Faso')
    club = models.CharField(max_length=150)
    logo_club = models.ImageField(upload_to='logos_clubs/', blank=True, null=True)
    photo = models.ImageField(upload_to='boxeurs/', blank=True, null=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    taille_cm = models.PositiveIntegerField(null=True, blank=True)
    poids_pesee = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    categorie = models.ForeignKey(Categorie, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.prenom} {self.nom} ({self.club})"
