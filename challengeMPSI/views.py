from django.http import HttpResponse, JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404, redirect
from django.template import engines, TemplateSyntaxError
from django.template.loader import get_template
from django.db.models import Max, Sum, Count, Q, F, Value, Func, IntegerField
from .models import Epreuve, Etudiant, Succes, Domaine, Chapitre, Classe
import random as rd
import numpy as np
import datetime as dt
import time
import json

def accueilView(request):
    if request.user.is_authenticated:
        user = request.user
        domaines = Domaine.objects.all()
        chapitres = []
        listeDomaines = []
        for d in domaines:
            data = {"domaine":d}
            cs = Chapitre.objects.filter(domaine=d).order_by("numero")
            if not user.etudiant.classe.spe:
                cs = cs.filter(spe=False)
            data["chapitres"] = list(cs)
            listeDomaines.append(data)
        classe = user.etudiant.classe
        listeJoueurs = classement(classe)
        if user.is_staff:
            derniers_succes = Succes.objects.all().order_by("-date")[:10]
        else:
            derniers_succes = Succes.objects.filter(etudiant__classe=classe, etudiant__estClasse=True).order_by("-date")[:10]
        succes = []
        for s in derniers_succes:
            data = {}
            data["date"] = s.date.strftime("%d/%m/%Y")
            data["time"] = s.date.strftime("%H:%M:%S")
            data["nom"] = s.etudiant.user.first_name + " " + s.etudiant.user.last_name[:2] + "."
            data["etudiantId"] = s.etudiant.id
            data["epreuve"] = s.epreuve.titre
            data["epreuveId"] = s.epreuve.id
            succes.append(data)
        return render(request, 'accueil.html', {"listeDomaines":listeDomaines,
                                                "chapitres":chapitres,
                                                'stats':getStats(user.etudiant),
                                                'evenements':succes})
    else:
        return redirect('login')

def loginView(request):
    if request.user.is_authenticated:
        return redirect('accueil')
    if('username' in request.POST and 'password' in request.POST):
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('accueil')
        else:
            return render(request, 'login.html', {'message': "echec"})
    else:
        return render(request, 'login.html')



def logView(request):
    if request.user.is_authenticated and request.user.is_staff:
        fich = open("log/error.log")
        return HttpResponse(fich.read(), content_type="text/plain");


def adminView(request):
    if request.user.is_authenticated and request.user.is_staff:
        classes = Classe.objects.all()
        data = []
        print(classes)
        for c in classes:
            clst = classement(c)
            data.append({"nom":c.nom, "classement":clst})
        return render(request, "administration.html", {"classes":data,
                                                       'stats':getStats(request.user.etudiant)})
    else:
        redirect("accueil");

def getListeEpreuves(id_domaine, etudiant):
    chapitres = Chapitre.objects.filter(domaine_id=id_domaine).order_by("numero")
    if not etudiant.classe.spe:
        chapitres = chapitres.filter(spe=False)
    data = []
    classe = etudiant.classe;
    if etudiant.user.is_staff:
        nb_etudiants = len(Etudiant.objects.all())
    else:
        nb_etudiants = len(Etudiant.objects.filter(classe=classe, estClasse=True))

    for c in chapitres:
        d = {"chapitre":c}
        epreuves = Epreuve.objects.filter(chapitre=c).order_by("etoiles")
        reussi = Count('succes', filter=Q(succes__etudiant=etudiant))
        epreuves = epreuves.annotate(reussi=reussi)
        d['epreuves'] = epreuves
        if etudiant.user.is_staff:
            validations =  Count("succes")
        else:
            validations =  Count("succes", filter=Q(succes__etudiant__classe=classe, succes__etudiant__estClasse=True))
        epreuves = epreuves.annotate(validations=validations)
        epreuves = epreuves.annotate(nb_total=Value(nb_etudiants/100)).annotate(validations_pc=Round(F('validations')/F('nb_total'), output_field=IntegerField()))
        d['epreuves'] = epreuves
        data.append(d)
    return data



class Round(Func):
    function = 'ROUND'
    template='%(function)s(%(expressions)s, 0)'

def listeEpreuvesView(request, id_domaine):
    if request.user.is_authenticated:
        user = request.user
        data = getListeEpreuves(id_domaine, user.etudiant)
        n_epreuves = sum([len(e["epreuves"]) for e in data])
        domaine = Domaine.objects.get(id=id_domaine)
        classe = user.etudiant.classe
        listeJoueurs = classement(classe)
        return render(request, 'liste.html', {'data':data,
                                              'stats':getStats(user.etudiant),
                                              'domaine': domaine,
                                              'n_epreuves':n_epreuves,
                                              }
                      )
    else:
        return redirect('login')

