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
    path('', views.home, name="home"),
    path('search/',views.search_routes, name='search_routes'),
    path('select-trip/<int:schedule_id>/', views.seat_selection, name='select_trip'),
    path('select-seats/<int:schedule_id>/submit/', views.submit_seats, name='submit_seats'),
    path('home', views.home, name="home"),
    path('login/', views.user_login, name="login"),
    path('signup/', views.signup, name="signup"),
    path('signin/', views.signin, name="signin"),
    path('signout/', views.signout, name="signout"),

    # path('findbus', views.findbus, name="findbus"),
    # path('bookings', views.bookings, name="bookings"),
    # path('cancellings', views.cancellings, name="cancellings"),
    # path('seebookings', views.seebookings, name="seebookings"),

    # path('success', views.success, name="success"),
    # path('download_ticket/<int:booking_id>/', views.download_ticket, name='download_ticket'),

    # path('bookings/payement/<int:booking_id>/', views.payment_page, name='payement'),
    # path('bookings/payement/success/<int:booking_id>/', views.payment_success, name='payment_success'),
    # path('bookings/payement/success/<int:booking_id>/feedback/', views.FeedbackForm, name='feedback'),
    # URL for feedback form
    # path('bookings/payement/success/<int:booking_id>/feedback/list/', views.FeedbackList, name='feedback_list'),
    #
    # path('seatselection',views.seat_selection),
    #

    # admin url call
    path('admindashboard/',views.admin_dashboard,name='admin_dashboard'),
    path('admindashboard/user_home/',views.user_home,name='user_home'),
    path('admindashboard/user_home/<int:user_id>/delete/', views.soft_delete_user, name='soft_delete_user'),
    path('admindashboard/operator_home/',views.operator_home,name='operator_home'),
    path('admindashboard/operator_home/add_new_operator/',views.add_operator,name='operator_add'),
    path('admindashboard/operator_home/<int:operator_id>/update/',views.update_operator,name='operator_update'),
    path('admindashboard/operator_home/<int:operator_id>/delete/',views.delete_operator,name='operator_delete'),
    path('admindashboard/route_home/',views.route_home,name='route_home'),
    path('admindashboard/route_home/add_new_route/',views.add_route,name='route_add'),
    path('admindashboard/route_home/<int:route_id>/update/',views.update_route,name='route_update'),
    path('admindashboard/route_home/<int:route_id>/delete/',views.delete_route,name='route_delete'),
]
