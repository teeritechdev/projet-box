# pyrefly: ignore [missing-import]
from django.db import models

class ArbitreCentral(models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    pays = models.CharField(max_length=100, default='Burkina Faso')
    photo = models.ImageField(upload_to='arbitres/', blank=True, null=True)

    def __str__(self):
        return f"{self.prenom} {self.nom} ({self.pays})"
