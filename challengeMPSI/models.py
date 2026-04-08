from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_delete
from django.dispatch import receiver

# Create your models here.
class Classe(models.Model):
    nom = models.TextField(default="MPSI 1 -- 2023-2024")
    spe = models.BooleanField(default=False)
    def __str__(self):
        return self.nom

class Etudiant(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    seed = models.IntegerField(default=0)
    classe = models.ForeignKey(Classe, on_delete=models.PROTECT)
    points = models.IntegerField(default=0)
    estClasse = models.BooleanField(default=True)

    def __str__(self):
        return self.user.last_name+" "+self.user.first_name+" -- "+str(self.classe)

class Domaine(models.Model):
    nom = models.TextField(default="Divers")
    nom_affiche = models.TextField(default="Divers")
    numero = models.IntegerField(default=0)
    description = models.TextField(default="")
    # image = models.ImageField(upload_to="images", default="images/defaultDomaine.png")
    image = models.TextField(default="optique.png")
    def __str__(self):
        return self.nom

class Chapitre(models.Model):
    nom = models.TextField(default="Chapitre 1")
    numero = models.IntegerField(default=0)
    domaine = models.ForeignKey(Domaine, on_delete = models.CASCADE)
    spe = models.BooleanField(default=False)
    def __str__(self):
        return str(self.domaine)+"-"+self.nom

class Epreuve(models.Model):
    titre = models.TextField(default="")
    domaine = models.ForeignKey(Domaine, on_delete=models.PROTECT)
    chapitre = models.ForeignKey(Chapitre, on_delete=models.PROTECT, null=True)
    etoiles = models.IntegerField(default=1)
    enonce = models.TextField(default="")
    dataFunc = models.TextField(default="def dataFunc(seed):\n    rd.seed(seed)\n    data={}\n    return data")
    testFunc = models.TextField(default="""def testFunc(data, reponse):
    rep = float(reponse)
    return np.abs((rep-repOK)/repOK)<1e-3""")
    solution = models.TextField(default="Pas de solution pour l'instant")

    def __str__(self):
        return str(self.domaine)+"-"+self.titre+" "+"★"*self.etoiles

def image_path(instance, filename):
    return "img/{0}/{1}".format(instance.imageDomaine.nom, filename)

class Image(models.Model):
    imageDomaine = models.ForeignKey(Domaine, on_delete=models.PROTECT, related_name='images')
    image = models.ImageField(upload_to=image_path)


@receiver(post_delete, sender=Image)
def delete_file_when_image_deleted(sender, instance, **kwargs):
    if instance.image:
        instance.image.delete(False)

class Succes(models.Model):
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE)
    epreuve = models.ForeignKey(Epreuve, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return str(self.etudiant)+" -- E"+str(self.epreuve.id) + "--" + str(self.date)
