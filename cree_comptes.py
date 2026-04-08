import os
import django
# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'challengeMPSI.settings')
django.setup()

#from django.core.wsgi import get_wsgi_application
#application = get_wsgi_application()

from django.contrib.auth.models import User
from challengeMPSI.models import Etudiant, Classe
import csv
import random as rd


csvfile = open("mdp_MPSI2_2025-2026.csv","r")
reader = csv.reader(csvfile, delimiter=';')

for row in reader:
    mdp = row[3].strip()
    username = row[2].strip()
    last_name = row[0].strip()
    first_name = row[1].strip()
    email = row[4].strip()
    u = User.objects.get_or_create(username=username)[0]
    u.last_name = last_name
    u.first_name = first_name
    u.email = email
    u.set_password(mdp)
    u.save()
    classe = Classe.objects.filter(nom="MPSI 2 -- 2025-2026")[0]
    e = Etudiant.objects.get_or_create(classe = classe, user=u)[0]
    e.niveau = 0
    e.points = 0
    e.seed = rd.randint(0, 100000)
    e.save()
    print(last_name, first_name, username, mdp, email)
csvfile.close()
