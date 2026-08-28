from django.db import models
from django.conf import settings
from applications.combats.models import Round

class ScoreJuge(models.Model):
    round_combat = models.ForeignKey(Round, on_delete=models.CASCADE, related_name='scores_juges', verbose_name="Round")
    juge = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='scores_attribues_scoring', verbose_name="Juge")
    pts_rouge = models.IntegerField(default=10, verbose_name="Points Boxeur Rouge")
    pts_bleu = models.IntegerField(default=9, verbose_name="Points Boxeur Bleu")
    date_saisie = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Score Juge"
        verbose_name_plural = "Scores Juges"
        unique_together = ('round_combat', 'juge')

    @property
    def points_rouge(self):
        return self.pts_rouge

    @property
    def points_bleu(self):
        return self.pts_bleu

    def __str__(self):
        return f"Juge {self.juge.username} - Round {self.round_combat.numero_round}: Rouge {self.pts_rouge} vs Bleu {self.pts_bleu}"