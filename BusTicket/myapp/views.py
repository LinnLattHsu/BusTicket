import json
import re
from django.db.models import Max
from django.shortcuts import render
from django.db.models import Q, Count
from datetime import datetime, date
from django.contrib import messages
from django.shortcuts import render
from decimal import Decimal
from django.db import IntegrityError, transaction
from django.contrib.auth import login
from django.template.context_processors import request
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from .models import User, Operator, Bus, Route, Schedule,Booking,Ticket,Payment,Feedback, QuestionAndAnswer,Seat_Status,Admin
from django.urls import reverse
from .forms import UserLoginForm, UserRegisterForm, CustomUserCreationForm,BookingForm,OperatorForm,RouteForm,BusForm,qaForm,ScheduleForm,CustomUserChangeForm,ContactForm
from django.contrib.auth.decorators import login_required, user_passes_test
from decimal import Decimal
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
import qrcode
from django.shortcuts import render, get_object_or_404
from io import BytesIO
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.shortcuts import render
from datetime import datetime
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.admin.views.decorators import staff_member_required
from .forms import CustomUserAuthenticationForm,FeedbackForm
from django.contrib.auth import logout as auth_logout
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator # This was the previous fix
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode # This is the new fix
from django.utils.encoding import force_bytes # This is also needed
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.db.models import Q, Count, Case, When, Value, F
from datetime import datetime, timedelta
from django.core.mail import EmailMessage
import smtplib
import os
import requests


# Your views go here
# Create your views here.


# In home page, when you enter origin,destination and date this function will search for available routes

def home_page_feedback_qa(request):
    origins = Route.objects.values_list('origin', flat=True).distinct().order_by('origin')
    destinations = Route.objects.values_list('destination', flat=True).distinct().order_by('destination')
    # Step 1: Find the latest 'created_date' for each customer
    latest_dates = Feedback.objects.values('customer').annotate(latest_date=Max('created_date'))

    # Step 2: Query for the Feedback objects that match those latest dates and customers
    # This is done by filtering the original Feedback queryset
    latest_feedbacks = Feedback.objects.filter(
        created_date__in=[item['latest_date'] for item in latest_dates],
        customer__in=[item['customer'] for item in latest_dates]
    ).order_by('-created_date')[:3]
    # feedbacks = Feedback.objects.filter(del_flag=0).distinct().order_by('-created_date')[:3]
    qas = QuestionAndAnswer.objects.filter(del_flag=0).order_by('-created_date')[:3]
    context = {
        'origins':origins,
        'destinations':destinations,
        'active_page' : 'home',
        'feedbacks': latest_feedbacks,
        'qas':qas,
    }
    return render(request, 'base.html', context)

def search_routes(request):
    origins = Route.objects.values_list('origin', flat=True).distinct().order_by('origin')
    destinations = Route.objects.values_list('destination', flat=True).distinct().order_by('destination')
    operators = Operator.objects.filter(del_flag=0).order_by("operator_name")

    context = {
        'origins': origins,
        'destinations': destinations,
        'operators': operators,
        'selected_origin': None,
        'selected_destination': None,
        'selected_date': None,
        'number_of_seats': None,
        'selected_bus_type': None,
        'selected_operator': None,
        'error': None,
    }
    data = request.GET if request.method == 'GET' and request.GET else request.POST

    if data:
        origin_r = data.get('origin', '').strip()
        dest_r = data.get('destination', '').strip()
        date_r = data.get('date')
        number_of_seats = data.get('number_of_seats')
        bus_type = data.get('bus_type')
        operator_name = data.get('operator_name')  # ✅ fixed

        if not dest_r and data.get('to'):
            dest_r = data.get('to').strip()

        context.update({
            'data': data,
            'selected_origin': origin_r,
            'selected_destination': dest_r,
            'selected_date': date_r,
            'number_of_seats': number_of_seats,
            'selected_bus_type': bus_type,
            'selected_operator': operator_name,
        })

        if not (origin_r and dest_r and date_r):
            context.update({'error': 'Please enter origin, destination and date.'})
            return render(request, 'base.html', context)

        try:
            date_obj = datetime.strptime(date_r, "%Y-%m-%d").date()
        except ValueError:
            context.update({'error': 'Invalid date format.'})
            return render(request, 'base.html', context)
        now = datetime.now()
        schedules = Schedule.objects.filter(
            route__origin__iexact=origin_r,
            route__destination__iexact=dest_r,
            # date=date_obj,
            del_flag=0,
            route__del_flag=0,
            bus__del_flag=0
        )

        if date_obj < now.date():
            # If the selected date is in the past, no schedules should be returned
            schedules = schedules.none()
        elif date_obj == now.date():
            # If the selected date is today, filter for schedules with times greater than or equal to now's time
            schedules = schedules.filter(Q(date=date_obj, time__gte=now.time()))
        else:
            # If the selected date is in the future, just filter by the selected date
            schedules = schedules.filter(date=date_obj)
        # Apply bus type filter
        if bus_type:
            schedules = schedules.filter(bus__bus_type__iexact=bus_type)

        # Apply operator filter
        if operator_name:
            schedules = schedules.filter(bus__operator__operator_name__iexact=operator_name)

        schedules = schedules.order_by('time')
        # --- PLACE THE NEW QUERY HERE ---
        # Get the operators from the final, filtered list of schedules
        operators_with_schedules = Operator.objects.filter(
            id__in=schedules.values_list('bus__operator__id', flat=True)
        ).distinct().order_by("operator_name")
        if schedules.exists():
            return render(request, 'available_routes.html', {
                'schedules': schedules,
                'origins': origins,
                'destinations': destinations,
                # 'operators': operators,  # ✅ added
                'operators': operators_with_schedules,
                'selected_origin': origin_r,
                'selected_destination': dest_r,
                'selected_date': date_r,
                'selected_seat': number_of_seats,
                'selected_bus_type': bus_type,
                'selected_operator': operator_name,
            })
        else:
            context.update({'error': 'No available Bus Schedule for entered Route and Date'})
            return render(request, 'available_routes.html', context)

    return render(request, 'base.html', context)

