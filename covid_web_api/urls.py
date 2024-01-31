from django.urls import path, include
from rest_framework import routers
from webhooks.views import CaseViewSet
from webhooks import views

router = routers.DefaultRouter()
router.register(r'cases', CaseViewSet, basename='cases')

urlpatterns = [
    path('', include(router.urls)),
    path('predict_cases/<str:date>/<str:state>', CaseViewSet.as_view({'get': 'predict_cases'}), name='predict_cases'),
    path('home',view=views.home_page,name="home"),
    path('state/<str:state>/', views.state_page, name='state_page'),
]
