from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Boxeur, Categorie, Pays

def convertir_date_fr_vers_iso(date_str):
    if not date_str:
        return None
    date_str = date_str.strip()
    import re
    # Convertir JJ/MM/AAAA ou JJ-MM-AAAA -> AAAA-MM-JJ
    m_fr = re.match(r'^(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{4})$', date_str)
    if m_fr:
        jour, mois, annee = m_fr.groups()
        return f"{annee}-{int(mois):02d}-{int(jour):02d}"
    return date_str

@login_required
def inscription_combattant_vue(request):
    """
    Interface d'inscription officielle des combattants MMA (CNP-MMA/DA)
    Jeux de l'Alliance des États du Sahel (JAES) 2026.
    """
    categories = Categorie.objects.all().order_by('genre', 'poids_maximum')
    combattants = Boxeur.objects.all().select_related('categorie', 'pays_fk').order_by('-id')
    pays_list = Pays.objects.all().order_by('nom')

    if request.method == 'POST':
        action = request.POST.get('action', 'creer')
        
        if action == 'creer_pays':
            nom_p = request.POST.get('nom_pays')
            code_p = request.POST.get('code_iso', '')
            emoji_p = request.POST.get('drapeau_emoji', '🏳️')
            aes_p = request.POST.get('est_membre_aes') == 'on'
            if nom_p:
                p_obj, created = Pays.objects.get_or_create(nom=nom_p, defaults={
                    'code_iso': code_p,
                    'drapeau_emoji': emoji_p,
                    'est_membre_aes': aes_p
                })
                if 'drapeau' in request.FILES:
                    p_obj.drapeau = request.FILES['drapeau']
                    p_obj.save()
                messages.success(request, f"Le pays {p_obj.nom} {p_obj.drapeau_emoji} a été ajouté avec succès !")
            return redirect('inscription_combattant')

        elif action == 'creer':
            nom = request.POST.get('nom')
            prenom = request.POST.get('prenom')
            surnom = request.POST.get('surnom', '')
            sexe = request.POST.get('sexe', 'Masculin')
            pays_id = request.POST.get('pays_fk')
            pays_nom_brut = request.POST.get('pays', 'Burkina Faso')
            club = request.POST.get('club', '') or ''
            date_naissance_brut = request.POST.get('date_naissance') or None
            date_naissance = convertir_date_fr_vers_iso(date_naissance_brut)
            age = request.POST.get('age') or None
            taille_cm = request.POST.get('taille_cm') or None
            poids_pesee = request.POST.get('poids_pesee') or None
            categorie_id = request.POST.get('categorie')

            categorie = Categorie.objects.filter(id=categorie_id).first() if categorie_id else None
            pays_obj = Pays.objects.filter(id=pays_id).first() if pays_id else None
            
            if pays_obj:
                pays_nom_brut = pays_obj.nom

            # Auto-attribution de la catégorie par le poids si non sélectionnée
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
                pays=pays_nom_brut,
                pays_fk=pays_obj,
                club=club,
                date_naissance=date_naissance,
                age=age,
                taille_cm=taille_cm,
                poids_pesee=poids_pesee,
                categorie=categorie
            )

            if 'photo' in request.FILES:
                b.photo = request.FILES['photo']
            if 'logo_club' in request.FILES:
                b.logo_club = request.FILES['logo_club']
            if 'musique_victoire' in request.FILES:
                b.musique_victoire = request.FILES['musique_victoire']
            b.save()

            messages.success(request, f"Le combattant MMA {b.prenom} {b.nom} ({b.drapeau_emoji} {b.pays}) a été inscrit avec succès !")
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
        'pays_list': pays_list,
    }
    return render(request, 'boxeurs/inscription_combattant.html', context)

