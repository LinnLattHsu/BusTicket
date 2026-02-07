import pytest
from decimal import Decimal
from django.urls import reverse
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
from django.utils import timezone
from myapp.models import Feedback
from django.contrib.messages import get_messages
from myapp.models import Route, Operator, Bus, Schedule, Seat_Status
from pytest_django.asserts import assertContains, assertTemplateUsed
from django.test import TestCase, Client



User = get_user_model()
@pytest.mark.django_db
def test_soft_delete_user_toggle_logic(client):
    """Test that an admin can toggle del_flag from 0 to 1."""
    admin_user = User.objects.create_superuser(
        email="admin@test.com",
        password="password",
        name="System Admin"
    )
    client.force_login(admin_user) 

    target_user = User.objects.create(
        name="testuser",
        user_id=999,
        del_flag=0
    )

    url = reverse('soft_delete_user', kwargs={'user_id': 999})
    response = client.get(url) 

    target_user.refresh_from_db()
    assert target_user.del_flag == 1
    assert response.status_code == 302
    assert response.url == reverse('user_home')


@pytest.mark.django_db
def test_soft_delete_user_undo_logic(client):
    """Test that calling it again toggles del_flag back from 1 to 0."""
    admin_user = User.objects.create_superuser(
        email="admin2@test.com",
        password="password",
        name="Admin Two"
    )
    client.force_login(admin_user)

    target_user = User.objects.create(name="undo_user", user_id=888, del_flag=1)

    url = reverse('soft_delete_user', kwargs={'user_id': 888})
    client.get(url)

    target_user.refresh_from_db()
    assert target_user.del_flag == 0


@pytest.mark.django_db
def test_soft_delete_user_permission_denied(client):
    """Test that a non-logged-in user cannot access the view."""
    target_user = User.objects.create(name="protected", user_id=777, del_flag=0)
    url = reverse('soft_delete_user', kwargs={'user_id': 777})

    response = client.get(url)

    assert response.status_code == 302
    assert 'login' in response.url

