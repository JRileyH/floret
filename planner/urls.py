from django.urls import path

from planner import views

urlpatterns = [
    path("", views.index, name="index"),
    path("plants/", views.plant_list, name="plant_list"),
    # Garden API endpoints
    path("garden/save/", views.save_garden, name="garden_save"),
    path("garden/load/<uuid:garden_id>/", views.load_garden, name="garden_load"),
    path("garden/list/", views.list_gardens, name="garden_list"),
]