def seat_selection(request,schedule_id):
    # print("DEBUG request.GET:", request.GET)
    # print("DEBUG request.POST:", request.POST)
    selected_bus = Schedule.objects.get(id=schedule_id)
    seat_capacity =selected_bus.bus.seat_capacity
    booked_seat_statuses = Seat_Status.objects.filter(
        schedule=selected_bus
    ).exclude(seat_status='Available').values_list('seat_no', flat=True)
    booked_seat_list = list(booked_seat_statuses)
    seats_data = []
    for i in range(seat_capacity):
        row_letter = chr(ord('A') + i // 3)
        seat_number_in_row = (i % 3) + 1
        seat_name = f"{row_letter}{seat_number_in_row}"
        is_booked = seat_name in booked_seat_list

        seats_data.append({
            'seat_name': seat_name,
            'is_booked': is_booked,
            'seat_index_in_row': i % 3
            # This helps with the 2-aisle-1 layout in the template (0, 1 for left; 2 for right)
        })
    # --- END NEW ---
    # source = request.GET.get('from')
    # dest = request.GET.get('to')
    # date = request.GET.get('departure_date')
    seats = request.GET.get('number_of_seats')
    # print("DEBUG seats (raw):", seats)
    seats = int(seats)
    total_price=Decimal(seats)*selected_bus.price
    print(total_price)
    context={
        'selected_bus':selected_bus,
        'origin':selected_bus.route.origin,
        'destination':selected_bus.route.destination,
        'date':selected_bus.date,
        'seats':seats,
        'total_price':total_price,
        'schedule_id':selected_bus.id,
        'seat_capacity':seat_capacity,
        'seats_data':seats_data,
    }
    return render(request, 'seat_selection.html',context)


#submit seat by lls
def submit_seats(request, schedule_id):
    if request.method == 'POST':
        request.session['seat_selection_data'] = {
            'schedule_id': schedule_id,
            'selected_seats': request.POST.get('selected_seats', ''),
        }

        if not request.user.is_authenticated:
            # Redirect to login page, which will redirect back to this view after login
            return redirect(f"{reverse('login')}?next={reverse('submit_seats', kwargs={'schedule_id': schedule_id})}")

    # If the user is authenticated, check for data in the session
    if request.user.is_authenticated:
        seat_data = request.session.get('seat_selection_data')
        if seat_data and seat_data['schedule_id'] == schedule_id:
            selected_seats_str = seat_data['selected_seats']
            # Clear the session data after use
            del request.session['seat_selection_data']
        else:
            # Handle cases where session data is missing or doesn't match
            selected_seats_str = request.POST.get('selected_seats')

        if not selected_seats_str:
            return render(request, 'error_page.html', {'message': 'No seats selected.'})

        selected_seats_list = selected_seats_str.split(',')
        number_of_seats = len(selected_seats_list)

        selected_bus = get_object_or_404(Schedule, id=schedule_id)
        total_price = Decimal(number_of_seats) * selected_bus.price

        context = {
            'schedule_id': schedule_id,
            'selected_bus': selected_bus,
            'bus_name': selected_bus.bus.license_no,
            'departure_date': selected_bus.date,
            'departure_time': selected_bus.time,
            'origin': selected_bus.route.origin,
            'destination': selected_bus.route.destination,
            'selected_seats': selected_seats_str,
            'number_of_seats': number_of_seats,
            'total_price': total_price,
            'user_id': request.user.user_id,
            'user_name': request.user.name,
        }

        # For debugging purposes
        print("--- Start Debugging ---")
        for key, value in context.items():
            print(f"Key: {key}, Value: {value}")
        print("--- End Debugging ---")

        return render(request, 'payment.html', context)

    # If the request is a GET and the user is not authenticated,
    # or there's no session data, redirect to home.
    return redirect('home')


# process payment by sdwp
@login_required
def process_payment(request, user_id):
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('home')

    schedule_id = request.POST.get('schedule_id')
    selected_seats_str = request.POST.get('selected_seats', '')
    total_price_str = request.POST.get('total_price')
    payment_method_value = request.POST.get('payment_method')
    # selected_seats_list = selected_seats_str.split(',')

    # Add this print statement to see what you are receiving from the form
    print("Received selected_seats_str:", selected_seats_str)

    # Use a more robust way to split and clean the list
    # .strip() removes any leading/trailing whitespace from each seat number
    selected_seats_list = [seat.strip() for seat in selected_seats_str.split(',') if seat.strip()]

    # Check if the list of selected seats is empty after cleaning
    if not selected_seats_list:
        messages.error(request, "Please select at least one seat.")
        return redirect('select_seats', schedule_id=schedule_id)

    print(schedule_id)
    print(selected_seats_str)
    print(total_price_str)
    print(payment_method_value)

    # for seat_no in selected_seats_str:
    #     print(seat_no)


    if not all([schedule_id, selected_seats_str, total_price_str, payment_method_value]):
        messages.error(request, "Missing payment details. Please go back and try again.")
        # You should redirect to the page where the user can re-enter details
        return redirect('home')

    try:
        try:
            total_price_decimal = Decimal(total_price_str)
        except (ValueError, InvalidOperation):
            messages.error(request, "Invalid total price. Please try again.")
            return redirect('submit_seats', schedule_id=schedule_id)

        with transaction.atomic():
            selected_bus_schedule = get_object_or_404(Schedule.objects.select_for_update(), id=schedule_id)

            # The code from here on is the same as your original code
            booking = Booking.objects.create(
                schedule=selected_bus_schedule,
                customer=request.user,
                seat_numbers=selected_seats_str,
            )
            # date_part = booking.booked_time.strftime('%Y%m%d')
            # time_part = booking.booked_time.strftime('%H%M')
            # print(date_part)
            # print(time_part)
            # #
            # # # Combine the formatted date, time, and original ID
            # formatted_booking_id = f'B{date_part}{time_part}{booking.id}'
            # print(formatted_booking_id)

            for seat_no in selected_seats_list:
                seat_status_obj = get_object_or_404(
                    Seat_Status.objects.select_for_update(),
                    schedule=selected_bus_schedule,
                    seat_no=seat_no,
                    seat_status='Available'
                )
                seat_status_obj.seat_status = 'Unavailable'
                seat_status_obj.booking = booking
                seat_status_obj.save()

            ticket = Ticket.objects.create(
                booking=booking,
                total_seat=len(selected_seats_list),
                total_amount=Decimal(total_price_str),
            )

            payment_method_code = 'KP' if payment_method_value == 'kpay' else 'WM'
            Payment.objects.create(
                ticket=ticket,
                payment_method=payment_method_code,
            )


            # Success! Redirect to the booking confirmation page.
            # return redirect('booking_confirmation', booking_id=booking.id,custom_booking_id = formatted_booking_id)
            return redirect('booking_confirmation',booking_id=booking.id)
    except (Schedule.DoesNotExist, Seat_Status.DoesNotExist) as e:
        # A specific seat or schedule was not found, meaning it's already taken or invalid.
        messages.error(request, "One or more selected seats are no longer available. Please re-select your seats.")
        return redirect('select_seats', schedule_id=schedule_id)  # Redirect the user back to seat selection.

    except Exception as e:
        # Catch any other unexpected, critical errors.

        messages.error(request, "An unexpected error occurred during booking. Please try again.")
        # Print the error for your own debugging
        import traceback
        print("Unhandled exception in process_payment:", e)
        traceback.print_exc()
        return redirect('submit_seats',schedule_id=schedule_id)



@login_required
def booking_confirmation(request, booking_id):
    try:
        booking = get_object_or_404(Booking, id=booking_id, customer=request.user)
        ticket = Ticket.objects.get(booking=booking)
        schedule = booking.schedule
        bus = schedule.bus
        route = schedule.route
        booked_seats_status = Seat_Status.objects.filter(booking=booking)

        date_part = booking.booked_time.strftime('%Y%m%d')
        time_part = booking.booked_time.strftime('%H%M')
        formatted_booking_id = f'B{date_part}{time_part}{booking.id}'

        context = {
            'booking': booking,
            'ticket': ticket,
            'schedule': schedule,
            'bus': bus,
            'route': route,
            'booked_seats_status': booked_seats_status,
            'user': request.user,
            'custom_booking_id': formatted_booking_id,
        }

        return render(request, 'booking_confirmation.html', context)

    except Booking.DoesNotExist:
        return render(request, 'error.html', {'message': 'Booking not found.'})
    except Ticket.DoesNotExist:
        return render(request, 'error.html', {'message': 'Ticket information missing.'})



def home(request):
    bookings = Bus.objects.all()
    return render(request,'base.html',{'bookings':bookings})

@login_required # Add this decorator to protect the view
def profile_page(request):
    # Pass the authenticated user object to the template context
    # return render(request, 'profile_page.html', {'user': request.user})
    user = request.user

    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            user.refresh_from_db()
            messages.success(request, 'Your profile has been updated successfully!')
            # --- IMPORTANT CHANGE HERE: Re-render the page instead of redirecting ---
            return redirect('/')
        else:
            print("\n--- FORM ERRORS ---")  # Keep this for debugging if issues persist
            print(form.errors)
            print("--- END FORM ERRORS ---\n")
            messages.error(request, 'There was an error updating your profile. Please correct the errors below.')
            return render(request, 'profile_page.html', {'form': form})
            # messages.error(request, 'There was an error updating your profile. Please correct the errors below.')
    else:
        form = CustomUserChangeForm(instance=user)

    return render(request, 'profile_page.html', {'form': form})

# custom user register form by sdwp

@login_required
def seebookings(request, booking_id=None):
    if booking_id:
        try:
            booking = Booking.objects.get(id=booking_id,customer=request.user)
        except Booking.DoesNotExist:
            messages.error(request, "Ticket not found or you don't have permission to view it.")
            return redirect('seebookings')
        date_part = booking.booked_time.strftime('%Y%m%d')
        time_part = booking.booked_time.strftime('%H%M')
        print(date_part)
        print(time_part)

        # Combine the formatted date, time, and original ID
        formatted_booking_id = f'B{date_part}{time_part}{booking.id}'
        print(formatted_booking_id)
        context = {
            'active_page': 'seebookings',
            'booking': booking,
            'custom_booking_id': formatted_booking_id # Pass the single booking object for detailed view
        }
        return render(request, 'see_bookings.html', context)

    else:
        search_id_str = request.GET.get('booking_id')
        search_date_str = request.GET.get('travel_date')
        # convert string id to booking_id
        user_bookings = Booking.objects.filter(customer=request.user)

        if search_id_str:
            match = re.search(r'B\d{12}(\d+)$', search_id_str)
            print(match)
            if match:
                try:
                    numeric_id = int(match.group(1))
                    print(numeric_id)
                    user_bookings = user_bookings.filter(id=numeric_id)
                except (ValueError, TypeError):
                    user_bookings = Booking.objects.none()
            else:
                user_bookings = Booking.objects.none()
                messages.warning(request, "Please enter a valid booking ID format.")
        elif search_date_str:
            try:
                date_obj = datetime.strptime(search_date_str, "%Y-%m-%d").date()
                user_bookings = user_bookings.filter(schedule__date=date_obj)
            except ValueError:
                user_bookings = user_bookings.none()
                messages.error(request, "Invalid date format.")

        user_bookings = user_bookings.order_by('-schedule__date')
        # today=date.today()
        # processed_bookings = []
        for booking in user_bookings:
            # booking.is_past_booking = booking.schedule.date < today

            date_part = booking.booked_time.strftime('%Y%m%d')
            time_part = booking.booked_time.strftime('%H%M')
            # Attach the formatted ID directly to each booking object
            booking.custom_booking_id = f'B{date_part}{time_part}{booking.id}'
            # processed_bookings.append(booking)


        context = {
            'bookings': user_bookings,  # This now contains the custom ID
            # 'bookings': processed_bookings,
            'today': date.today(),
            'active_page': 'seebookings',
            'search_id': search_id_str,
            'search_date': search_date_str
        }

        return render(request, 'see_bookings.html', context)

# @login_required
def feedback(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)

        if form.is_valid():
            feedback_instance = form.save(commit=False)  # Create but don't save yet
            feedback_instance.customer = request.user  # Assign the logged-in user


            feedback_instance.save()  # Now save the instance to the database
            print(request.user.email)
            messages.success(request, "Thank you for your feedback! We appreciate it.")
            return redirect('feedback_success')  # Redirect to a success page
        else:
            messages.error(request, "There was an error submitting your feedback. Please correct the issues below.")
            print('processs fail')
            # If form is not valid, it will be rendered again with errors in the template
    else:
        form = FeedbackForm()  # Create a fresh, empty form for GET requests
        # print('processs fail')

    context = {
        'active_page': 'feedback',
        'form': form,
    }
    return render(request, 'feedback_form.html', context)

@login_required
def feedback_success(request):
    return render(request, 'feedback_success.html')


def about_us(request):
    is_authenticated = request.user.is_authenticated
    context = {
        'active_page': 'about_us',
        'is_authenticated': is_authenticated
    }
    if is_authenticated:
        context['user'] = request.user

    return render(request, 'about_us.html', context)

def user_registration(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()
            # FIX: Explicitly specify the custom authentication backend for login
            login(request, user, backend='myapp.backends.MyCustomAuthBackend')
            messages.success(request, 'Account created successfully!')
            return redirect('login')
        else:
            messages.error(request, 'There was an error creating your account. Please check the form.')
    else:
        form = CustomUserCreationForm()
    return render(request, 'user_registration_form.html', {'form': form})


# def user_login(request):
#     if request.method == 'POST':
#         form = CustomUserAuthenticationForm(request=request, data=request.POST)
#
#         if form.is_valid():
#             user = form.get_user()
#
#             if user is not None:
#                 # Log the user in
#                 login(request, user)
#                 messages.success(request, 'You have been logged in successfully!')
#
#                 # Check for the 'next' parameter in the request's GET data
#                 # If a 'next' URL is present, redirect to it.
#                 next_url = request.GET.get('next')
#                 if next_url:
#                     return redirect(next_url)
#
#                 # If no 'next' parameter, use the default redirection logic
#                 if isinstance(user, Admin):
#                     return redirect('admin_dashboard')
#                 else:
#                     return redirect('logined_user')
#             else:
#                 messages.error(request, 'Invalid email or password. Please try again.')
#     else:
#         form = CustomUserAuthenticationForm(request=request)
#
#     return render(request, 'login.html', {'form': form,'active_page':login})
#
# @login_required
# def logined_user_home(request):
#     user_id = request.user.user_id
#     context = {
#         'active_page': login,
#         'user_id': user_id,
#         'user_email': request.user.email,
#     }
#     return render(request, 'register_user/login_user_home.html', context)

def is_admin(user):
    """
    A simple test to check if the user is an admin.
    You can use user.is_staff or check for a specific group.
    """
    return user.is_staff

def user_login(request):

    if request.method == 'POST':
        form = CustomUserAuthenticationForm(request=request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user is not None:
                login(request, user)
                messages.success(request, 'You have been logged in successfully!')

                next_page = request.session.pop('next_page', None)
                if next_page:
                    return redirect(next_page)

                # Redirect based on user type after successful login
                if user.is_staff:
                    return redirect('admin_dashboard')
                else:
                    return redirect('logined_user')
            else:
                messages.error(request, 'Invalid email or password. Please try again.')
    else:
        form = CustomUserAuthenticationForm(request=request)
        # Store the 'next' parameter if it's in the GET request, common for login redirects
        next_page = request.GET.get('next')
        if next_page:
            request.session['next_page'] = next_page

    # return render(request, 'login.html', {'form': form, 'active_page': 'login'})

    return render(request, 'login.html', {'form': form, 'active_page': 'login'})

# Admin Dashboard View with access control
@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):

    return render(request, 'dashboard.html')

# Logged-in User Dashboard View
@login_required
def logined_user(request):
    """
    This view is for the regular user dashboard.
    Only logged-in users can access this page.
    """
    return render(request, 'base.html')


def logout_view(request):
    auth_logout(request)  # <-- use Django’s logout, not your view
    storage = messages.get_messages(request)
    list(storage)
    messages.info(request, "You have been logged out")
    return redirect('login')


def forgot_password_view(request):
    """ Renders the forgot password page """
    return render(request, 'forgot_psw.html')

def send_password_reset_email(request):
    """
    Handles the password reset request.
    It takes an email, finds the user, generates a token, and sends an email.
    """
    if request.method == 'POST':
        try:
            # Parse the JSON data sent from the frontend
            data = json.loads(request.body)
            email = data.get('email')
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid request format.'}, status=400)

        # Do not reveal if the email is registered for security reasons
        # We will send a success message regardless of whether the email exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return JsonResponse({'message': 'If an account exists with this email, a reset link has been sent.'},
                                status=200)

        # Generate a unique token for the password reset link
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        # Build the password reset URL
        current_site = get_current_site(request)
        reset_link = reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
        reset_url = f"http://{current_site.domain}{reset_link}"

        # Prepare the email content using a template
        email_subject = 'Password Reset Request'
        email_message = render_to_string('password_reset_email.html', {
            'user': user,
            'reset_url': reset_url,
        })

        # Send the email
        send_mail(
            email_subject,
            None,  # The plain text version can be empty
            'noreply@yourdomain.com',
            [user.email],
            fail_silently=False,
            html_message=email_message,  # This sends it as HTML
        )

        return JsonResponse({'message': 'A password reset link has been sent to your email address.'}, status=200)

    return JsonResponse({'error': 'Invalid request method.'}, status=405)




def contact_us(request):
    """
    Handles the contact form submission with ZeroBounce API validation.
    """
    if request.method == 'POST':
        form = ContactForm(request.POST)

        # Get the user's email
        user_email = request.user.email

        # If the user is logged in, you can add a field to the form data
        # so the form can validate it.
        if request.user.is_authenticated:
            form.data = form.data.copy()
            form.data['user_email'] = user_email

        if form.is_valid():
            # --- REAL-TIME EMAIL VALIDATION WITH ZEROBOUNCE API ---
            # Get the API key from your settings
            api_key = os.getenv("ZEROBOUNCE_API_KEY")

            # The API endpoint for real-time validation
            api_url = f'https://api.zerobounce.net/v2/validate?api_key={api_key}&email={user_email}'

            try:
                # Make the API call
                response = requests.get(api_url)
                response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)

                result = response.json()

                # Check the validation status from the API response
                if result.get('status') != 'valid':
                    # The email is not valid according to ZeroBounce
                    messages.error(request,
                                   f'The email address "{user_email}" is not a real or valid account.')
                    return render(request, 'contact_us.html', {'form': form, 'active_page': 'contact'})

            except requests.exceptions.RequestException as e:
                # Handle API connection errors
                messages.error(request,
                               f'Could not connect to the email validation service. Please try again later. ')
                return render(request, 'contact_us.html', {'form': form, 'active_page': 'contact'})
            # --- END OF ZEROBOUNCE VALIDATION ---

            # If validation passes, proceed with sending the email
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']

            try:
                # Create and send the email
                email = EmailMessage(
                    subject=f"Contact from {user_email}: {subject}",
                    body=f"From: {user_email}\n\n{message}",
                    from_email=settings.EMAIL_HOST_USER,
                    to=[settings.EMAIL_HOST_USER],
                    headers={'Reply-To': user_email},
                )
                email.send(fail_silently=False)

                messages.success(request,
                                 'Your message has been sent successfully! Our team will get back to you shortly. 📧')
                return redirect('contact_us')

            # You can keep your existing email sending error handling here
            except smtplib.SMTPException as e:
                messages.error(request, f'An error occurred with the email server. Error: {e} 🚨')
            except Exception as e:
                messages.error(request, f'An unexpected error occurred. Error: {e} 🐛')

    else:
        # For a GET request, display a new, empty form
        form = ContactForm()

    context = {
        'form': form,
        'active_page': 'contact'
    }
    return render(request, 'contact_us.html', context)


