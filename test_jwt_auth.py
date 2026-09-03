"""
Test JWT authentication scheme
"""
import jwt
import requests
from datetime import datetime, timedelta

AUTH_URL = "http://localhost:8001"
JWT_SECRET = "your-jwt-secret-key-change-in-production"
SERVICE_ID = "taurus-backend"


def generate_jwt_token():
    """Generate JWT Token"""
    now = datetime.utcnow()
    payload = {
        "sub": SERVICE_ID,
        "iat": now,
        "exp": now + timedelta(minutes=60),
        "nbf": now,
        "ip": "127.0.0.1",
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return token


def test_health():
    """Test health check"""
    print("=" * 60)
    print("Test 1: Health check (no auth required)")
    print("=" * 60)
    
    response = requests.get(f"{AUTH_URL}/health/")
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.json()}")
    print()


def test_generate_with_jwt():
    """Test ticket generation using JWT"""
    print("=" * 60)
    print("Test 2: Generate ticket using JWT")
    print("=" * 60)
    
    token = generate_jwt_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    
    data = {
        "host_uuid": "550e8400-e29b-41d4-a716-446655440000",
        "action": "execute_command",
        "command": "ls -la",
        "expires_minutes": 5,
    }
    
    response = requests.post(
        f"{AUTH_URL}/api/v1/tickets/generate",
        headers=headers,
        json=data,
    )
    
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.json()}")
    print()
    
    return response


def test_generate_without_jwt():
    """Test without JWT (should fail)"""
    print("=" * 60)
    print("Test 3: Without JWT (should be rejected)")
    print("=" * 60)
    
    headers = {
        "Content-Type": "application/json",
    }
    
    data = {
        "host_uuid": "550e8400-e29b-41d4-a716-446655440000",
        "action": "execute_command",
    }
    
    response = requests.post(
        f"{AUTH_URL}/api/v1/tickets/generate",
        headers=headers,
        json=data,
    )
    
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.json()}")
    print()


def test_generate_with_invalid_jwt():
    """Test using invalid JWT"""
    print("=" * 60)
    print("Test 4: Using invalid JWT (should be rejected)")
    print("=" * 60)
    
    headers = {
        "Authorization": "Bearer invalid_token_here",
        "Content-Type": "application/json",
    }
    
    data = {
        "host_uuid": "550e8400-e29b-41d4-a716-446655440000",
        "action": "execute_command",
    }
    
    response = requests.post(
        f"{AUTH_URL}/api/v1/tickets/generate",
        headers=headers,
        json=data,
    )
    
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.json()}")
    print()


def test_generate_with_expired_jwt():
    """Test using expired JWT"""
    print("=" * 60)
    print("Test 5: Using expired JWT (should be rejected)")
    print("=" * 60)
    
    now = datetime.utcnow()
    payload = {
        "sub": SERVICE_ID,
        "iat": now - timedelta(hours=2),
        "exp": now - timedelta(hours=1),
        "nbf": now - timedelta(hours=2),
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    
    data = {
        "host_uuid": "550e8400-e29b-41d4-a716-446655440000",
        "action": "execute_command",
    }
    
    response = requests.post(
        f"{AUTH_URL}/api/v1/tickets/generate",
        headers=headers,
        json=data,
    )
    
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.json()}")
    print()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Taurus Auth JWT Authentication Tests")
    print("=" * 60 + "\n")
    
    test_health()
    test_generate_with_jwt()
    test_generate_without_jwt()
    test_generate_with_invalid_jwt()
    test_generate_with_expired_jwt()
    
    print("=" * 60)
    print("Tests completed!")
    print("=" * 60)