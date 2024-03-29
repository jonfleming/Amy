from django.urls import path

from . import views

app_name = 'chat'
urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('register', views.register_request, name='register'),
    path('login', views.login_request, name='login'),
    path('logout', views.logout_request, name= 'logout'),    
    path('session/', views.session, name='session'),
    path('password_reset', views.password_reset_request, name='password_reset'),
    path('home', views.homepage, name='homepage'),
    path('transcript/<offset>', views.Transcript.as_view(), name='transcript'),
    path('summary/', views.summary, name='summary'),
    path('profile/', views.profile_view, name='profile_view'),
    path('reindex/', views.reindex, name='reindex')
]
