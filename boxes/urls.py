from django.urls import path

from . import views

urlpatterns = [
    path("recommend-box/", views.recommend_box, name="recommend-box"),
    path("orders/", views.create_order, name="order-create"),
    path("orders/<int:pk>/", views.order_detail, name="order-detail"),
]
