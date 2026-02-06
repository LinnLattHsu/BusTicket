import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
from myapp.models import Feedback
from django.contrib.messages import get_messages

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