# Admin Dashboard
@staff_member_required
@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    no_of_users = User.objects.filter(del_flag = 0).count()
    no_of_buses = Bus.objects.filter(del_flag = 0).count()
    no_of_routes = Route.objects.filter(del_flag=0).count()
    no_of_operators = Operator.objects.filter(del_flag=0).count()
    no_of_schedules = Schedule.objects.filter(del_flag=0).count()
    no_of_bookings = Booking.objects.all().count()
    no_of_tickets = Ticket.objects.all().count()

    bus_query = request.GET.get('bus_number', '')
    origin_query = request.GET.get('origin', '')
    destination_query = request.GET.get('destination', '')
    selected_schedule = None
    seat_status_list = []

    if bus_query and origin_query and destination_query:
        try:
            selected_schedule = Schedule.objects.get(
                Q(bus__license_no__iexact=bus_query) &
                (Q(route__origin__iexact=origin_query) & Q(route__destination__iexact=destination_query)) &
                Q(del_flag=0)
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
        'origin_query': origin_query,
        'destination_query': destination_query,
        'selected_schedule': selected_schedule,
        'seat_status_list': seat_status_list
    })

@login_required
@user_passes_test(is_admin)
def user_home(request):

    # Start with the base queryset for all users
    users = User.objects.all()

    # Get the filter parameters from the request
    name_query = request.GET.get('name')
    status_query = request.GET.get('status', 'active')

    if name_query:
        # Use Q objects for more complex or combined queries if needed,
        # or simply filter by a single field.
        # This will filter based on both first_name and last_name or just name field
        users = users.filter(name__icontains=name_query)

    if status_query:
        if status_query == 'active':
            # Assuming del_flag = 0 means the user is active
            users = users.filter(del_flag=0)
        elif status_query == 'deleted':
            # Assuming any value other than 0 for del_flag means deleted
            users = users.filter(del_flag__gt=0)

    # Sort the users for a consistent display
    users = users.order_by('user_id')

    # Prepare the context to pass to the template
    users = {
        'users': users
    }

    # Render the user_home.html template with the filtered user list
    return render(request, 'admin/user_home.html', users)

