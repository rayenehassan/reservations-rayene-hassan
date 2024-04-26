from django.contrib import admin

# Register your models here.

from .models import Gare, Trajet, Client, Passager, Reservation

admin.site.register(Gare)
admin.site.register(Trajet)
admin.site.register(Client)
admin.site.register(Passager)
admin.site.register(Reservation)


