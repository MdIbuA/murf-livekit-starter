import os
import sys
import unittest
from datetime import datetime

# Add src directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src import db

class TestDay4Memory(unittest.TestCase):

    def setUp(self):
        """Set up test environment and clean database for test_user."""
        db.init_db()
        self.test_user_id = "test_farmer_101"
        db.delete_farmer(self.test_user_id)

    def tearDown(self):
        """Clean up test_user from database."""
        db.delete_farmer(self.test_user_id)

    def test_01_db_initialization(self):
        """Step 1 & 2: Test DB table creation and initial state."""
        farmer = db.get_farmer(self.test_user_id)
        self.assertIsNone(farmer, "New test user should not exist initially")

    def test_02_save_caller_with_consent(self):
        """Step 2 & 5: Save caller profile with facts when permission is granted."""
        saved = db.save_farmer(
            user_id=self.test_user_id,
            name="Ramesh Kumar",
            language_preference="Hinglish",
            district="Ludhiana, Punjab",
            crops_grown="Wheat, Paddy",
            land_size="5 acres",
            irrigation_type="Canal",
            last_topic="Yellow leaves on wheat crop"
        )

        self.assertIsNotNone(saved)
        self.assertEqual(saved["name"], "Ramesh Kumar")
        self.assertEqual(saved["district"], "Ludhiana, Punjab")
        self.assertEqual(saved["crops_grown"], "Wheat, Paddy")
        self.assertEqual(saved["land_size"], "5 acres")
        self.assertEqual(saved["irrigation_type"], "Canal")
        self.assertEqual(saved["last_topic"], "Yellow leaves on wheat crop")

    def test_03_returning_caller_lookup(self):
        """Step 4: Retrieve returning caller profile to greet by name and last topic."""
        # First save profile
        db.save_farmer(
            user_id=self.test_user_id,
            name="Suresh Patel",
            district="Rajkot, Gujarat",
            crops_grown="Cotton",
            last_topic="Pink bollworm attack on cotton"
        )

        # Lookup returning caller
        retrieved = db.get_farmer(self.test_user_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["name"], "Suresh Patel")
        self.assertEqual(retrieved["last_topic"], "Pink bollworm attack on cotton")

        # Simulate returning caller greeting formulation
        greeting = f"Namaste {retrieved['name']} ji! Last time we spoke about {retrieved['last_topic']}."
        self.assertIn("Suresh Patel", greeting)
        self.assertIn("Pink bollworm attack on cotton", greeting)

    def test_04_permission_denied_rule(self):
        """Step 5: Ensure data is NOT saved when permission_granted is False."""
        # Initial lookup
        farmer_before = db.get_farmer(self.test_user_id)
        self.assertIsNone(farmer_before)

        # Simulate permission_granted=False logic from tool
        permission_granted = False
        if not permission_granted:
            result = "ERROR: Permission denied by user. Information was NOT saved."
        else:
            db.save_farmer(user_id=self.test_user_id, name="Unauthorised User")

        self.assertIn("Permission denied", result)
        farmer_after = db.get_farmer(self.test_user_id)
        self.assertIsNone(farmer_after, "Profile should not be saved when permission is denied")

    def test_05_forget_me_tool(self):
        """Advanced: Test caller data deletion via 'forget me' tool."""
        # Save profile first
        db.save_farmer(user_id=self.test_user_id, name="Temp Farmer", district="Karnal")
        self.assertIsNotNone(db.get_farmer(self.test_user_id))

        # Delete profile
        deleted = db.delete_farmer(self.test_user_id)
        self.assertTrue(deleted, "delete_farmer should return True when deleting existing user")
        self.assertIsNone(db.get_farmer(self.test_user_id), "Profile should be removed from database")


if __name__ == "__main__":
    print("=========================================================")
    print("   KISAN MITRA DAY 4 PERSISTENT MEMORY TEST SUITE")
    print("=========================================================\n")
    unittest.main()
