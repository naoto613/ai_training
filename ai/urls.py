from django.urls import path
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    path('home/', views.home, name='home'),
    path('introduction/', views.introduction, name='introduction'),
    path('list/', views.list, name='list'),
    path('back/', views.back, name='back'),
    path('wait/', views.wait, name='wait'),
    path('facejudge/', views.facejudge, name='facejudge'),
    path('predict/', views.predict, name='predict'),
    path('kakugen/', views.kakugen, name='kakugen'),
    path('kakugen_result/', views.kakugen_result, name='kakugen_result'),
    path('chatbot/', views.talk_do, name='chatbot'),
]