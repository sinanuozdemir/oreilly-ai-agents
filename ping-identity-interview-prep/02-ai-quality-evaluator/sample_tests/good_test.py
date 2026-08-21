"""
Example: Well-Written AI-Generated Test

This demonstrates what a high-quality AI-generated test looks like.
It should score 32+/40 on the evaluation rubric.

Key Qualities:
✅ Comprehensive coverage (happy path + errors)
✅ Specific assertions (not just assertTrue)
✅ Edge cases tested (None, empty, invalid)
✅ Maintainable structure (setUp, docstrings)
"""

import unittest
import requests
from typing import Dict, Any


class TestUserAPI(unittest.TestCase):
    """
    Test suite for User Management API.
    
    Covers:
    - User creation (success and failure cases)
    - Input validation
    - Edge cases and error handling
    """
    
    def setUp(self):
        """Set up test fixtures before each test."""
        self.base_url = "https://api.example.com/v1"
        self.headers = {
            "Authorization": "Bearer test-token",
            "Content-Type": "application/json"
        }
        self.test_user = {
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "role": "user"
        }
    
    def tearDown(self):
        """Clean up after each test."""
        # Clean up test data
        pass
    
    def test_create_user_success(self):
        """
        Test successful user creation with valid data.
        
        Expected: 201 Created with user details
        """
        response = requests.post(
            f"{self.base_url}/users",
            json=self.test_user,
            headers=self.headers
        )
        
        # Verify status code
        self.assertEqual(response.status_code, 201)
        
        # Verify response structure
        data = response.json()
        self.assertIn("id", data)
        self.assertIn("email", data)
        self.assertIn("created_at", data)
        
        # Verify data integrity
        self.assertEqual(data["email"], self.test_user["email"])
        self.assertEqual(data["first_name"], self.test_user["first_name"])
        self.assertEqual(data["last_name"], self.test_user["last_name"])
        
        # Verify ID format (UUID)
        self.assertIsInstance(data["id"], str)
        self.assertEqual(len(data["id"]), 36)  # UUID length
    
    def test_create_user_invalid_email(self):
        """
        Test user creation fails with invalid email format.
        
        Expected: 400 Bad Request with error details
        """
        invalid_user = self.test_user.copy()
        invalid_user["email"] = "not-an-email"
        
        response = requests.post(
            f"{self.base_url}/users",
            json=invalid_user,
            headers=self.headers
        )
        
        self.assertEqual(response.status_code, 400)
        
        data = response.json()
        self.assertIn("error", data)
        self.assertIn("email", data.get("details", {}))
    
    def test_create_user_duplicate_email(self):
        """
        Test user creation fails with duplicate email.
        
        Expected: 409 Conflict
        """
        # Create first user
        requests.post(
            f"{self.base_url}/users",
            json=self.test_user,
            headers=self.headers
        )
        
        # Try to create duplicate
        response = requests.post(
            f"{self.base_url}/users",
            json=self.test_user,
            headers=self.headers
        )
        
        self.assertEqual(response.status_code, 409)
        
        data = response.json()
        self.assertIn("error", data)
        self.assertIn("already exists", data.get("message", "").lower())
    
    def test_create_user_missing_required_fields(self):
        """
        Test user creation fails when required fields are missing.
        
        Expected: 400 Bad Request
        """
        incomplete_user = {"email": "incomplete@example.com"}
        
        response = requests.post(
            f"{self.base_url}/users",
            json=incomplete_user,
            headers=self.headers
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_create_user_empty_email(self):
        """
        Test user creation with empty email string.
        
        Expected: 400 Bad Request
        """
        user_with_empty_email = self.test_user.copy()
        user_with_empty_email["email"] = ""
        
        response = requests.post(
            f"{self.base_url}/users",
            json=user_with_empty_email,
            headers=self.headers
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_create_user_long_name(self):
        """
        Test user creation with very long name (boundary test).
        
        Expected: Handle gracefully (truncate or reject)
        """
        user_with_long_name = self.test_user.copy()
        user_with_long_name["first_name"] = "A" * 1000
        
        response = requests.post(
            f"{self.base_url}/users",
            json=user_with_long_name,
            headers=self.headers
        )
        
        # Should either succeed with truncation or fail gracefully
        self.assertIn(response.status_code, [201, 400])
    
    def test_get_user_success(self):
        """
        Test retrieving an existing user.
        
        Expected: 200 OK with user details
        """
        # First create a user
        create_response = requests.post(
            f"{self.base_url}/users",
            json=self.test_user,
            headers=self.headers
        )
        user_id = create_response.json()["id"]
        
        # Get the user
        response = requests.get(
            f"{self.base_url}/users/{user_id}",
            headers=self.headers
        )
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["id"], user_id)
        self.assertEqual(data["email"], self.test_user["email"])
    
    def test_get_user_not_found(self):
        """
        Test retrieving non-existent user.
        
        Expected: 404 Not Found
        """
        response = requests.get(
            f"{self.base_url}/users/non-existent-id",
            headers=self.headers
        )
        
        self.assertEqual(response.status_code, 404)
    
    def test_update_user_success(self):
        """
        Test updating user information.
        
        Expected: 200 OK with updated details
        """
        # Create user first
        create_response = requests.post(
            f"{self.base_url}/users",
            json=self.test_user,
            headers=self.headers
        )
        user_id = create_response.json()["id"]
        
        # Update user
        updates = {"first_name": "Updated"}
        response = requests.patch(
            f"{self.base_url}/users/{user_id}",
            json=updates,
            headers=self.headers
        )
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["first_name"], "Updated")
        self.assertEqual(data["email"], self.test_user["email"])  # Unchanged
    
    def test_delete_user_success(self):
        """
        Test deleting a user.
        
        Expected: 204 No Content
        """
        # Create user first
        create_response = requests.post(
            f"{self.base_url}/users",
            json=self.test_user,
            headers=self.headers
        )
        user_id = create_response.json()["id"]
        
        # Delete user
        response = requests.delete(
            f"{self.base_url}/users/{user_id}",
            headers=self.headers
        )
        
        self.assertEqual(response.status_code, 204)
        
        # Verify user is gone
        get_response = requests.get(
            f"{self.base_url}/users/{user_id}",
            headers=self.headers
        )
        self.assertEqual(get_response.status_code, 404)
    
    def test_unauthorized_access(self):
        """
        Test accessing API without authentication.
        
        Expected: 401 Unauthorized
        """
        response = requests.get(
            f"{self.base_url}/users",
            headers={}  # No auth header
        )
        
        self.assertEqual(response.status_code, 401)


class TestUserListAPI(unittest.TestCase):
    """Test suite for User List API."""
    
    def setUp(self):
        self.base_url = "https://api.example.com/v1"
        self.headers = {
            "Authorization": "Bearer test-token"
        }
    
    def test_list_users_pagination(self):
        """
        Test listing users with pagination.
        
        Expected: Paginated response with metadata
        """
        response = requests.get(
            f"{self.base_url}/users?limit=10&offset=0",
            headers=self.headers
        )
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn("users", data)
        self.assertIn("total", data)
        self.assertIn("limit", data)
        self.assertIn("offset", data)
        
        self.assertIsInstance(data["users"], list)
        self.assertLessEqual(len(data["users"]), 10)
    
    def test_list_users_filtering(self):
        """
        Test listing users with filters.
        
        Expected: Filtered results
        """
        response = requests.get(
            f"{self.base_url}/users?role=admin&active=true",
            headers=self.headers
        )
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        for user in data.get("users", []):
            self.assertEqual(user.get("role"), "admin")
            self.assertTrue(user.get("active", False))


if __name__ == "__main__":
    unittest.main()