def epreuveView(request, id_epreuve):
    if request.user.is_authenticated:
        user = request.user
        etudiant = user.etudiant
        epreuve = Epreuve.objects.get(id=id_epreuve)
        if (not etudiant.classe.spe) and epreuve.chapitre.spe:
            return redirect("accueil");
        exec(epreuve.dataFunc, globals())
        data = dataFunc(etudiant.seed)
        valide = Succes.objects.filter(etudiant=etudiant, epreuve=epreuve)
        return render(request, 'epreuve.html', {'epreuve':epreuve,
                                                'data':str(data),
                                                'stats':getStats(etudiant),
                                                'valide':valide,
                                                }
                      )
    else:
        return redirect('login')

def profileView(request, id_etudiant):
    if request.user.is_authenticated:
        user = request.user
        etudiant = request.user.etudiant
        etudiantVu = Etudiant.objects.get(id=id_etudiant)
        if (etudiantVu.classe != etudiant.classe) and not user.is_staff:
            return redirect('accueil')
        domaines = Domaine.objects.all()
        epreuves = {}
        for d in domaines:
            e = getListeEpreuves(d.id, etudiantVu)
            epreuves[d.nom] = e
        return render(request, 'profile.html', {'etudiant':etudiantVu,
                                                'statsVu':getStats(etudiantVu),
                                                'stats':getStats(etudiant),
                                                'epreuves':epreuves
                                                })
    else:
        return redirect('login')

def logoutView(request):
    if request.user.is_authenticated:
        logout(request)
    return loginView(request)

def soumissionReponse(request, id_epreuve):
    if request.user.is_authenticated:
        etudiant = request.user.etudiant
        epreuve = Epreuve.objects.get(id=id_epreuve)
        reponse = request.POST['reponse']
        exec(epreuve.dataFunc, globals())
        exec(epreuve.testFunc, globals())
        data = dataFunc(etudiant.seed)
        result = testFunc(data, reponse)
        if result:
            if not Succes.objects.filter(etudiant=etudiant, epreuve=epreuve):
                succes = Succes.objects.get_or_create(etudiant=etudiant, epreuve=epreuve, date=dt.datetime.now())[0]
                succes.save()
            resultat = '{"resultat":1}'
        else:
            resultat = '{"resultat":0}'
        time.sleep(2)
        return HttpResponse(resultat, content_type="application/json")

    else:
        return redirect('accueil')


def validePar(request, id_epreuve):
    if request.user.is_authenticated:
        etudiant = request.user.etudiant
        succes =  Succes.objects.filter(etudiant__classe=etudiant.classe, etudiant__estClasse=True, epreuve__id=id_epreuve)
        etudiants = []
        for s in succes:
            etudiants.append({
                "prenom":s.etudiant.user.first_name,
                "nom":s.etudiant.user.last_name[:2],
                "id":s.etudiant.id
                })
        return HttpResponse(json.dumps(etudiants), content_type="application/json")


def scoreEtudiant(etudiant):
    res = Succes.objects.filter(etudiant=etudiant).aggregate(score=Sum("epreuve__etoiles"))['score']
    if res is None:
        res = 0
    return res

def classement(classe):
    joueurs = []
    for e in Etudiant.objects.filter(estClasse=True, classe=classe):
        j = {}
        j['first_name'] = e.user.first_name;
        j['last_name_init'] = e.user.last_name[:2]+"."
        j['id'] = e.id
        j['score'] = scoreEtudiant(e)
        joueurs.append(j)
        joueurs.sort(key=lambda j:j['score'], reverse=True)
    return joueurs

def rang(classement, etudiant):
    for i, j in enumerate(classement):
        if j["id"] == etudiant.id:
            return i+1


# Renvoie le classement, le rang du joueur et son score
def getStats(etudiant):
    listeJoueurs = classement(etudiant.classe)
    rangJoueur = rang(listeJoueurs, etudiant)
    score = scoreEtudiant(etudiant)
    domaines = Domaine.objects.all()
    listeDomaines=[]
    for d in domaines:
        data = {"domaine":d}
        s =  Succes.objects.filter(etudiant=etudiant, epreuve__domaine=d).aggregate(score=Sum("epreuve__etoiles"))['score']
        if s == None:
            s = 0
        data['score'] = s
        listeDomaines.append(data)
        if not etudiant.classe.spe:
            data['score_max'] = Epreuve.objects.all().filter(domaine=d).filter(chapitre__spe=False).aggregate(total=Sum("etoiles"))['total']
        else:
            data['score_max'] = Epreuve.objects.all().filter(domaine=d).aggregate(total=Sum("etoiles"))['total']
        if data["score_max"]==None:
            data['score_max'] = 1
        data['pourcent'] = int(np.round(100*data['score']/data['score_max']))
    return {'liste':listeJoueurs, 'rang':rangJoueur, 'score':score, 'domaines':listeDomaines}

