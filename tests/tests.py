import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def client():
    return APIClient()


@pytest.mark.django_db
def test_create_user(client):
    data = {
        'username': 'testuser',
        'email': 'test@test.com',
        'password': 'StrongPass123!',
        'first_name': 'Test',
        'last_name': 'User'
    }
    response = client.post('/api/users/', data)
    if response.status_code != 201:
        print("Status code:", response.status_code)
        print("Response data:", response.data)
    assert response.status_code == 201
    assert User.objects.count() == 1
    assert response.data['username'] == 'testuser'


@pytest.mark.django_db
def test_get_ingredients(client):
    response = client.get('/api/ingredients/')
    assert response.status_code == 200


@pytest.mark.django_db
def test_get_tags(client):
    response = client.get('/api/tags/')
    assert response.status_code == 200