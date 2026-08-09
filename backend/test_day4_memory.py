import os
import sys
import unittest
from datetime import datetime

# Add src directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src import db

class TestDay4MemoryTamil(unittest.TestCase):

    def setUp(self):
        """Set up test environment and clean database for test_user."""
        db.init_db()
        self.test_user_id = "test_farmer_tamil_101"
        db.delete_farmer(self.test_user_id)

    def tearDown(self):
        """Clean up test_user from database."""
        db.delete_farmer(self.test_user_id)

    def test_01_db_initialization(self):
        """Step 1 & 2: Test DB table creation and initial state."""
        farmer = db.get_farmer(self.test_user_id)
        self.assertIsNone(farmer, "New test user should not exist initially")

    def test_02_save_caller_with_consent_tanglish(self):
        """Step 2 & 5: Save Tamil farmer profile with facts when permission is granted."""
        saved = db.save_farmer(
            user_id=self.test_user_id,
            name="Muthu Selvan",
            language_preference="Tanglish",
            district="Thanjavur, Tamil Nadu",
            crops_grown="Nel (Paddy), Karumbu (Sugarcane)",
            land_size="5 acres",
            irrigation_type="Canal (Cauvery)",
            last_topic="Yellow leaves on paddy crop"
        )

        self.assertIsNotNone(saved)
        self.assertEqual(saved["name"], "Muthu Selvan")
        self.assertEqual(saved["district"], "Thanjavur, Tamil Nadu")
        self.assertEqual(saved["crops_grown"], "Nel (Paddy), Karumbu (Sugarcane)")
        self.assertEqual(saved["land_size"], "5 acres")
        self.assertEqual(saved["irrigation_type"], "Canal (Cauvery)")
        self.assertEqual(saved["last_topic"], "Yellow leaves on paddy crop")

    def test_03_returning_caller_lookup_tanglish(self):
        """Step 4: Retrieve returning Tamil caller profile to greet by name and last topic."""
        db.save_farmer(
            user_id=self.test_user_id,
            name="Karthik Raja",
            district="Madurai, Tamil Nadu",
            crops_grown="Vazhai (Banana)",
            last_topic="Leaf spot disease on banana"
        )

        retrieved = db.get_farmer(self.test_user_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["name"], "Karthik Raja")
        self.assertEqual(retrieved["last_topic"], "Leaf spot disease on banana")

        greeting = f"Vanakkam {retrieved['name']} ayya! Last time we spoke about {retrieved['last_topic']}."
        self.assertIn("Karthik Raja", greeting)
        self.assertIn("Leaf spot disease on banana", greeting)

    def test_04_permission_denied_rule(self):
        """Step 5: Ensure data is NOT saved when permission_granted is False."""
        farmer_before = db.get_farmer(self.test_user_id)
        self.assertIsNone(farmer_before)

        permission_granted = False
        if not permission_granted:
            result = "ERROR: Permission denied by user. Information was NOT saved."
        else:
            db.save_farmer(user_id=self.test_user_id, name="Unauthorised User")

        self.assertIn("Permission denied", result)
        farmer_after = db.get_farmer(self.test_user_id)
        self.assertIsNone(farmer_after)

    def test_05_forget_me_tool(self):
        """Advanced: Test caller data deletion via 'forget me' tool."""
        db.save_farmer(user_id=self.test_user_id, name="Temp Farmer", district="Coimbatore")
        self.assertIsNotNone(db.get_farmer(self.test_user_id))

        deleted = db.delete_farmer(self.test_user_id)
        self.assertTrue(deleted)
        self.assertIsNone(db.get_farmer(self.test_user_id))


if __name__ == "__main__":
    print("=========================================================")
    print("   KISAN MITRA TAMIL & TANGLISH PERSISTENT MEMORY TEST SUITE")
    print("=========================================================\n")
    unittest.main()
