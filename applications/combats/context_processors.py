from .models import Evenement

def evenement_actif(request):
    """
    Fournit l'événement actif et ses logos/titres dynamiques (Capture A)
    à tous les gabarits sans rien coder en dur.
    """
    evt = Evenement.objects.filter(est_actif=True).first()
    return {
        'evenement_actif': evt
    }
