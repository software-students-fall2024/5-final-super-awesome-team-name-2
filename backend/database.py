"""
backend.database

This module defines the Database class for interacting with the MongoDB backend.
It includes methods for user authentication, budget management, and expense tracking.
"""

from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime
import os
from pymongo import MongoClient
from bson import ObjectId


@dataclass
class Expense:
    """
    Represents a financial expense.
    """

    amount: float
    description: str
    date: datetime
    _id: Optional[ObjectId] = None

    @property
    def id(self) -> Optional[str]:
        """Return the string representation of the expense ID."""
        return str(self._id) if self._id else None


class Database:
    """
    Handles all interactions with the MongoDB database for the finance application.
    """

    def __init__(self, uri: str = None):
        """
        Initialize the Database instance and ensure the default user exists.
        """
        if uri is None:
            uri = os.environ.get("MONGO_URI", "mongodb://mongodb:27017/")
        self.client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        self.db = self.client.finance_db
        self._ensure_default_user()

    def _ensure_default_user(self):
        """
        Ensure that the default user exists in the database with an initial budget.
        """
        if not self.db.users.find_one({"username": "user"}):
            self.db.users.insert_one(
                {
                    "username": "user",
                    "password": "pw",
                    "budget": 0.0,
                    "total_expenses": 0.0,
                }
            )

    def get_user_data(self, username: str) -> dict:
        """
        Retrieve data for a specific user.
        """
        return self.db.users.find_one({"username": username})

    def update_budget(self, username: str, amount: float) -> None:
        """
        Update the budget for a specific user.
        """
        try:
            amount = float(amount)
            if not isinstance(amount, (int, float)) or amount < 0:
                raise ValueError("Invalid budget amount")

            self.db.users.update_one(
                {"username": username}, {"$set": {"budget": amount}}
            )
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid budget value: {str(e)}") from e

    def add_expense(self, username: str, amount: float, description: str) -> None:
        """
        Add a new expense for a specific user.
        """
        expense = {
            "username": username,
            "amount": amount,
            "description": description,
            "date": datetime.utcnow(),
        }
        self.db.expenses.insert_one(expense)

        self.db.users.update_one(
            {"username": username}, {"$inc": {"total_expenses": amount}}
        )

    def remove_expense(self, username: str, expense_id: str) -> bool:
        """
        Remove an existing expense for a specific user.
        """
        expense = self.db.expenses.find_one(
            {"_id": ObjectId(expense_id), "username": username}
        )
        if expense:
            self.db.expenses.delete_one({"_id": ObjectId(expense_id)})
            self.db.users.update_one(
                {"username": username}, {"$inc": {"total_expenses": -expense["amount"]}}
            )
            return True
        return False

    def get_expenses(self, username: str) -> List[Expense]:
        """
        Retrieve all expenses for a specific user.
        """
        expenses = self.db.expenses.find({"username": username}).sort("date", -1)
        return [Expense(**exp) for exp in expenses]