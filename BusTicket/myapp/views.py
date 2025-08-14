# D:\bus_ticket\BusTicket\BusTicket\myapp\views.py

from django.shortcuts import render, redirect
from django.db.models import Q, Count
from datetime import datetime
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from .models import User, Operator, Bus, Route, Schedule, Booking, Ticket, Seat_Status
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from .forms import UserLoginForm, UserRegisterForm
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from io import BytesIO
import qrcode
from django.shortcuts import get_object_or_404
from .forms import BookingForm, OperatorForm, RouteForm, BusForm, ScheduleForm
from django.contrib.auth.hashers import make_password
from django.db import IntegrityError

# In home page, when you enter origin,destination and date this function will search for available routes
def search_routes(request):
    # Always provide dropdown lists
    origins = Route.objects.values_list('origin', flat=True).distinct()
    destinations = Route.objects.values_list('destination', flat=True).distinct()

    context = {'origins': origins, 'destinations': destinations}

    # Accept both GET and POST (GET useful for header quick-search)
    data = request.GET if request.method == 'GET' and request.GET else request.POST

    if data:
        origin_r = data.get('origin', '').strip()
        dest_r = data.get('destination', '').strip()
        date_r = data.get('date') or data.get('departure_date')
        number_of_seats = data.get('number_of_seats')

        if not dest_r and data.get('to'):
            dest_r = data.get('to').strip()

        context.update({
            'data': data,
            'selected_origin': origin_r,
            'selected_destination': dest_r,
            'selected_date': date_r,
            'number_of_seats': number_of_seats,
        })

        if not (origin_r and dest_r and date_r):
            context.update({'error': 'Please enter origin, destination and date.', 'data': data})
            return render(request, 'base.html', context)

        try:
            date_obj = datetime.strptime(date_r, "%Y-%m-%d").date()
        except ValueError:
            context.update({'error': 'Invalid date format.', 'data': data})
            return render(request, 'base.html', context)

        schedules = Schedule.objects.filter(
            route__origin__iexact=origin_r,
            route__destination__iexact=dest_r,
            date=date_obj,
            del_flag=0,
            route__del_flag=0,
            bus__del_flag=0
        )

        if schedules.exists():
            return render(request, 'available_routes.html', {
                'schedules': schedules,
                'origins': origins,
                'destinations': destinations,
                'selected_origin': origin_r,
                'selected_destination': dest_r,
                'selected_date': date_r,
                'selected_seat': number_of_seats,
            })
        else:
            context.update({'error': 'No available Bus Schedule for entered Route and Date', 'data': data})
            return render(request, 'base.html', {'context': context})

    return render(request, 'base.html', context)

def seat_selection(request, schedule_id):
    selected_bus = Schedule.objects.get(id=schedule_id)
    seats = request.GET.get('number_of_seats')
    seats = int(seats)
    total_price = Decimal(seats) * selected_bus.price
    context = {
        'selected_bus': selected_bus,
        'origin': selected_bus.route.origin,
        'destination': selected_bus.route.destination,
        'date': selected_bus.date,
        'seats': seats,
        'total_price': total_price,
        'schedule_id': selected_bus.id,
    }
    return render(request, 'seat_selection.html', context)

def submit_seats(request, schedule_id):
    if request.method == "POST":
        selected_seats = request.POST.getlist('selected_seats')
        return HttpResponse(f"Selected seats: {', '.join(selected_seats)}")
    return HttpResponse(status=405)

def user_login(request):
    if request.user.is_authenticated:
        return render(request, 'home.html')
    else:
        return render(request, 'signin.html')

def home(request):
    bookings = Bus.objects.all()
    return render(request, 'base.html', {'bookings': bookings})

def signup(request):
    context = {}
    if request.method == 'POST':
        name_r = request.POST.get('name')
        email_r = request.POST.get('email')
        password_r = request.POST.get('password')
        nrc_r = request.POST.get('nrc')
        address_r = request.POST.get('address')
        phone_no_r = request.POST.get('phone_no')

        if User.objects.filter(name=name_r).exists():
            context["error"] = "Username already exists, please choose another one."
            return render(request, 'signup.html', context)

        if User.objects.filter(email=email_r).exists():
            context["error"] = "Email is already registered, please choose another one."
            return render(request, 'signup.html', context)

        if nrc_r and User.objects.filter(nrc=nrc_r).exists():
            context['error'] = "NRC already exists."
            return render(request, 'signup.html', context)

        try:
            user = User.objects.create(
                name=name_r,
                email=email_r,
                password=make_password(password_r),
                nrc=nrc_r,
                address=address_r,
                phone_no=phone_no_r
            )
            if user:
                login(request, user)
                return render(request, 'thank.html')
        except IntegrityError:
            context["error"] = "An error occurred. Please try again."
            return render(request, 'signup.html', context)

    return render(request, 'signup.html', context)

