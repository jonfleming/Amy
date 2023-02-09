from django.urls import path

from . import views

app_name = 'chat'
urlpatterns = [
    path('', views.session, name='session'),
    path('list', views.IndexView.as_view(), name='list'),
    path('<int:pk>/', views.DetailView.as_view(), name='detail'),
    path('<int:pk>/results/', views.ResultsView.as_view(), name='results'),
    path('session/', views.session, name='session'),
]
