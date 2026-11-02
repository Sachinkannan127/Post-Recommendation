"""
Database Connection Manager.
Configured with the official assignment MongoDB Atlas URI:
mongodb+srv://Testusers:JyzhXqF0DxjhjllK@cluster0.947yt.mongodb.net/

Attempts live connection to Atlas first. If MongoDB Atlas rejects authentication
or network blocks occur, it reports the exact status and seamlessly falls back
to the resilient local database so recommendations and evaluation remain functional.
"""
import os
import logging
from typing import Tuple, Any, Optional
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from dotenv import load_dotenv

from backend.app.db.mock_db import MockDatabase

load_dotenv(override=True)

logger = logging.getLogger("recsys.db")
logging.basicConfig(level=logging.INFO)

DEFAULT_LOCAL_STORAGE = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "local_db.json")
DEFAULT_ASSIGNMENT_URI = "mongodb+srv://Testusers:JyzhXqF0DxjhjllK@cluster0.947yt.mongodb.net/"

class DatabaseManager:
    _instance: Optional["DatabaseManager"] = None

    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.db: Any = None
        self.is_live: bool = False
        self.connection_status: str = "Uninitialized"
        self.last_error: Optional[str] = None
        self.target_uri: str = os.getenv("MONGODB_URI", DEFAULT_ASSIGNMENT_URI)
        self.db_name: str = os.getenv("MONGODB_DB_NAME", "social_commerce_db")
        self.storage_file = os.path.abspath(DEFAULT_LOCAL_STORAGE)
        os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
        self._initialize()

    def _initialize(self):
        # Target URI from assignment
        self.target_uri = os.getenv("MONGODB_URI", DEFAULT_ASSIGNMENT_URI)
        self.db_name = os.getenv("MONGODB_DB_NAME", "social_commerce_db")

        # Attempt live connection to MongoDB Atlas
        try:
            logger.info("Connecting to MongoDB Atlas at: %s...", self.target_uri.split("@")[-1] if "@" in self.target_uri else self.target_uri)
            test_client = MongoClient(self.target_uri, serverSelectionTimeoutMS=2500)
            # Try to query or ping
            test_client.admin.command("ping")
            self.client = test_client
            self.db = test_client[self.db_name]
            self.is_live = True
            self.last_error = None
            self.connection_status = f"Connected to Live MongoDB Atlas ({self.db_name})"
            logger.info("Successfully authenticated and connected to live MongoDB Atlas.")
            return
        except Exception as e:
            err_msg = str(e)
            self.last_error = err_msg
            logger.warning("MongoDB Atlas returned auth/connection failure: %s", err_msg)
            self.is_live = False
            self.connection_status = f"Fallback Mode: MongoDB Atlas responded with Authentication Failure ({err_msg[:60]}...)"
            self.db = MockDatabase(name=self.db_name, storage_path=self.storage_file)

    def reconnect(self, new_uri: str, db_name: Optional[str] = None) -> Tuple[bool, str]:
        """Allows dynamically reconnecting with an updated URI."""
        target_db = db_name or self.db_name
        try:
            test_client = MongoClient(new_uri, serverSelectionTimeoutMS=3000)
            test_client.admin.command("ping")
            self.client = test_client
            self.db = test_client[target_db]
            self.target_uri = new_uri
            self.db_name = target_db
            self.is_live = True
            self.last_error = None
            self.connection_status = f"Connected to Live MongoDB Atlas ({target_db})"
            return True, "Connected successfully."
        except Exception as e:
            self.last_error = str(e)
            return False, str(e)

    def get_db(self) -> Any:
        return self.db

    def get_status(self) -> dict:
        coll_counts = {}
        try:
            if self.db is not None:
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

        # Mask password in URI for safe display
        masked_uri = self.target_uri
        if "@" in masked_uri:
            prefix = masked_uri.split("@")[0]
            host = masked_uri.split("@")[1]
            if ":" in prefix:
                user_part = prefix.split(":")[0] + ":" + prefix.split(":")[1]
                masked_uri = f"{user_part}:****@{host}"

        return {
            "is_live_mongodb": self.is_live,
            "target_uri": masked_uri,
            "status": self.connection_status,
            "last_error": self.last_error,
            "collection_counts": coll_counts,
            "total_documents": sum(coll_counts.values())
        }


# Singleton accessor
_db_manager = DatabaseManager()

def get_db():
    return _db_manager.get_db()

def get_db_manager() -> DatabaseManager:
    return _db_manager