def signin(request):
    context = {}
    if request.method == 'POST':
        name_r = request.POST.get('name')
        password_r = request.POST.get('password')
        user = authenticate(request, username=name_r, password=password_r)
        if user:
            login(request, user)
            context["user"] = name_r
            context["id"] = request.user.id
            return render(request, 'success.html', context)
        else:
            context["error"] = "Provide valid credentials"
            return render(request, 'signin.html', context)
    else:
        context["error"] = "You are not logged in"
        return render(request, 'signin.html', context)

def signout(request):
    context = {}
    logout(request)
    context['error'] = "You have been logged out"
    return render(request, 'signin.html', context)

# Admin Dashboard
def admin_dashboard(request):
    no_of_users = User.objects.filter(del_flag=0).count()
    no_of_buses = Bus.objects.filter(del_flag=0).count()
    no_of_routes = Route.objects.filter(del_flag=0).count()
    no_of_operators = Operator.objects.filter(del_flag=0).count()
    no_of_schedules = Schedule.objects.filter(del_flag=0).count()
    no_of_bookings = Booking.objects.all().count()
    no_of_tickets = Ticket.objects.all().count()

    bus_query = request.GET.get('bus_number', '')
    route_query = request.GET.get('route', '')
    selected_schedule = None
    seat_status_list = []

    if bus_query and route_query:
        try:
            selected_schedule = Schedule.objects.get(
                Q(bus__license_no__iexact=bus_query) &
                (Q(route__origin__iexact=route_query) | Q(route__destination__iexact=route_query))
            )
            seat_status_list = Seat_Status.objects.filter(schedule=selected_schedule).order_by('seat_no')
        except Schedule.DoesNotExist:
            selected_schedule = None
            seat_status_list = []

    return render(request, 'admin/dashboard.html', {
        'no_of_users': no_of_users,
        'no_of_buses': no_of_buses,
        'no_of_routes': no_of_routes,
        'no_of_operators': no_of_operators,
        'no_of_schedules': no_of_schedules,
        'no_of_bookings': no_of_bookings,
        'no_of_tickets': no_of_tickets,
        'bus_query': bus_query,
        'route_query': route_query,
        'selected_schedule': selected_schedule,
        'seat_status_list': seat_status_list
    })

def user_home(request):
    users = User.objects.all().order_by('name')
    return render(request, 'admin/user_home.html', {'users': users})

def soft_delete_user(request, user_id):
    user_info = User.objects.get(user_id=user_id)
    user_info.del_flag = 1 if user_info.del_flag == 0 else 0
    user_info.save()
    return redirect('user_home')

# operator home page in admin
def operator_home(request):
    search_query = request.GET.get('search', '')
    operators = Operator.objects.all()
    if search_query:
        operators = operators.filter(Q(operator_name__icontains=search_query))
    context = {
        'operators': operators,
        'search_query': search_query,
    }
    return render(request, 'admin/operator_home.html', context)

def add_operator(request):
    if request.method == 'POST':
        operator_form = OperatorForm(request.POST)
        if operator_form.is_valid():
            operator_form.save()
            return HttpResponseRedirect('/admindashboard/operator_home/')
    else:
        operator_form = OperatorForm()
    return render(request, 'admin/operator_add_form.html', {'form': operator_form})

def update_operator(request, operator_id):
    operator_info = Operator.objects.get(pk=operator_id)
    if request.method == 'POST':
        operator_form = OperatorForm(request.POST, instance=operator_info)
        if operator_form.is_valid():
            operator_form.save()
            return redirect('operator_home')
    else:
        operator_form = OperatorForm(instance=operator_info)
    return render(request, 'admin/operator_update.html', {'operator_form': operator_form})

def delete_operator(request, operator_id):
    operator_info = Operator.objects.get(id=operator_id)
    operator_info.del_flag = 1 if operator_info.del_flag == 0 else 0
    operator_info.save()
    return redirect('operator_home')

# route home page in admin
def route_home(request):
    origin_query = request.GET.get('origin', '')
    destination_query = request.GET.get('destination', '')
    routes = Route.objects.all()
    if origin_query:
        routes = routes.filter(Q(origin__icontains=origin_query))
    if destination_query:
        routes = routes.filter(Q(destination__icontains=destination_query))
    routes = routes.order_by('-updated_date')
    context = {
        'routes': routes,
        'origin_query': origin_query,
        'destination_query': destination_query,
    }
    return render(request, 'admin/route_home.html', context)

