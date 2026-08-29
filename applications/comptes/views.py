from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Utilisateur, Role

def connexion_vue(request):
    next_url = request.GET.get('next')
    if request.user.is_authenticated:
        if next_url:
            return redirect(next_url)
        return rediriger_selon_role(request.user)

    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user is not None:
            login(request, user)
            if next_url:
                return redirect(next_url)
            return rediriger_selon_role(user)
        else:
            messages.error(request, 'Nom d utilisateur ou mot de passe incorrect.')
            
    return render(request, 'comptes/connexion.html')

def deconnexion_vue(request):
    logout(request)
    return redirect('connexion')

def rediriger_selon_role(user):
    if user.is_superuser or user.is_staff or (user.role and user.role.code == 'ADMIN'):
        return redirect('admin_dashboard')
    elif user.role and user.role.code == 'JUGE_PRINCIPAL':
        return redirect('table_juge_principal')
    elif user.role and user.role.code == 'JURY':
        return redirect('tablette_juge')
    return redirect('admin_dashboard')


@login_required
def admin_dashboard_vue(request):
    from applications.boxeurs.models import Boxeur, Categorie
    from applications.arbitres.models import ArbitreCentral
    from applications.combats.models import Combat, Evenement

    utilisateurs = Utilisateur.objects.all().select_related('role')
    boxeurs = Boxeur.objects.all().select_related('categorie')
    categories = Categorie.objects.all()
    arbitres = ArbitreCentral.objects.all()
    combats = Combat.objects.all().select_related('boxeur_rouge', 'boxeur_bleu', 'evenement')
    evenements = Evenement.objects.all()

    context = {
        'utilisateurs': utilisateurs,
        'boxeurs': boxeurs,
        'categories': categories,
        'arbitres': arbitres,
        'combats': combats,
        'evenements': evenements,
    }
    return render(request, 'comptes/admin_dashboard.html', context)