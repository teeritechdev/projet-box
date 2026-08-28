from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Boxeur, Categorie

@login_required
def inscription_combattant_vue(request):
    """
    Interface d'inscription officielle des combattants MMA (CNP-MMA/DA)
    Jeux de l'Alliance des États du Sahel (JAES) 2026.
    """
    categories = Categorie.objects.all().order_by('genre', 'poids_maximum')
    combattants = Boxeur.objects.all().order_by('-id')

    if request.method == 'POST':
        action = request.POST.get('action', 'creer')
        
        if action == 'creer':
            nom = request.POST.get('nom')
            prenom = request.POST.get('prenom')
            surnom = request.POST.get('surnom', '')
            sexe = request.POST.get('sexe', 'Masculin')
            pays = request.POST.get('pays', 'Burkina Faso')
            club = request.POST.get('club')
            age = request.POST.get('age') or None
            taille_cm = request.POST.get('taille_cm') or None
            poids_pesee = request.POST.get('poids_pesee') or None
            categorie_id = request.POST.get('categorie')

            categorie = Categorie.objects.filter(id=categorie_id).first() if categorie_id else None
            
            # Auto-assign category by weigh-in if not explicitly chosen
            if not categorie and poids_pesee:
                try:
                    poids_val = float(poids_pesee)
                    genre_filter = 'Homme' if sexe == 'Masculin' else 'Femme'
                    categorie = Categorie.objects.filter(genre=genre_filter, poids_maximum__gte=poids_val).order_by('poids_maximum').first()
                except ValueError:
                    pass

            b = Boxeur.objects.create(
                nom=nom,
                prenom=prenom,
                surnom=surnom,
                sexe=sexe,
                pays=pays,
                club=club,
                age=age,
                taille_cm=taille_cm,
                poids_pesee=poids_pesee,
                categorie=categorie
            )

            if 'photo' in request.FILES:
                b.photo = request.FILES['photo']
            if 'logo_club' in request.FILES:
                b.logo_club = request.FILES['logo_club']
            b.save()

            messages.success(request, f"Le combattant MMA {b.prenom} {b.nom} ({b.pays}) a été inscrit avec succès !")
            return redirect('inscription_combattant')
        
        elif action == 'supprimer':
            b_id = request.POST.get('boxeur_id')
            if b_id:
                b = get_object_or_404(Boxeur, id=b_id)
                nom_complet = f"{b.prenom} {b.nom}"
                b.delete()
                messages.warning(request, f"Le combattant {nom_complet} a été supprimé.")
            return redirect('inscription_combattant')

    context = {
        'categories': categories,
        'combattants': combattants,
    }
    return render(request, 'boxeurs/inscription_combattant.html', context)
