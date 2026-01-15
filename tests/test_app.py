"""Test Flask app creation and basic routes."""
import pytest


def test_app_creates(app):
    """Test that the app is created."""
    assert app is not None


def test_app_is_testing(app):
    """Test that the app is in testing mode."""
    assert app.config['TESTING'] is True


def test_index_route(client):
    """Test that the index route returns 200."""
    response = client.get('/')
    assert response.status_code == 200


def test_timelapse_route(client):
    """Test that the timelapse route returns 200."""
    response = client.get('/timelapse/', follow_redirects=True)
    assert response.status_code == 200


def test_config_route(client):
    """Test that the config route returns 200."""
    response = client.get('/config/', follow_redirects=True)
    assert response.status_code == 200


def test_gallery_route(client):
    """Test that the gallery route returns 200."""
    response = client.get('/gallery/', follow_redirects=True)
    assert response.status_code == 200


def test_videos_route(client):
    """Test that the videos route returns 200."""
    response = client.get('/videos/', follow_redirects=True)
    assert response.status_code == 200


def test_system_route(client):
    """Test that the system route returns 200."""
    response = client.get('/system/', follow_redirects=True)
    assert response.status_code == 200


def test_logs_route(client):
    """Test that the logs route returns 200."""
    response = client.get('/logs/', follow_redirects=True)
    assert response.status_code == 200


def test_api_status(client):
    """Test API status endpoint."""
    response = client.get('/api/status')
    assert response.status_code == 200
    data = response.get_json()
    assert 'last_capture' in data
    assert 'stats' in data


def test_system_api_metrics(client):
    """Test system metrics API endpoint."""
    response = client.get('/system/api/metrics')
    assert response.status_code == 200
    data = response.get_json()
    assert 'cpu_temp' in data or data.get('cpu_temp') is None
    assert 'memory' in data or data.get('memory') is None