@login_required
@user_passes_test(is_admin)
def soft_delete_user(request,user_id):
    user_info = User.objects.get(user_id=user_id)
    if user_info.del_flag == 0:
        user_info.del_flag = 1
        user_info.save()
    else:
        user_info.del_flag = 0
        user_info.save()

    return redirect('user_home')


# operator home page in admin
@login_required
@user_passes_test(is_admin)
def operator_home(request):
    search_query = request.GET.get('search', '')
    status_query = request.GET.get('status', 'active')

    operators = Operator.objects.all()
    if search_query:
        operators = operators.filter(Q(operator_name__icontains=search_query))

    if status_query:
        if status_query == 'active':
            # Assuming del_flag = 0 means the user is active
            operators = operators.filter(del_flag=0)
        elif status_query == 'Deleted':
            # Assuming any value other than 0 for del_flag means deleted
            operators = operators.filter(del_flag = 1)
    context = {
    'operators': operators,
    'search_query': search_query,
    }
    return render(request, 'admin/operator_home.html', context)



# route home page in admin
@login_required
@user_passes_test(is_admin)
def route_home(request):
    origin_query = request.GET.get('origin', '')
    destination_query = request.GET.get('destination', '')
    status_query = request.GET.get('status', 'active')

    routes = Route.objects.all()

    if origin_query:
        routes = routes.filter(Q(origin__icontains=origin_query))

    if destination_query:
        routes = routes.filter(Q(destination__icontains=destination_query))

    if status_query:
        if status_query == 'active':
            # Assuming del_flag = 0 means the user is active
            routes = routes.filter(del_flag=0)
        elif status_query == 'deleted':
            # Assuming any value other than 0 for del_flag means deleted
            routes = routes.filter(del_flag = 1)

    context = {
        'routes': routes,
        'origin_query': origin_query,
        'destination_query': destination_query,
    }
    return render(request, 'admin/route_home.html', context)

