import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "reservations.settings")
import django
django.setup()

from reservationhub.models import Gare, Trajet, Passager, Client, Reservation

Reservation.objects.all().delete()
Passager.objects.all().delete()
Client.objects.all().delete()