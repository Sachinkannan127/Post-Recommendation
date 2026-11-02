"""
Database Connection Manager.
Attempts to connect to MongoDB Atlas using provided URI.
If unavailable or authentication fails, seamlessly falls back to local MockDatabase.
"""
import os
import logging
from typing import Tuple, Any, Optional
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from backend.app.db.mock_db import MockDatabase

logger = logging.getLogger("recsys.db")
logging.basicConfig(level=logging.INFO)

DEFAULT_LOCAL_STORAGE = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "local_db.json")

class DatabaseManager:
    _instance: Optional["DatabaseManager"] = None

    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.db: Any = None
        self.is_live: bool = False
        self.connection_status: str = "Uninitialized"
        self.storage_file = os.path.abspath(DEFAULT_LOCAL_STORAGE)
        os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
        self._initialize()

    def _initialize(self):
        mongo_uri = os.getenv(
            "MONGODB_URI",
            "mongodb+srv://Testusers:JyzhXqF0DxjhjllK@cluster0.947yt.mongodb.net/social_commerce_db"
        )
        db_name = os.getenv("MONGODB_DB_NAME", "social_commerce_db")

        # Attempt live connection
        try:
            logger.info("Connecting to MongoDB at: %s...", mongo_uri.split("@")[-1] if "@" in mongo_uri else mongo_uri)
            test_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=2500)
            # Test ping
            test_client.admin.command("ping")
            self.client = test_client
            self.db = test_client[db_name]
            self.is_live = True
            self.connection_status = f"Connected to Live MongoDB Atlas ({db_name})"
            logger.info("Successfully connected to live MongoDB Atlas.")
            return
        except Exception as e:
            logger.warning("Could not authenticate/connect with live MongoDB (%s). Falling back to resilient Mock Database.", e)
            self.is_live = False
            self.connection_status = f"Mock In-Memory / File-backed Database ({os.path.basename(self.storage_file)})"
            self.db = MockDatabase(name=db_name, storage_path=self.storage_file)

    def reconnect(self, new_uri: str, db_name: str = "social_commerce_db") -> Tuple[bool, str]:
        """Allows dynamically reconnecting with a fresh URI provided by recruiter/user."""
        try:
            test_client = MongoClient(new_uri, serverSelectionTimeoutMS=3000)
            test_client.admin.command("ping")
            self.client = test_client
            self.db = test_client[db_name]
            self.is_live = True
            self.connection_status = f"Connected to Live MongoDB Atlas ({db_name})"
            return True, "Connected successfully."
        except Exception as e:
            return False, str(e)

    def get_db(self) -> Any:
        return self.db

    def get_status(self) -> dict:
        coll_counts = {}
        try:
            if self.db is not None:
                # Count for standard collections
                collections = [
                    "posts", "postembeddings", "postengagements", "postmetrics",
                    "postcomments", "follows", "views", "carts", "orders",
                    "sellerdetails", "productcategories", "productsubcategories",
                    "variants", "products"
                ]
                for c in collections:
                    coll = self.db[c]
                    coll_counts[c] = coll.count_documents({})
        except Exception as e:
            logger.error("Error fetching collection counts: %s", e)

        return {
            "is_live_mongodb": self.is_live,
            "status": self.connection_status,
            "collection_counts": coll_counts,
            "total_documents": sum(coll_counts.values())
        }


# Singleton accessor
_db_manager = DatabaseManager()

def get_db():
    return _db_manager.get_db()

def get_db_manager() -> DatabaseManager:
    return _db_manager