@login_required
@user_passes_test(is_admin)
def add_operator(request):
    if request.method == 'POST':
        operator_form = OperatorForm(request.POST)
        if operator_form.is_valid():
            operator_form.save()
            return HttpResponseRedirect('/admindashboard/operator_home/')
    else:
        operator_form = OperatorForm()
    return render(request, 'admin/operator_add_form.html', {'form': operator_form})

@login_required
@user_passes_test(is_admin)
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

@login_required
@user_passes_test(is_admin)
def delete_operator(request, operator_id):
    operator_info = Operator.objects.get(id=operator_id)
    operator_info.del_flag = 1 if operator_info.del_flag == 0 else 0
    operator_info.save()
    return redirect('operator_home')

# route home page in admin
from django.shortcuts import render
from django.db.models import Q
from .models import Route  # Assuming your model is named Route

@login_required
@user_passes_test(is_admin)
def route_home(request):
    origin_query = request.GET.get('origin', '')
    destination_query = request.GET.get('destination', '')
    status_query = request.GET.get('status', 'active')

    routes = Route.objects.all()

    if origin_query:
        routes = routes.filter(Q(origin__icontains=origin_query))

    if destination_query:
        routes = routes.filter(Q(destination__icontains=destination_query))

    if status_query:
        if status_query == 'Active':
            # Assuming del_flag = 0 means the user is active
            routes = routes.filter(del_flag=0)
        elif status_query == 'Deleted':
            # Assuming any value other than 0 for del_flag means deleted
            routes = routes.filter(del_flag = 1)

    routes = routes.order_by('-updated_date')

    context = {
        'routes': routes,
        'origin_query': origin_query,
        'destination_query': destination_query,
    }
    return render(request, 'admin/route_home.html', context)

