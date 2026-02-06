import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db
def test_soft_delete_user_toggle_logic(client): # Changed admin_client to client
    """
    Test that an admin can toggle del_flag from 0 to 1.
    """
    # 1. Setup: Manually create admin with the REQUIRED 'name' field
    admin_user = User.objects.create_superuser(
        email="admin@test.com",
        password="password",
        name="System Admin"  # This solves the TypeError
    )
    client.force_login(admin_user) 

    target_user = User.objects.create(
        name="testuser",
        user_id=999,
        del_flag=0
    )

    # 2. Action: Call the view using the logged-in 'client'
    url = reverse('soft_delete_user', kwargs={'user_id': 999})
    response = client.get(url) 

    # 3. Verification
    target_user.refresh_from_db()
    assert target_user.del_flag == 1
    assert response.status_code == 302 
    assert response.url == reverse('user_home')


@pytest.mark.django_db
def test_soft_delete_user_undo_logic(client): # Changed admin_client to client
    """
    Test that calling it again toggles del_flag back from 1 to 0.
    """
    # Log in an admin first
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
    """
    Test that a non-logged-in user cannot access the view.
    """
    # Ensure even regular creation uses the 'name' field
    target_user = User.objects.create(name="protected", user_id=777, del_flag=0)
    url = reverse('soft_delete_user', kwargs={'user_id': 777})

    response = client.get(url)

    assert response.status_code == 302
    assert 'login' in response.url