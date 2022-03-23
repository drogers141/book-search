from django.urls import path

from . import views

urlpatterns = [

    path('', views.home, name='home'),
    path('search/', views.search, name='search'),
    # enables viewing the content of a book
    path('view/<int:document>/<int:page>/', views.view_page, name='view-page'),
]
