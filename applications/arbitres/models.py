from django.db import models
from applications.boxeurs.models import Pays

class ArbitreCentral(models.Model):
    CHOICES_SEXE = [('Masculin', 'Masculin'), ('Féminin', 'Féminin')]

    nom = models.CharField(max_length=100, verbose_name="Nom")
    prenom = models.CharField(max_length=100, verbose_name="Prénom")
    sexe = models.CharField(max_length=20, choices=CHOICES_SEXE, default='Masculin', verbose_name="Sexe")
    pays = models.CharField(max_length=100, default='Burkina Faso', verbose_name="Pays / Nationalité")
    pays_fk = models.ForeignKey(Pays, on_delete=models.SET_NULL, null=True, blank=True, related_name='arbitres', verbose_name="Pays Officiel")
    date_naissance = models.DateField(null=True, blank=True, verbose_name="Date de Naissance")
    age = models.PositiveIntegerField(null=True, blank=True, verbose_name="Âge")


    photo = models.ImageField(upload_to='arbitres/', blank=True, null=True, verbose_name="Photo officielle")

    class Meta:
        verbose_name = "Arbitre Central"
        verbose_name_plural = "Arbitres Centraux"

    @property
    def drapeau_url(self):
        if self.pays_fk and self.pays_fk.drapeau:
            return self.pays_fk.drapeau.url
        return None

    @property
    def drapeau_emoji(self):
        if self.pays_fk and self.pays_fk.drapeau_emoji:
            return self.pays_fk.drapeau_emoji
        m = {
            'burkina faso': '🇧🇫',
            'mali': '🇲🇱',
            'niger': '🇳🇪',
        }
        return m.get((self.pays or '').lower().strip(), '🏳️')

    def save(self, *args, **kwargs):
        if self.date_naissance:
            from datetime import date
            today = date.today()
            self.age = today.year - self.date_naissance.year - ((today.month, today.day) < (self.date_naissance.month, self.date_naissance.day))
        if self.pays_fk:
            self.pays = self.pays_fk.nom
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.prenom} {self.nom} ({self.drapeau_emoji} {self.pays})"


