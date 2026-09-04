# pyrefly: ignore [missing-import]
from django.db import models

class Pays(models.Model):

    nom = models.CharField(max_length=100, unique=True, verbose_name="Nom du Pays")
    code_iso = models.CharField(max_length=10, blank=True, null=True, verbose_name="Code ISO (ex: BF)")
    drapeau = models.ImageField(upload_to='drapeaux_pays/', blank=True, null=True, verbose_name="Image du Drapeau HD")
    drapeau_emoji = models.CharField(max_length=10, blank=True, default="🏳️", verbose_name="Emoji Drapeau")
    est_membre_aes = models.BooleanField(default=False, verbose_name="Membre de l'AES")

    class Meta:
        verbose_name = "Pays / Nation"
        verbose_name_plural = "Pays / Nations"
        ordering = ['nom']

    def __str__(self):
        return f"{self.nom} {self.drapeau_emoji or ''}"

class Categorie(models.Model):
    nom = models.CharField(max_length=100)
    genre = models.CharField(max_length=20, choices=[('Homme', 'Homme'), ('Femme', 'Femme')], default='Homme')
    poids_minimum = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    poids_maximum = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        verbose_name = "Catégorie de Poids"
        verbose_name_plural = "Catégories de Poids"
        ordering = ['genre', 'poids_maximum']

    def __str__(self):
        return f"{self.nom} (Genre: {self.genre} • Poids: {self.poids_minimum} kg à {self.poids_maximum} kg)"

class Boxeur(models.Model):
    CHOICES_SEXE = [('Masculin', 'Masculin'), ('Féminin', 'Féminin')]

    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    surnom = models.CharField(max_length=100, blank=True, null=True)
    sexe = models.CharField(max_length=20, choices=CHOICES_SEXE, default='Masculin')
    pays = models.CharField(max_length=100, default='Burkina Faso')
    pays_fk = models.ForeignKey(Pays, on_delete=models.SET_NULL, null=True, blank=True, related_name='boxeurs', verbose_name="Pays Officiel")
    club = models.CharField(max_length=150, blank=True, null=True, default='', verbose_name="Club / Équipe")
    logo_club = models.ImageField(upload_to='logos_clubs/', blank=True, null=True)
    photo = models.ImageField(upload_to='boxeurs/', blank=True, null=True)
    musique_victoire = models.FileField(upload_to='musiques_boxeurs/', blank=True, null=True, verbose_name="Musique / Hymne de Victoire Personnalisé", help_text="Fichier audio (MP3/WAV) propre à ce combattant")
    date_naissance = models.DateField(null=True, blank=True, verbose_name="Date de Naissance")
    age = models.PositiveIntegerField(null=True, blank=True, verbose_name="Âge")


    taille_cm = models.PositiveIntegerField(null=True, blank=True)
    poids_pesee = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    categorie = models.ForeignKey(Categorie, on_delete=models.SET_NULL, null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.date_naissance:
            from datetime import date
            today = date.today()
            self.age = today.year - self.date_naissance.year - ((today.month, today.day) < (self.date_naissance.month, self.date_naissance.day))
        super().save(*args, **kwargs)


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
            'côte d\'ivoire': '🇨🇮',
            'cote d\'ivoire': '🇨🇮',
            'sénégal': '🇸🇳',
            'senegal': '🇸🇳',
            'togo': '🇹🇬',
            'bénin': '🇧🇯',
            'benin': '🇧🇯',
            'ghana': '🇬🇭',
            'cameroun': '🇨🇲',
            'france': '🇫🇷',
        }
        return m.get((self.pays or '').lower().strip(), '🏳️')

    def __str__(self):
        if self.club:
            return f"{self.prenom} {self.nom} ({self.club})"
        return f"{self.prenom} {self.nom}"


