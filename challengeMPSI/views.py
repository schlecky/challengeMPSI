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
    else:
        return redirect('accueil')


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


def adminViewResultats(request):
    if request.user.is_authenticated and request.user.is_staff:
        classes = Classe.objects.all()
        data = []
        for c in classes:
            clst = classement(c)
            data.append({"nom":c.nom, "classement":clst})
        return render(request, "admin_resultats.html", {"classes":data,
                                                       'stats':getStats(request.user.etudiant)})
    else:
        redirect("accueil");

def adminViewEpreuves(request):
    if request.user.is_authenticated and request.user.is_staff:
        domaines = Domaine.objects.all()
        return render(request, "admin_epreuves.html", {"domaines":domaines})
    else:
        redirect("accueil");


def adminViewEtudiants(request):
    if request.user.is_authenticated and request.user.is_staff:
        classes = Classe.objects.all()
        return render(request, "admin_etudiants.html", {"classes":classes})
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
        for k in data:
            if type(data[k]).__module__ == 'numpy':
                data[k] = data[k].item()
        valide = Succes.objects.filter(etudiant=etudiant, epreuve=epreuve)
        return render(request, 'epreuve.html', {'epreuve':epreuve,
                                                'data':str(data),
                                                'stats':getStats(etudiant),
                                                'valide':valide,
                                                }
                      )
    else:
        return redirect('login')


def adminViewEditEpreuve(request, id_epreuve):
    if request.user.is_authenticated and request.user.is_staff:
        if request.method == 'GET':
            epreuve = Epreuve.objects.get(id=id_epreuve)
            return render(request, 'edit_epreuve.html', {'epreuve':epreuve})
        elif request.method == 'POST':
            res = majEpreuve(request.body, id_epreuve)
            return HttpResponse(json.dumps({'resultat':res}), content_type="application/json")
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


# Reçoit une epreuve mise à jour et l'enregistre
def majEpreuve(data, id_epreuve):
    epreuve = Epreuve.objects.get(id=id_epreuve)
    if epreuve is not None:
        e = json.loads(data)
        epreuve.titre = e["titre"]
        epreuve.etoiles = int(e["etoiles"])
        epreuve.enonce = e['enonce']
        epreuve.dataFunc = e['dataFunc']
        epreuve.testFunc = e['testFunc']
        epreuve.solution = e['solution']
        epreuve.save()
        return True
    return False


# renvoie la liste des étudiants ayant validé une épreuve au format JSON
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

# Renvoie la liste des classes au format JSON
def listeClasses(request):
    if request.user.is_authenticated and request.user.is_staff:
        classes = Classe.objects.all()
        classesData = []
        for c in classes:
            classesData.append({
                "nom":c.nom,
                "id":c.id
                })
        return HttpResponse(json.dumps(classesData), content_type="application/json")

# Renvoie la liste des étudiants au format JSON
def listeEtudiants(request, id_classe):
    if request.user.is_authenticated and request.user.is_staff:
        etudiants = Etudiant.objects.filter(classe__id=id_classe)
        etudiantsData = []
        for e in etudiants:
            etudiantsData.append({
                "nom":e.user.last_name,
                "prenom":e.user.first_name,
                "id":e.id
                })
        return HttpResponse(json.dumps(etudiantsData), content_type="application/json")

# Renvoie les données d'un étudiant au format JSON
def getEtudiant(request, id_etudiant):
    if request.user.is_authenticated and request.user.is_staff:
        etudiant = Etudiant.objects.get(id=id_etudiant)
        data = {}
        data["id"] = etudiant.id
        data["nom"] = etudiant.user.last_name
        data["prenom"] = etudiant.user.first_name
        data["email"] = etudiant.user.email
        data["username"] = etudiant.user.username
        data["classe"] = etudiant.classe.id

        return HttpResponse(json.dumps(data), content_type="application/json")

# Renvoie la liste des domaines au format JSON
def listeDomaines(request):
    if request.user.is_authenticated and request.user.is_staff:
        domaines = Domaine.objects.all()
        domainesData = []
        for d in domaines:
            domainesData.append({
                "nom":d.nom,
                "nom_affiche":d.nom_affiche,
                "numero":d.numero,
                "description":d.description,
                "id":d.id
                })
        return HttpResponse(json.dumps(domainesData), content_type="application/json")

# Renvoie la liste des épreuves au format JSON
def listeEpreuves(request, id_domaine):
    if request.user.is_authenticated and request.user.is_staff:
        epreuves = Epreuve.objects.filter(domaine__id=id_domaine)

        chapitres = Chapitre.objects.filter(domaine__id=id_domaine)
        data = []
        for c in chapitres:
            d = {"chapitre":c.id}
            epreuves = Epreuve.objects.filter(chapitre=c).order_by("etoiles")
            epreuvesData = []
            for e in epreuves:
                epreuvesData.append({"titre":e.titre, "id":e.id})
            d['epreuves'] = epreuvesData
            data.append(d)
        return HttpResponse(json.dumps(data), content_type="application/json")

# Renvoie les données d'une épreuve au format JSON
def getEpreuve(request, id_epreuve):
    if request.user.is_authenticated and request.user.is_staff:
        epreuve = Epreuve.objects.get(id=id_epreuve)
        data = {}
        data["titre"] = epreuve.titre
        data["domaine"] = epreuve.domaine.id
        data["chapitre"] = epreuve.chapitre.id
        data["etoiles"] = epreuve.etoiles
        data["enonce"] = epreuve.enonce
        data["testFunc"] = epreuve.testFunc
        data["solution"] = epreuve.solution
        return HttpResponse(json.dumps(data), content_type="application/json")

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

