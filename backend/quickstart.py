#!/usr/bin/env python3
"""
Quick start script for testing the authentication API.

This script demonstrates basic authentication flows.
Run after setting up the backend server.
"""

import requests
import json
from typing import Optional

# Configuration
BASE_URL = "http://localhost:8000/api/v1"


class AuthClient:
    """Simple client for testing authentication endpoints."""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None

    def register(self, email: str, password: str, first_name: str, last_name: str) -> dict:
        """Register a new user."""
        response = requests.post(
            f"{self.base_url}/auth/register",
            json={
                "email": email,
                "password": password,
                "first_name": first_name,
                "last_name": last_name,
            },
        )
        response.raise_for_status()
        return response.json()

    def login(self, email: str, password: str) -> dict:
        """Login and store tokens."""
        response = requests.post(
            f"{self.base_url}/auth/login",
            json={"email": email, "password": password},
        )
        response.raise_for_status()
        data = response.json()
        self.access_token = data["access_token"]
        self.refresh_token = data["refresh_token"]
        return data

    def get_profile(self) -> dict:
        """Get current user profile."""
        if not self.access_token:
            raise ValueError("Not authenticated. Please login first.")

        response = requests.get(
            f"{self.base_url}/auth/me",
            headers={"Authorization": f"Bearer {self.access_token}"},
        )
        response.raise_for_status()
        return response.json()

    def refresh(self) -> dict:
        """Refresh access token."""
        if not self.refresh_token:
            raise ValueError("No refresh token available.")

        response = requests.post(
            f"{self.base_url}/auth/refresh",
            json={"refresh_token": self.refresh_token},
        )
        response.raise_for_status()
        data = response.json()
        self.access_token = data["access_token"]
        return data


def main():
    """Run authentication flow examples."""
    print("🚀 Authentication API Quick Start\n")

    client = AuthClient()

    # Example 1: Register
    print("1️⃣ Registering new user...")
    try:
        user_data = client.register(
            email="demo@example.com",
            password="SecurePassword123!",
            first_name="Demo",
            last_name="User",
        )
        print(f"✅ Registration successful!")
        print(f"   User ID: {user_data['user_id']}")
        print(f"   Email: {user_data['email']}")
        print(f"   Email Verified: {user_data['email_verified']}")
        print()
    except requests.exceptions.HTTPError as e:
        print(f"❌ Registration failed: {e.response.json()['detail']}")
        print()

    # Note: In real scenario, user needs to verify email first
    print("⚠️  In production, user must verify email before login")
    print("   For testing, you may need to manually mark email as verified in DB\n")

    # Example 2: Login (will fail if email not verified)
    print("2️⃣ Attempting login...")
    try:
        login_data = client.login(
            email="demo@example.com",
            password="SecurePassword123!",
        )
        print(f"✅ Login successful!")
        print(f"   Access Token: {login_data['access_token'][:50]}...")
        print(f"   User: {login_data['user']['first_name']} {login_data['user']['last_name']}")
        print()

        # Example 3: Get Profile
        print("3️⃣ Getting user profile...")
        profile = client.get_profile()
        print(f"✅ Profile retrieved!")
        print(f"   Name: {profile['full_name']}")
        print(f"   Email: {profile['email']}")
        print(f"   Role: {profile['role']}")
        print()

    except requests.exceptions.HTTPError as e:
        error_detail = e.response.json()['detail']
        print(f"❌ Login failed: {error_detail}")
        print()

    print("📚 For more examples, check the API docs at: http://localhost:8000/docs")


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to the API server.")
        print("   Make sure the backend is running:")
        print("   cd backend && uvicorn app.main:app --reload")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
