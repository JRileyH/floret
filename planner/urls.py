from django.urls import path

from planner import views

urlpatterns = [
    path("", views.index, name="index"),
    path("plants/", views.plant_list, name="plant_list"),
    path("summary/", views.garden_summary, name="garden_summary"),
    # Garden API endpoints
    path("api/garden-plants/", views.get_garden_plants, name="get_garden_plants"),
    path("garden/save/", views.save_garden, name="garden_save"),
    path("garden/load/<uuid:garden_id>/", views.load_garden, name="garden_load"),
    path("garden/list/", views.list_gardens, name="garden_list"),
]