# test for bus management
class BusViewTests(TestCase):
    def setUp(self):
        """Set up the test environment."""
        # Create user with mandatory fields (email and name as per your model)
        self.user = User.objects.create_user(
            email='admin@example.com',
            name='Admin User',
            password='password123',
            is_staff=True
        )

        self.client = Client()
        # Login using the credentials defined above
        self.client.login(email='admin@example.com', password='password123')

        # Create Operator first because Bus depends on it (ForeignKey)
        self.operator = Operator.objects.create(operator_name="Express Line")

        # Create Bus instance
        self.bus = Bus.objects.create(
            license_no="YGN-1234",
            seat_capacity=45,
            bus_type="VIP",
            operator=self.operator,
            del_flag=0
        )

    def test_update_bus_post(self):
        """Test updating bus details."""
        # Use the name 'update_bus' directly without any prefix
        url = reverse('bus_update', kwargs={'bus_id': self.bus.id})

        updated_data = {
            'license_no': 'MDY-9999',
            'seat_capacity': 30,
            'bus_type': 'Standard',
            'operator': self.operator.id,
        }

        response = self.client.post(url, data=updated_data)

        # 302 means redirect was successful
        self.assertEqual(response.status_code, 302)

        self.bus.refresh_from_db()
        self.assertEqual(self.bus.license_no, 'MDY-9999')

    def test_delete_bus_toggle(self):
        """Test the toggle logic for del_flag (0 to 1)."""
        url = reverse('bus_delete', kwargs={'bus_id': self.bus.id})

        # First toggle: Change 0 to 1
        response = self.client.get(url)
        self.bus.refresh_from_db()
        self.assertEqual(self.bus.del_flag, 1)
        self.assertRedirects(response, reverse('bus_home'))

    def test_access_denied_for_anonymous_user(self):
        """Ensure non-logged in users are redirected."""
        self.client.logout()
        url = reverse('bus_update', kwargs={'bus_id': self.bus.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)


# test for schedule management
class ScheduleTests(TestCase):
    def setUp(self):
        # 1. Create User (Using your custom model fields)
        self.password = 'password123'
        self.admin_user = User.objects.create_superuser(
            name='admin',
            email='admin@test.com',
            password=self.password
        )

        # 2. Create Operator
        # Note: If Operator has a field like 'user', assign it here.
        # If it doesn't have 'name', this is usually where the error is.
        self.operator = Operator.objects.create(operator_name='Test Operator')

        # 3. Create Bus and Route
        self.bus = Bus.objects.create(
            license_no="B123",
            seat_capacity=6,
            operator=self.operator
        )
        self.route = Route.objects.create(
            origin="City A",
            destination="City B"
        )

        self.client = Client()

    def test_add_schedule_creates_seats(self):
        # Ensure login matches the email used in setUp
        self.client.login(email='admin@test.com', password=self.password)

        form_data = {
            'bus': self.bus.id,  # Use the actual PK field name
            'route': self.route.id,
            'date': '2026-05-20',
            'time': '14:30',
            'price': 500,
        }

        # Submit to the 'schedule_add' name (ensure this matches urls.py)
        response = self.client.post(reverse('schedule_add'), data=form_data)

        # If this fails, the view is redirecting back to the form because of errors
        self.assertEqual(response.status_code, 302)

        # Verify logic
        schedule = Schedule.objects.filter(bus=self.bus).first()
        self.assertIsNotNone(schedule)  # This will now pass
        self.assertEqual(Seat_Status.objects.filter(schedule=schedule).count(), 6)

    def test_update_schedule(self):
        self.client.login(email='admin@test.com', password=self.password)

        schedule = Schedule.objects.create(
            bus=self.bus, route=self.route, date='2026-05-20',
            time='14:30', price=500
        )

        update_data = {
            'bus': self.bus.id,
            'route': self.route.id,
            'date': '2026-05-20',
            'time': '14:30',
            'price': 750,  # New Price
        }

        # Use the name 'schedule_update'
        response = self.client.post(reverse('schedule_update', args=[schedule.id]), data=update_data)

        schedule.refresh_from_db()
        # Use Decimal() for the comparison
        self.assertEqual(schedule.price, Decimal('750'))

    def test_soft_delete_schedule(self):
        self.client.login(email='admin@test.com', password=self.password)

        schedule = Schedule.objects.create(
            bus=self.bus, route=self.route, date='2026-05-20',
            time='14:30', price=500, del_flag=0
        )

        # First call: Toggle 0 to 1
        self.client.get(reverse('schedule_delete', args=[schedule.id]))
        schedule.refresh_from_db()
        self.assertEqual(schedule.del_flag, 1)



@pytest.mark.django_db
class TestFeedbackView:

    @pytest.fixture
    def user(self, django_user_model):
        """Create a standard user for testing."""
        return django_user_model.objects.create_user(
            email="test@example.com",
            password="password123",
            name="Test User"
        )

    def test_feedback_get_request(self, client):
        """Test that the feedback page loads with an empty form."""
        url = reverse('feedback')
        response = client.get(url)

        assert response.status_code == 200
        assert 'form' in response.context
        assert response.context['active_page'] == 'feedback'

    def test_feedback_post_success(self, client, user):
        """Test successful feedback submission when logged in."""
        client.force_login(user)
        url = reverse('feedback')

        data = {
            'overall_rating': 5,
            'message': 'Great ride!'
        }

        response = client.post(url, data)

        if response.status_code == 200:
            print(response.context['form'].errors)

        assert response.status_code == 302
        assert response.url == reverse('feedback_success')

        feedback = Feedback.objects.last()
        assert feedback.customer == user
        assert feedback.overall_rating == 5
        assert feedback.message == 'Great ride!'

        messages = list(get_messages(response.wsgi_request))
        assert "Thank you for your feedback!" in str(messages[0])

    def test_feedback_post_invalid_form(self, client, user):
        """Test submission with missing required fields."""
        client.force_login(user)
        url = reverse('feedback')

        data = {}
        response = client.post(url, data)

        assert response.status_code == 200
        assert 'form' in response.context
        assert not response.context['form'].is_valid()

        messages = list(get_messages(response.wsgi_request))
        assert "There was an error submitting" in str(messages[0])

    def test_feedback_anonymous_user_fail(self, client):
        """Test that feedback fails if user is not logged in."""
        url = reverse('feedback')
        data = {'subject': 'Hello', 'message': 'World', 'rating': 5}
        response = client.post(url, data)

        assert response.status_code in [200, 302]


@pytest.mark.django_db
class TestSearchRoutes:

    def test_search_routes_past_date(self, client):
        url = reverse('search_routes')
        # Use the Django timezone to go back 5 days
        past_date = (timezone.now() - timedelta(days=5)).strftime('%Y-%m-%d')

        data = {
            'origin': 'Yangon',
            'destination': 'Mandalay',
            'date': past_date,
        }

        response = client.get(url, data)

        # assertContains also checks whether the status code is 200 at the same time
        assertContains(response, 'No routes found for the selected data.')

    def test_search_routes_missing_fields(self, client):
        url = reverse('search_routes')
        data = {
            'origin': 'Yangon',
            # Destination and date are not included
        }

        response = client.get(url, data)

        assertContains(response, 'Please enter origin, destination and date.')

    def test_search_routes_success(self, client):

        # 1. Setup Data: setup required data for testing
        operator = Operator.objects.create(operator_name="Elite", del_flag=0)
        route = Route.objects.create(origin="Yangon", destination="Mandalay", del_flag=0)
        bus = Bus.objects.create(bus_type="VIP", operator=operator, del_flag=0)

        # Define future date
        future_date = (timezone.now() + timedelta(days=2)).date()

        schedule = Schedule.objects.create(
            route=route,
            bus=bus,
            date=future_date,
            time="08:00:00",
            price=50000,
            del_flag=0
        )

        # 2. Action: define the data that will be sent from the search form
        url = reverse('search_routes')
        search_query = {
            'origin': 'Yangon',
            'destination': 'Mandalay',
            'date': future_date.strftime('%Y-%m-%d'),
            'bus_type': 'VIP'
        }

        # 3. Make request
        response = client.get(url, search_query)

        # 4. Assertions: test the result
        assert response.status_code == 200
        assertTemplateUsed(response, 'available_routes.html')

        # Check whether schedules are included in the context
        assert 'schedules' in response.context
        assert response.context['schedules'].count() == 1

        # Check whether the operator name and bus type are included in the displayed HTML
        assertContains(response, 'Elite')
        assertContains(response, 'VIP')
        assertContains(response, 'Yangon')
        assertContains(response, 'Mandalay')


@pytest.mark.django_db
class TestSeatSelectionView:

    @pytest.fixture
    def setup_data(self):
        op = Operator.objects.create(operator_name="Famous Express")
        route = Route.objects.create(origin="Yangon", destination="Mandalay")
        bus = Bus.objects.create(
            license_no="YGN-1234",
            seat_capacity=6,
            bus_type="VIP",
            operator=op
        )

        schedule = Schedule.objects.create(
            bus=bus,
            route=route,
            date="2026-02-10",
            time="08:00:00",  # field name က 'time' ဖြစ်ရပါမယ်
            price=Decimal("20000")
        )
        return schedule

    def test_seat_selection_view_success(self, client, setup_data):
        schedule = setup_data
        url = reverse('select_trip', kwargs={'schedule_id': schedule.id})

        response = client.get(url, {'number_of_seats': '2'})

        assert response.status_code == 200
        assert response.context['origin'] == "Yangon"
        assert response.context['destination'] == "Mandalay"
        assert response.context['total_price'] == Decimal("40000")

    def test_seat_data_logic(self, client, setup_data):
        schedule = setup_data
        url = reverse('select_trip', kwargs={'schedule_id': schedule.id})

        Seat_Status.objects.create(
            schedule=schedule,
            seat_no="A1",
            seat_status="Booked"
        )

        response = client.get(url, {'number_of_seats': '1'})
        seats_data = response.context['seats_data']

        a1_seat = next(s for s in seats_data if s['seat_name'] == "A1")
        assert a1_seat['is_booked'] is True

        a2_seat = next(s for s in seats_data if s['seat_name'] == "A2")
        assert a2_seat['is_booked'] is False


import pytest
from django.urls import reverse
from django.contrib.messages import get_messages
from decimal import Decimal
from myapp.models import Schedule, Booking, Seat_Status, Ticket, Payment, Route, Bus, Operator
from django.utils import timezone


@pytest.mark.django_db
class TestPaymentProcess:

    @pytest.fixture
    def setup_data(self, client, django_user_model):
        # 1. Create user
        user = django_user_model.objects.create_user(
            email = 'testuser@example.com',
            name = 'Test User',
            password='password123',)
        client.login(username='testuser@example.com', password='password123')

        # Create required schedule data
        operator = Operator.objects.create(operator_name="Elite", del_flag = 0)
        route = Route.objects.create(origin="Yangon", destination="Mandalay", del_flag = 0)
        bus = Bus.objects.create(bus_type="VIP", operator=operator,del_flag = 0)
        schedule = Schedule.objects.create(
            route=route,
            bus=bus,
            date=timezone.now().date() + timedelta(days=1),
            time="08:00:00",
            price=40000,
            del_flag = 0
        )

        # Create seat status
        seat1 = Seat_Status.objects.create(schedule=schedule, seat_no="A1", seat_status='Available')
        seat2 = Seat_Status.objects.create(schedule=schedule, seat_no="A2", seat_status='Available')

        return user, schedule, [seat1, seat2]

    def test_process_payment_success(self, client, setup_data):
        # Check that the payment is successful with valid data
        user, schedule, seats = setup_data
        url = reverse('process_payment', kwargs={'user_id': user.pk})

        data = {
            'schedule_id': schedule.id,
            'selected_seats': 'A1, A2',
            'total_price': '80000',
            'payment_method': 'kpay',
        }

        response = client.post(url, data)

        # Check whether a redirect occurs
        assert response.status_code == 302

        # Check whether the Booking and Ticket are actually created in the database
        assert Booking.objects.filter(customer=user, schedule=schedule).exists()
        booking = Booking.objects.get(customer=user)
        assert Ticket.objects.filter(booking=booking).exists()

        # “3. Check whether the seat statuses have changed to ‘Unavailable’
        for seat in seats:
            seat.refresh_from_db()
            assert seat.seat_status == 'Unavailable'
            assert seat.booking == booking

    def test_process_payment_seat_already_taken(self, client, setup_data):
        # Race condition: another user purchases the seat first.
        user, schedule, seats = setup_data
        url = reverse('process_payment', kwargs={'user_id': user.pk})

        # Assume that another user has already taken the seat
        seats[0].seat_status = 'Unavailable'
        seats[0].save()

        data = {
            'schedule_id': schedule.id,
            'selected_seats': 'A1, A2',
            'total_price': '80000',
            'payment_method': 'kpay',
        }

        response = client.post(url, data)

        # Show an error message and redirect back to select_seats
        assert response.status_code == 302
        messages = list(get_messages(response.wsgi_request))
        actual_message = str(messages[0])
        assert "An unexpected error occurred" in actual_message

        # Check that the booking was not created
        assert not Booking.objects.filter(customer=user).exists()


@pytest.mark.django_db
class TestRouteAndOperatorRoles:
            """Tests for the core roles of Route and Operator models."""

            def test_operator_setup_and_str(self):
                """Verify Operator role: holding company info and correct display."""
                operator = Operator.objects.create(operator_name="Mandalar Minn")
                assert operator.operator_name == "Mandalar Minn"
                assert str(operator) == "Mandalar Minn"
                assert operator.del_flag == 0  # Default role is 'Active'

            def test_route_setup_and_str(self):
                """Verify Route role: defining the path between origin and destination."""
                route = Route.objects.create(origin="Yangon", destination="Taunggyi")
                assert route.origin == "Yangon"
                assert route.destination == "Taunggyi"
                # Tests the specific arrow format you wrote in your __str__
                assert str(route) == "Yangon -> Taunggyi"

            def test_soft_delete_operator_role(self):
                """Verify the 'Deactivation' role using del_flag."""
                op = Operator.objects.create(operator_name="Test Operator")
                # Soft delete action
                op.del_flag = 1
                op.save()

                # Verify the data persists but the flag has changed
                db_op = Operator.objects.get(operator_name="Test Operator")
                assert db_op.del_flag == 1

            def test_route_meta_plural(self):
                """Verify the Meta role: ensures 'Routes' shows correctly in Admin."""
                assert str(Route._meta.verbose_name_plural) == "Routes"
