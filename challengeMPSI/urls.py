"""
URL configuration for challengeMPSI project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.accueilView,name='accueil'),
    path('administration/', views.adminViewResultats,name='admin'),
    path('administration/resultats', views.adminViewResultats,name='adminResultats'),
    path('administration/epreuves', views.adminViewEpreuves,name='adminEpreuves'),
    path('administration/etudiants', views.adminViewEtudiants,name='adminEtudiants'),

    path('administration/editEpreuve/<int:id_epreuve>/', views.adminViewEditEpreuve,name='editEpreuve'),
    path(r'administration/addEpreuve/<int:id_chapitre>/', views.adminAddEpreuve, name='addEpreuve'),
    path(r'administration/delEpreuve/<int:id_epreuve>/', views.adminDelEpreuve, name='delEpreuve'),


    # API
    path(r'api/classes/', views.listeClasses, name='listeClasses'),
    path(r'api/etudiants/<int:id_classe>/', views.listeEtudiants, name='listeEtudiants'),
    path(r'api/etudiant/<int:id_etudiant>/', views.getEtudiant, name='getEtudiants'),
    path(r'api/etudiant/<int:id_etudiant>/motdepasse/', views.setMotDePasse, name='setMotDePasse'),
    path(r'api/domaines/', views.listeDomaines, name='listeDomaines'),
    path(r'api/epreuves/<int:id_domaine>/', views.listeEpreuves, name='listeEpreuves'),
    path(r'api/epreuve/<int:id_epreuve>/', views.getEpreuve, name='getEpreuve'),
    path(r'api/images/<int:id_domaine>/', views.getImages, name='getImages'),
    path(r'api/uploadimage/<int:id_domaine>/', views.uploadImage, name='uploadImage'),
    path(r'api/classe/', views.gestClasse, name='gestClasse'),



    path(r'domaine/<int:id_domaine>/', views.listeEpreuvesView, name='listeEpreuves'),
    path(r'epreuve/<int:id_epreuve>/', views.epreuveView, name='epreuve'),
    path(r'profile/<int:id_etudiant>/', views.profileView, name='profile'),
    path(r'login/', views.loginView, name='login'),
    path(r'logout/', views.logoutView, name='logout'),
    path(r'check_epreuve/<int:id_epreuve>/', views.soumissionReponse, name='check_epreuve'),
    path(r'valide_par/<int:id_epreuve>/', views.validePar, name='valide_par'),
    path(r'log/', views.logView, name='log'),
]
 

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
