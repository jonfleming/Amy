from django.urls import path

from . import views

app_name = 'chat'
urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('register', views.register_request, name='register'),
    path("login", views.login_request, name="login"),
    path("logout", views.logout_request, name= "logout"),    
    path('list', views.IndexView.as_view(), name='list'),
    path('<int:pk>/', views.DetailView.as_view(), name='detail'),
    path('<int:pk>/results/', views.ResultsView.as_view(), name='results'),
    path('session/', views.session, name='session'),
]
