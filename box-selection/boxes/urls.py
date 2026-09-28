from django.urls import path

from . import views

urlpatterns = [
    path("recommend-box/", views.recommend_box, name="recommend-box"),
]
