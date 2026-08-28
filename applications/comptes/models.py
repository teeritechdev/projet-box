from django.db import models
from django.contrib.auth.models import AbstractUser

class Role(models.Model):
    nom = models.CharField(max_length=50)
    code = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return self.nom

class Utilisateur(AbstractUser):
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
