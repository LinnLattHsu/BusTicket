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
        # Django timezone သုံးပြီး ၅ ရက် အနောက်ကို ဆုတ်မယ်
        past_date = (timezone.now() - timedelta(days=5)).strftime('%Y-%m-%d')

        data = {
            'origin': 'Yangon',
            'destination': 'Mandalay',
            'date': past_date,
        }

        response = client.get(url, data)

        # assertContains က status_code=200 ဖြစ်မဖြစ်ပါ တစ်ခါတည်း စစ်ပေးတယ်
        assertContains(response, 'No routes found for the selected data.')

    def test_search_routes_missing_fields(self, client):
        url = reverse('search_routes')
        data = {
            'origin': 'Yangon',
            # destination နဲ့ date မပါဘူး
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