@login_required
@user_passes_test(is_admin)
def add_route(request):
    if request.method == 'POST':
        route_form = RouteForm(request.POST)
        if route_form.is_valid():
            route_form.save()
            return redirect('route_home')
    else:
        route_form = RouteForm()
    return render(request, 'admin/route_add_form.html', {'form': route_form})

@login_required
@user_passes_test(is_admin)
def update_route(request,route_id):
    route_info = Route.objects.get(pk = route_id)

    if request.method == 'POST':
        route_form = RouteForm(request.POST, instance=route_info)
        if route_form.is_valid():
            route_form.save()
            return redirect('route_home')
    else:
        route_form = RouteForm(instance=route_info)

    return render(request,'admin/route_update.html',{'route_form' : route_form})

@login_required
@user_passes_test(is_admin)
def delete_route(request,route_id):
    route_info = Route.objects.get(id=route_id)
    if route_info.del_flag == 0:
        route_info.del_flag = 1
        route_info.save()
    else:
        route_info.del_flag = 0
        route_info.save()

    return redirect('route_home')

# Admin Bus Section
@login_required
@user_passes_test(is_admin)
def bus_home(request):
    license_query = request.GET.get('license_no', '')
    operator_query = request.GET.get('operator', '')
    status_query = request.GET.get('status', 'active')

    buses = Bus.objects.all()

    if license_query:
        buses = buses.filter(Q(license_no__icontains=license_query))

    if operator_query:
        buses = buses.filter(Q(operator__operator_name__icontains=operator_query))

    if status_query:
        if status_query == 'active':
            # Assuming del_flag = 0 means the user is active
            buses = buses.filter(del_flag=0)
        elif status_query == 'deleted':
            # Assuming any value other than 0 for del_flag means deleted
            buses = buses.filter(del_flag = 1)

    buses = buses.order_by('-updated_date')
    operators = Operator.objects.all()

    context = {
        'buses': buses,
        'operators': operators,
        'license_query': license_query,
        'operator_query': operator_query,
    }

    return render(request, 'admin/bus_home.html', context)

@login_required
@user_passes_test(is_admin)
def add_bus(request):
    if request.method == 'POST':
        bus_form = BusForm(request.POST)
        if bus_form.is_valid():
            bus_form.save()
            return redirect('bus_home')
    else:
        bus_form = BusForm()
    return render(request,'admin/bus_add_form.html',{'form' : bus_form})


@login_required
@user_passes_test(is_admin)
def update_bus(request,bus_id):
    bus_info = Bus.objects.get(pk= bus_id)

    if request.method == 'POST':
        bus_form = BusForm(request.POST, instance=bus_info)
        if bus_form.is_valid():
            bus_form.save()
            return redirect('bus_home')
    else:
        bus_form = BusForm(instance=bus_info)

    return render(request,'admin/bus_update.html',{'bus_form':bus_form})

@login_required
@user_passes_test(is_admin)
def delete_bus(request,bus_id):
    bus_info = Bus.objects.get(id=bus_id)
    if bus_info.del_flag == 0:
        bus_info.del_flag = 1
        bus_info.save()
    else:
        bus_info.del_flag = 0
        bus_info.save()

    return redirect('bus_home')


# Admin Schedule Section
# def schedule_home(request):
#
#     date_query = request.GET.get('date', '')
#     route_query = request.GET.get('route', '')
#
#     schedules = Schedule.objects.all()
#
#     if date_query:
#         schedules = schedules.filter(date__icontains=date_query)
#
#     if route_query:
#         schedules = schedules.filter(
#             Q(route__origin__icontains=route_query) | Q(route__destination__icontains=route_query)
#         )
#
#     schedules = schedules.order_by('-updated_date')
#
#     buses = Bus.objects.all()
#     routes = Route.objects.all()
#
#     context = {
#         'schedules': schedules,
#         'buses': buses,
#         'routes': routes,
#         'date_query': date_query,
#         'route_query': route_query,
#     }
#
#     # Render the schedule_home template with the context
#     return render(request, 'admin/schedule_home.html', context)

