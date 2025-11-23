"""
Unit tests for database operations
"""
import unittest
import os
import tempfile
from datetime import datetime

from src.database.db_manager import DatabaseManager
from src.models.component import Component, ComponentType, ComponentStatus


class TestDatabaseManager(unittest.TestCase):
    """Test database manager functionality"""

    def setUp(self):
        """Set up test database"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = DatabaseManager(self.temp_db.name)

    def tearDown(self):
        """Clean up test database"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)

    def test_create_component(self):
        """Test creating a component"""
        component = Component(
            id=None,
            designation_1="Test Cylinder",
            designation_2="Double Acting",
            material_number="TEST-001",
            manufacturer_number="MFG-001",
            component_type=ComponentType.PNEUMATIC_CYLINDER,
            status=ComponentStatus.ACTIVE
        )

        component_id = self.db.create_component(component)
        self.assertIsNotNone(component_id)
        self.assertGreater(component_id, 0)

    def test_get_component(self):
        """Test retrieving a component"""
        component = Component(
            id=None,
            designation_1="Test Valve",
            designation_2="3/2 Way",
            material_number="TEST-002",
            manufacturer_number="MFG-002",
            component_type=ComponentType.SOLENOID_VALVE,
            status=ComponentStatus.ACTIVE
        )

        component_id = self.db.create_component(component)
        retrieved = self.db.get_component(component_id)

        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.designation_1, "Test Valve")
        self.assertEqual(retrieved.material_number, "TEST-002")

    def test_update_component(self):
        """Test updating a component"""
        component = Component(
            id=None,
            designation_1="Test Component",
            designation_2="Version 1",
            material_number="TEST-003",
            manufacturer_number="MFG-003",
            component_type=ComponentType.INITIATOR,
            status=ComponentStatus.ACTIVE
        )

        component_id = self.db.create_component(component)
        component.id = component_id
        component.designation_2 = "Version 2"
        component.status = ComponentStatus.UNDER_TEST

        self.db.update_component(component)
        updated = self.db.get_component(component_id)

        self.assertEqual(updated.designation_2, "Version 2")
        self.assertEqual(updated.status, ComponentStatus.UNDER_TEST)

    def test_get_statistics(self):
        """Test getting overall statistics"""
        stats = self.db.get_statistics()

        self.assertIsNotNone(stats)
        self.assertIn('total_components', stats)
        self.assertIn('total_test_runs', stats)
        self.assertIn('total_switching_cycles', stats)
        self.assertIn('total_hours', stats)


if __name__ == '__main__':
    unittest.main()
