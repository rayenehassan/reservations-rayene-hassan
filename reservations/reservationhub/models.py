from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Gare(models.Model):
    nom = models.CharField(max_length=100)
    def __str__(self):
        return self.nom

class Trajet(models.Model):
    gare_depart = models.ForeignKey(Gare, related_name='trajets_de_depart', on_delete=models.CASCADE)
    date_heure_depart = models.DateTimeField()
    gare_arrivee = models.ForeignKey(Gare, related_name='trajets_d_arrivee', on_delete=models.CASCADE)
    date_heure_arrivee = models.DateTimeField()
    def __str__(self):
        return f"{self.gare_depart} -> {self.gare_arrivee}"

class Passager(models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    date_naissance = models.DateField()
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    def __str__(self):
        return f"{self.prenom} {self.nom}"

class Client(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    adresse = models.CharField(max_length=255)
    telephone = models.CharField(max_length=20)
    passager = models.ForeignKey(Passager, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"

    
class Reservation(models.Model):
    date_reservation = models.DateField()
    numero_reservation = models.CharField(max_length=50)
    numero_place = models.IntegerField(default=0)
    passager = models.ForeignKey(Passager, on_delete=models.CASCADE, null=True)
    trajet = models.ForeignKey(Trajet, on_delete=models.CASCADE)
    utilisateur_reservation = models.ForeignKey(Client, on_delete=models.CASCADE)
    def __str__(self):
        return f"Réservation {self.numero_reservation} - {self.passager}"
    


    
    
    