@login_required
@user_passes_test(is_admin)
def schedule_home(request):
    date_query = request.GET.get('date', '')
    origin_query = request.GET.get('origin', '')
    destination_query = request.GET.get('destination', '')
    status_query = request.GET.get('status', 'Active')

    now = datetime.now()

    expired_schedules = Schedule.objects.filter(
        Q(date__lt=now.date()) | Q(date=now.date(), time__lt=now.time()),
        del_flag=0
    )

    buses_to_unassign = expired_schedules.values_list('bus', flat=True).distinct()

    Bus.objects.filter(id__in=buses_to_unassign).update(is_assigned=0)

    expired_schedules.update(del_flag=1)

    schedules = Schedule.objects.annotate(
        available_seats_count=Count('seat_status', filter=Q(seat_status__seat_status='Available'))
    )

    three_days_from_now = now.date() + timedelta(days=3)
    schedules = schedules.annotate(
        alert=Case(
            When(date__lte=three_days_from_now, then=Value(True)),
            default=Value(False)
        )
    )

    if date_query:
        schedules = schedules.filter(
            Q(date=date_query) &
            Q(del_flag=0)
        )

    if origin_query:
        schedules = schedules.filter(
            Q(route__origin__icontains=origin_query) &
            Q(del_flag=0)
        )
    if destination_query:
        schedules = schedules.filter(
            Q(route__destination__icontains=destination_query) &
            Q(del_flag=0)
        )
    if status_query:
        if status_query == 'Active':
            schedules = schedules.filter(del_flag=0)
        elif status_query == 'Inactive':
            schedules = schedules.filter(del_flag=1)

    schedules = schedules.order_by('date')

    buses = Bus.objects.all()
    routes = Route.objects.all()

    context = {
        'schedules': schedules,
        'buses': buses,
        'routes': routes,
        'date_query': date_query,
        'origin_query': origin_query,
        'destination_query': destination_query,
        'status_query': status_query,
    }

    # Render the schedule_home template with the context
    return render(request, 'admin/schedule_home.html', context)

# def add_schedule(request):
#     if request.method == 'POST':
#         schedule_form = ScheduleForm(request.POST)
#         if schedule_form.is_valid():
#             print("Form is valid! Saving schedule...")
#             new_schedule = schedule_form.save()
#             bus = new_schedule.bus
#             seat_capacity = bus.seat_capacity
#             for seat_no in range(1, seat_capacity + 1):
#                 Seat_Status.objects.create(
#                     schedule=new_schedule,
#                     seat_no=f"{seat_no:02d}"
#
#                 )
#             return redirect('schedule_home')
#         else:
#             # This is the key change to debug the issue
#             print("Form is NOT valid! Errors:", schedule_form.errors)
#     else:
#         schedule_form = ScheduleForm()
#     return render(request, 'admin/schedule_add_form.html', {'form': schedule_form})

