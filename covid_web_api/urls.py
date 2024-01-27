from django.urls import path, include
from rest_framework import routers
from webhooks.views import CaseViewSet
from webhooks import views

router = routers.DefaultRouter()
router.register(r'cases', CaseViewSet, basename='cases')

urlpatterns = [
    path('', include(router.urls)),
    path('home',view=views.home_page,name="home"),
]
