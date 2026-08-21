"""
Example: Poorly Written AI-Generated Test

This demonstrates common problems with AI-generated tests.
It should score <28/40 on the evaluation rubric.

Key Problems:
❌ No real assertions (just assertTrue(True))
❌ Tests don't match actual API structure
❌ No error case coverage
❌ No edge cases
❌ Poor maintainability (magic values, no docs)
"""

import unittest
import requests


class TestAPI(unittest.TestCase):
    def test_api(self):
        """Test API"""
        response = requests.get("/api/users")
        self.assertEqual(response.status_code, 200)
    
    def test_api_2(self):
        """Test API again"""
        response = requests.post("/api/users", json={})
        self.assertTrue(True)  # Meaningless assertion
    
    def test_user(self):
        """Test user"""
        r = requests.get("/api/user/123")
        self.assertEqual(r.status_code, 200)
    
    def test_another_thing(self):
        """Another test"""
        result = True
        self.assertTrue(result)


class TestUser(unittest.TestCase):
    def test1(self):
        r = requests.get("http://localhost:3000/users")
        self.assertEqual(r.status_code, 200)
    
    def test2(self):
        r = requests.post("http://localhost:3000/users", data={"a": "b"})
        print(r.text)  # Print instead of assertion
    
    def test3(self):
        # No actual test, just comments
        # TODO: implement this test
        pass


class TestSSO(unittest.TestCase):
    def test_sso(self):
        """Test SSO"""
        response = requests.get("https://sso.example.com/config")
        self.assertTrue(response.status_code == 200)
    
    def test_sso_login(self):
        """Test login"""
        r = requests.post("https://sso.example.com/login", json={
            "username": "admin",
            "password": "admin123"  # Hardcoded credentials!
        })
        self.assertEqual(r.status_code, 200)
        # No validation of response structure


# Syntax errors that would be caught by schema validation
def test_incomplete():
    # Missing class wrapper
    response = requests.get("/api")
    assert response.status_code == 200


class TestWithSyntaxError(unittest.TestCase):
    def test_broken(self)
        # Missing colon above
        self.assertTrue(True)
    
    def test_incomplete_assertion(self
        # Missing closing parenthesis
        self.assertEqual(1, 1


class TestNoAssertions(unittest.TestCase):
    def test_no_assert(self):
        """Test with no assertions"""
        response = requests.get("/api/users")
        print(response.json())  # Just printing, no validation
    
    def test_only_comments(self):
        """Test that's just comments"""
        # This test doesn't actually test anything
        # It just passes by default
        pass


class TestWeakAssertions(unittest.TestCase):
    def test_weak_1(self):
        """Always passes"""
        self.assertTrue(True)
    
    def test_weak_2(self):
        """Also always passes"""
        self.assertFalse(False)
    
    def test_weak_3(self):
        """Tests nothing meaningful"""
        x = 5
        self.assertEqual(x, 5)  # Testing Python, not the API


class TestWrongAPI(unittest.TestCase):
    def test_wrong_endpoint(self):
        """Tests endpoint that doesn't exist"""
        response = requests.get("/api/v999/nonexistent")
        self.assertEqual(response.status_code, 200)  # Will fail
    
    def test_wrong_method(self):
        """Uses wrong HTTP method"""
        response = requests.delete("/api/users/create")  # Should be POST
        self.assertEqual(response.status_code, 201)


if __name__ == "__main__":
    unittest.main()
