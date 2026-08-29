# pyrefly: ignore [missing-import]
from django.db import models

class ArbitreCentral(models.Model):
    CHOICES_SEXE = [('Masculin', 'Masculin'), ('Féminin', 'Féminin')]

    nom = models.CharField(max_length=100, verbose_name="Nom")
    prenom = models.CharField(max_length=100, verbose_name="Prénom")
    sexe = models.CharField(max_length=20, choices=CHOICES_SEXE, default='Masculin', verbose_name="Sexe")
    pays = models.CharField(max_length=100, default='Burkina Faso', verbose_name="Pays / Nationalité")
    photo = models.ImageField(upload_to='arbitres/', blank=True, null=True, verbose_name="Photo officielle")

    class Meta:
        verbose_name = "Arbitre Central"
        verbose_name_plural = "Arbitres Centraux"

    def __str__(self):
        return f"{self.prenom} {self.nom} ({self.pays})"