@login_required
@user_passes_test(is_admin)
def add_schedule(request):

    if request.method == 'POST':
        schedule_form = ScheduleForm(request.POST)
        if schedule_form.is_valid():
            print("Form is valid! Saving schedule...")
            new_schedule = schedule_form.save()

            # Retrieve the bus object from the new schedule to get the seat capacity.
            bus = new_schedule.bus
            bus.is_assigned = 1
            bus.save()  # <--- This line is essential to save the change to the bus object.

            seat_capacity = bus.seat_capacity

            # Loop through the total number of seats to create a seat for each one.
            # Using i starting from 0, to simplify calculations.
            for i in range(seat_capacity):
                # Calculate the row letter based on a 3-seat-per-row layout.
                # Integer division `//` gives us the row index (0 for 'A', 1 for 'B', etc.).
                row_letter = chr(ord('A') + i // 3)

                # Calculate the seat number within the row using the modulo operator.
                # `i % 3` gives us 0, 1, or 2, so we add 1 to get seat numbers 1, 2, or 3.
                seat_number_in_row = (i % 3) + 1

                # Combine the letter and number to create the final seat name.
                seat_name = f"{row_letter}{seat_number_in_row}"
                # print(seat_name)

                # Create the Seat_Status object for the new schedule.
                # is_available is set to True by default for new seats.
                Seat_Status.objects.create(
                    schedule=new_schedule,
                    seat_no=seat_name
                )

            # Redirect to a success page after creating the schedule and seats.
            return redirect('schedule_home')
        else:
            # Print form errors for debugging if the form is not valid.
            print("Form is NOT valid! Errors:", schedule_form.errors)
    else:
        # For a GET request, create a blank form instance.
        schedule_form = ScheduleForm()

    # Render the form template.
    return render(request, 'admin/schedule_add_form.html', {'form': schedule_form})

@login_required
@user_passes_test(is_admin)
def update_schedule(request,schedule_id):
    schedule_info = Schedule.objects.get(id=schedule_id)

    if request.method == 'POST':
        schedule_form = ScheduleForm(request.POST, instance=schedule_info)
        if schedule_form.is_valid():
            schedule_form.save()
            return redirect('schedule_home')
    else:
        schedule_form = ScheduleForm(instance=schedule_info)

    return render(request,'admin/schedule_update.html',{'form':schedule_form})

@login_required
@user_passes_test(is_admin)
def delete_schedule(request,schedule_id):
    schedule_info = Schedule.objects.get(id=schedule_id)
    if schedule_info.del_flag == 0:
        schedule_info.del_flag = 1
        schedule_info.save()
    else:
        schedule_info.del_flag = 0
        schedule_info.save()

    return redirect('schedule_home')

# for booking admindashboard
@login_required
@user_passes_test(is_admin)
def booking_list(request):

    now = datetime.now()
    bookings = Booking.objects.select_related(
        'customer',
        'schedule__bus__operator',
        'schedule__route'
    ).filter(
        # Filter out schedules that have already passed
        Q(schedule__date__gt=now.date()) |
        (Q(schedule__date=now.date()) & Q(schedule__time__gte=now.time()))
    ).all()

    origin = request.GET.get('origin')
    destination = request.GET.get('destination')
    operator_name = request.GET.get('operator_name')
    license_no = request.GET.get('license')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    filter_query = Q()

    three_days_from_now = now.date() + timedelta(days=3)
    bookings = bookings.annotate(
        alert=Case(
            When(schedule__date__lte=three_days_from_now, then=Value(True)),
            default=Value(False)
        )
    )

    if origin:
        filter_query &= Q(schedule__route__origin__icontains=origin)

    if destination:
        filter_query &= Q(schedule__route__destination__icontains=destination)

    if operator_name:
        filter_query &= Q(schedule__bus__operator__operator_name__icontains=operator_name)

    if license_no:
        filter_query &= Q(schedule__bus__license_no__icontains=license_no)

    if from_date and to_date:
        filter_query &= Q(booked_time__date__range=[from_date, to_date])

    bookings = bookings.filter(filter_query)

    bookings = bookings.order_by('schedule__date')

    context = {
        'bookings': bookings,
        'request': request
    }
    print(now)
    for booking in bookings:
        print(booking.schedule.date)
    return render(request, 'admin/booking_list.html', context)

# def booking_create(request):
#     if request.method == "POST":
#         schedule_id = request.POST.get("schedule_id")
#         customer_id = request.POST.get("customer_id")
#         seat_number = request.POST.get("seat_number")
#
#         schedule = get_object_or_404(Schedule, id=schedule_id)
#         customer = get_object_or_404(User, id=customer_id)
#
#         Booking.objects.create(
#             schedule=schedule,
#             customer=customer,
#             seat_number=seat_number,
#             booked_time=timezone.now()
#         )
#         return redirect("booking_list")
#
#     schedules = Schedule.objects.all()
#     customers = User.objects.all()
#     return render(request, "admin/booking_form.html", {
#         "schedules": schedules,
#         "customers": customers
#     })

# for history admindashboard
# def history_view(request):
#     history_records = Booking.objects.all().order_by('-booked_time')
#     # change field as needed
#     return render(request, "admin/history.html", {"history_records": history_records})

@login_required
@user_passes_test(is_admin)
def history_list(request):

    bookings = Booking.objects.select_related(
        'customer',
        'schedule__bus__operator',
        'schedule__route'
    ).all()

    origin = request.GET.get('origin')
    destination = request.GET.get('destination')
    operator_name = request.GET.get('operator_name')
    license_no = request.GET.get('license')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    filter_query = Q()

    now = datetime.now()

    filter_query &= Q(schedule__date__lt=now.date()) | \
                    (Q(schedule__date=now.date()) & Q(schedule__time__lt=now.time()))

    if origin:
        filter_query &= Q(schedule__route__origin__icontains=origin)

    if destination:
        filter_query &= Q(schedule__route__destination__icontains=destination)

    if operator_name:
        filter_query &= Q(schedule__bus__operator__operator_name__icontains=operator_name)

    if license_no:
        filter_query &= Q(schedule__bus__license_no__icontains=license_no)

    if from_date and to_date:
        # Filter by the booked time date range, if provided
        filter_query &= Q(booked_time__date__range=[from_date, to_date])


    history_items = bookings.filter(filter_query)

    history_items = history_items.order_by('-booked_time')

    context = {
        'history': history_items,
        'request': request
    }

    return render(request, 'admin/history.html', context)

@login_required
@user_passes_test(is_admin)
def feedback_list(request):

    feedbacks = Feedback.objects.all().order_by('-created_date')

    search_query = request.GET.get('search')
    if search_query:
        feedbacks = feedbacks.filter(
            Q(customer__name__icontains=search_query) |
            Q(message__icontains=search_query)
        )

    context = {
        'feedbacks': feedbacks,
    }
    return render(request, 'admin/feedback_list.html', context)

@login_required
@user_passes_test(is_admin)
def feedback_detail(request, feedback_id):
    feedback = get_object_or_404(Feedback, id=feedback_id)
    if not feedback.is_read:
        feedback.is_read = 1
        feedback.save()
    if request.method == 'POST':
        response_message = request.POST.get('response_message')
        if response_message:
            feedback.response = response_message


            return redirect('feedback_detail', feedback_id=feedback.id)

    context = {
        'feedback': feedback,
    }
    return render(request, 'admin/feedback_details.html', context)

# q&a list page in admin
@login_required
@user_passes_test(is_admin)
def question_answer_list(request):
    qas = QuestionAndAnswer.objects.filter(del_flag=0).order_by('-created_date')

    search_query = request.GET.get('search')
    if search_query:
        qas = qas.filter(
            Q(question__icontains=search_query) |
            Q(answer__icontains=search_query)
        )

    qas = {
        'qas': qas,
    }
    return render(request, 'admin/question_answer_list.html', qas)

@login_required
@user_passes_test(is_admin)
def add_qa(request):
    if request.method == 'POST':
        qa_form = qaForm(request.POST)
        if qa_form.is_valid():
            qa_form.save()
            return redirect('question_answer_list')
    else:
        qa_form = qaForm()
    return render(request,'admin/qa_add_form.html',{'form' : qa_form})

@login_required
@user_passes_test(is_admin)
def update_qa(request,qa_id):
    qa_info = QuestionAndAnswer.objects.get(pk= qa_id)

    if request.method == 'POST':
        qa_form = qaForm(request.POST, instance=qa_info)
        if qa_form.is_valid():
            qa_form.save()
            return redirect('question_answer_list')
    else:
        qa_form = qaForm(instance=qa_info)

    return render(request,'admin/qa_update.html',{'form':qa_form})

@login_required
@user_passes_test(is_admin)
def delete_qa(request,qa_id):
    qa_info = QuestionAndAnswer.objects.get(pk= qa_id)
    if qa_info.del_flag == 0:
        qa_info.del_flag = 1
        qa_info.save()
    else:
        qa_info.del_flag = 0
        qa_info.save()

    return redirect('question_answer_list')