def add_route(request):
    if request.method == 'POST':
        route_form = RouteForm(request.POST)
        if route_form.is_valid():
            route_form.save()
            return redirect('route_home')
    else:
        route_form = RouteForm()
    return render(request, 'admin/route_add_form.html', {'form': route_form})

def update_route(request, route_id):
    route_info = Route.objects.get(pk=route_id)
    if request.method == 'POST':
        route_form = RouteForm(request.POST, instance=route_info)
        if route_form.is_valid():
            route_form.save()
            return redirect('route_home')
    else:
        route_form = RouteForm(instance=route_info)
    return render(request, 'admin/route_update.html', {'route_form': route_form})

def delete_route(request, route_id):
    route_info = Route.objects.get(id=route_id)
    route_info.del_flag = 1 if route_info.del_flag == 0 else 0
    route_info.save()
    return redirect('route_home')

# Admin Bus Section
def bus_home(request):
    license_query = request.GET.get('license_no', '')
    operator_query = request.GET.get('operator', '')
    buses = Bus.objects.all()
    if license_query:
        buses = buses.filter(Q(license_no__icontains=license_query))
    if operator_query:
        buses = buses.filter(Q(operator__id=operator_query))
    buses = buses.order_by('-updated_date')
    operators = Operator.objects.all()
    context = {
        'buses': buses,
        'operators': operators,
        'license_query': license_query,
        'operator_query': operator_query,
    }
    return render(request, 'admin/bus_home.html', context)

def add_bus(request):
    if request.method == 'POST':
        bus_form = BusForm(request.POST)
        if bus_form.is_valid():
            bus_form.save()
            return redirect('bus_home')
    else:
        bus_form = BusForm()
    return render(request, 'admin/bus_add_form.html', {'form': bus_form})

def update_bus(request, bus_id):
    bus_info = Bus.objects.get(pk=bus_id)
    if request.method == 'POST':
        bus_form = BusForm(request.POST, instance=bus_info)
        if bus_form.is_valid():
            bus_form.save()
            return redirect('bus_home')
    else:
        bus_form = BusForm(instance=bus_info)
    return render(request, 'admin/bus_update.html', {'bus_form': bus_form})

def delete_bus(request, bus_id):
    bus_info = Bus.objects.get(id=bus_id)
    bus_info.del_flag = 1 if bus_info.del_flag == 0 else 0
    bus_info.save()
    return redirect('bus_home')

# Admin Schedule Section
def schedule_home(request):
    date_query = request.GET.get('date', '')
    route_query = request.GET.get('route', '')
    schedules = Schedule.objects.all()
    if date_query:
        schedules = schedules.filter(date__icontains=date_query)
    if route_query:
        schedules = schedules.filter(
            Q(route__origin__icontains=route_query) | Q(route__destination__icontains=route_query)
        )
    schedules = schedules.annotate(
        available_seats_count=Count('seat_status', filter=Q(seat_status__seat_status='Available'))
    )
    schedules = schedules.order_by('-updated_date')
    buses = Bus.objects.all()
    routes = Route.objects.all()
    context = {
        'schedules': schedules,
        'buses': buses,
        'routes': routes,
        'date_query': date_query,
        'route_query': route_query,
    }
    return render(request, 'admin/schedule_home.html', context)

def add_schedule(request):
    if request.method == 'POST':
        schedule_form = ScheduleForm(request.POST)
        if schedule_form.is_valid():
            print("Form is valid! Saving schedule...")
            new_schedule = schedule_form.save()
            bus = new_schedule.bus
            seat_capacity = bus.seat_capacity
            for seat_no in range(1, seat_capacity + 1):
                Seat_Status.objects.create(
                    schedule=new_schedule,
                    seat_no=f"{seat_no:02d}"
                )
            return redirect('schedule_home')
        else:
            print("Form is NOT valid! Errors:", schedule_form.errors)
    else:
        schedule_form = ScheduleForm()
    return render(request, 'admin/schedule_add_form.html', {'form': schedule_form})

def update_schedule(request, schedule_id):
    schedule_info = Schedule.objects.get(id=schedule_id)
    if request.method == 'POST':
        schedule_form = ScheduleForm(request.POST, instance=schedule_info)
        if schedule_form.is_valid():
            schedule_form.save()
            return redirect('schedule_home')
    else:
        schedule_form = ScheduleForm(instance=schedule_info)
    return render(request, 'admin/schedule_update.html', {'form': schedule_form})

def delete_schedule(request, schedule_id):
    schedule_info = Schedule.objects.get(id=schedule_id)
    schedule_info.del_flag = 1 if schedule_info.del_flag == 0 else 0
    schedule_info.save()
    return redirect('schedule_home')