import importlib.util
import sqlite3
import sys
import types
import unittest
from pathlib import Path
from unittest import mock


eel_stub = types.ModuleType("eel")
eel_stub.expose = lambda function: function
eel_stub.init = lambda *args, **kwargs: None
eel_stub.start = lambda *args, **kwargs: None
sys.modules.setdefault("eel", eel_stub)

_memory_connection = sqlite3.connect(":memory:")
with mock.patch("sqlite3.connect", return_value=_memory_connection):
    spec = importlib.util.spec_from_file_location("app_main", Path(__file__).with_name("main.py"))
    app_main = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app_main)


class TaskDatabaseTests(unittest.TestCase):
    def setUp(self):
        app_main.cursor.execute("DROP TABLE IF EXISTS task")
        app_main.cursor.execute(
            """
            CREATE TABLE task (
                i INTEGER,
                name TEXT,
                color TEXT,
                col INTEGER,
                row INTEGER,
                len INTEGER
            )
            """
        )
        app_main.con.commit()

    def tearDown(self):
        app_main.cursor.execute("DELETE FROM task")
        app_main.con.commit()

    def test_read_data_returns_empty_list_when_table_is_empty(self):
        self.assertEqual(app_main.read_data(), [])

    def test_add_to_base_inserts_task(self):
        app_main.addToBase(1, "Тестовая задача", [255, 128, 0], 2, 3, 4)

        self.assertEqual(
            app_main.read_data(),
            [(1, "Тестовая задача", "255 128 0", 2, 3, 4)],
        )

    def test_add_to_base_converts_numeric_fields_to_integers(self):
        app_main.addToBase(2, "Задача", [1, 2, 3], "5", "6", "7")

        self.assertEqual(
            app_main.read_data(),
            [(2, "Задача", "1 2 3", 5, 6, 7)],
        )

    def test_uploading_tasks_returns_all_saved_tasks(self):
        app_main.addToBase(1, "Первая", [10, 20, 30], 1, 2, 3)
        app_main.addToBase(2, "Вторая", [40, 50, 60], 4, 5, 6)

        self.assertEqual(
            app_main.uploadingTasks(),
            [
                (1, "Первая", "10 20 30", 1, 2, 3),
                (2, "Вторая", "40 50 60", 4, 5, 6),
            ],
        )

    def test_remove_deletes_task_by_id(self):
        app_main.addToBase(1, "Первая", [10, 20, 30], 1, 2, 3)
        app_main.addToBase(2, "Вторая", [40, 50, 60], 4, 5, 6)

        app_main.remove("task1")

        self.assertEqual(
            app_main.uploadingTasks(),
            [(2, "Вторая", "40 50 60", 4, 5, 6)],
        )

    def test_remove_does_not_delete_other_tasks(self):
        app_main.addToBase(2, "Задача 2", [1, 2, 3], 1, 1, 1)
        app_main.addToBase(3, "Задача 3", [4, 5, 6], 2, 2, 2)

        app_main.remove("task3")

        self.assertEqual(
            app_main.uploadingTasks(),
            [(2, "Задача 2", "1 2 3", 1, 1, 1)],
        )


if __name__ == "__main__":
    unittest.main()
