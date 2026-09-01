from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Utilisateur, Role

def connexion_vue(request):
    next_url = request.GET.get('next')
    if request.user.is_authenticated:
        if next_url and '/admin/' not in next_url:
            return redirect(next_url)
        return rediriger_selon_role(request.user)

    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user is not None:
            login(request, user)
            if next_url and '/admin/' not in next_url:
                return redirect(next_url)
            return rediriger_selon_role(user)
        else:
            messages.error(request, 'Nom d utilisateur ou mot de passe incorrect.')
            
    return render(request, 'comptes/connexion.html')

def deconnexion_vue(request):
    logout(request)
    return redirect('connexion')

def rediriger_selon_role(user):
    # Traiter d'abord le rôle attribué à l'utilisateur
    if user.role:
        code = str(user.role.code).upper()
        nom = str(user.role.nom).lower()

        if code == 'JUGE_PRINCIPAL' or 'principal' in nom:
            return redirect('table_juge_principal')
        elif code in ['JURY', 'JUGE', '01'] or 'juge' in nom or 'jury' in nom:
            return redirect('tablette_juge')
        elif code == 'ADMIN' or 'admin' in nom:
            return redirect('admin_dashboard')

    # Si aucun rôle spécifique n'est défini, vérifier le statut superutilisateur/staff
    if user.is_superuser or user.is_staff:
        return redirect('admin_dashboard')

    return redirect('tablette_juge')


@login_required
def admin_dashboard_vue(request):
    # Sécurité : Si un juge (non superutilisateur) tente d'accéder directement au dashboard admin
    if request.user.role and not request.user.is_superuser:
        code = str(request.user.role.code).upper()
        nom = str(request.user.role.nom).lower()

        if code == 'JUGE_PRINCIPAL' or 'principal' in nom:
            return redirect('table_juge_principal')
        elif code in ['JURY', 'JUGE', '01'] or 'juge' in nom or 'jury' in nom:
            return redirect('tablette_juge')

    from applications.boxeurs.models import Boxeur, Categorie
    from applications.arbitres.models import ArbitreCentral
    from applications.combats.models import Combat, Evenement

    utilisateurs = Utilisateur.objects.all().select_related('role')
    boxeurs = Boxeur.objects.all().select_related('categorie')
    categories = Categorie.objects.all()
    arbitres = ArbitreCentral.objects.all()
    combats = Combat.objects.all().select_related('boxeur_rouge', 'boxeur_bleu', 'evenement')
    evenements = Evenement.objects.all()

    combat_actif = Combat.objects.filter(statut='EN_COURS').first()
    if not combat_actif:
        combat_actif = Combat.objects.filter(statut='TERMINE').order_by('-id').first()
    if not combat_actif:
        combat_actif = Combat.objects.first()

    context = {
        'utilisateurs': utilisateurs,
        'boxeurs': boxeurs,
        'categories': categories,
        'arbitres': arbitres,
        'combats': combats,
        'evenements': evenements,
        'combat_actif': combat_actif,
    }
    return render(request, 'comptes/admin_dashboard.html', context)