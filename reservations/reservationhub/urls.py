from django.urls import path
from . import views
from .views import register
from django.contrib.auth import views as auth_views

app_name = "reservationhub"

urlpatterns =[
    path("trajets/", views.trajets, name='trajets'),
    path("recherche_reservations/", views.recherche_reservations, name='recherche_reservations'),
    path('details_trajet/<int:trajet_id>/', views.details_trajet, name='details_trajet'),
    path('details_trajet_user/<int:trajet_id>/', views.details_trajet_user, name='details_trajet_user'),
    path("mes_reservations/", views.mes_reservations, name='mes_reservations'),
    path("login/", auth_views.LoginView.as_view(), name='login'),
    path('trajets/edit_reservation/<int:trajet_id>/', views.edit_reservation, name='edit_reservation'),
    path('trajets/nouvelle_reservation', views.edit_reservation, name='nouvelle_reservation'),
    path('creer_passager/', views.creer_passager, name='creer_passager'),
    path('mes_reservations/modifier/<int:reservation_id>/', views.modifier_reservation, name='modifier_reservation'),
    path('register/', register, name='register'),
    path('accueil/', views.homepage, name='accueil'),
    path('accueil_connecte/', views.homepage_connecte, name='accueil_connecte'),
    path('reservationhub/', views.homepage, name='accueil'),
    path('', views.homepage, name='accueil'),
   
    # URLS vers les différents charts possibles
    path('dashboard/suivi_reservations/<int:numero_trajet>/',views.get_charts_trajet, name='get_charts_trajet'),
    path('dashboard/suivi_reservations/<int:gare_id>/',views.get_charts_gare, name='get_charts_gare'),
    path('dashboard/<int:numero_trajet>/', views.trajets_chart_view, name='trajets_chart_view'),
]

