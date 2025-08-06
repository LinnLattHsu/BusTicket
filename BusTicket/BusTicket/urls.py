"""
URL configuration for BusTicket project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.contrib import admin
from django.urls import path

from django.urls import path,re_path,include
from django.views.generic import TemplateView
from myapp import views

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('', views.home, name="home"),
    # path('search/',views.search_routes, name='search_routes'),
    # path('home', views.home, name="home"),
    # path('login', views.user_login, name="login"),
    # path('findbus', views.findbus, name="findbus"),
    # path('bookings', views.bookings, name="bookings"),
    # path('cancellings', views.cancellings, name="cancellings"),
    # path('seebookings', views.seebookings, name="seebookings"),
    # path('signup', views.signup, name="signup"),
    # path('signin', views.signin, name="signin"),
    # path('success', views.success, name="success"),
    # path('download_ticket/<int:booking_id>/', views.download_ticket, name='download_ticket'),
    # path('signout', views.signout, name="signout"),
    # path('bookings/payement/<int:booking_id>/', views.payment_page, name='payement'),
    # path('bookings/payement/success/<int:booking_id>/', views.payment_success, name='payment_success'),
    # path('bookings/payement/success/<int:booking_id>/feedback/', views.FeedbackForm, name='feedback'),
    # # URL for feedback form
    # path('bookings/payement/success/<int:booking_id>/feedback/list/', views.FeedbackList, name='feedback_list'),
    #
    # path('seatselection',views.seat_selection),
    # path('select-trip/<int:bus_id>/',views.seat_selection,name='select_trip'),
    #

    # admin url call
    path('admindashboard/',views.admin_dashboard),
    path('admindashboard/user_home/',views.user_home),
]
