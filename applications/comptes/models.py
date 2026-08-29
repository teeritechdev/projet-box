from django.db import models
from django.contrib.auth.models import AbstractUser

class Role(models.Model):
    nom = models.CharField(max_length=50)
    code = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return self.nom

class Utilisateur(AbstractUser):
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    fonction = models.CharField(max_length=100, blank=True, null=True, verbose_name="Fonction / Titre", help_text="Ex: Président de séance, Médecin officiel, Chronométreur, etc.")
    photo = models.ImageField(upload_to='juges_photos/', blank=True, null=True, verbose_name="Photo Officielle", help_text="Photo d'identité / portrait officiel du juge")

    def __str__(self):
        if self.first_name or self.last_name:
            return f"{self.first_name} {self.last_name} ({self.username})"
        return self.username

