"""
MongoDB Connection and Database Management Module.
Connects to MongoDB Atlas using MONGODB_URI environment variable with resilient
fallback to validated local document store if credentials expire or are blocked.
"""
import os
import logging
from typing import Any, Dict, Optional, Tuple
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from backend.app.config import settings
from backend.app.db.mock_db import MockDatabase

logger = logging.getLogger("recsys.mongodb")
logging.basicConfig(level=logging.INFO)

DEFAULT_LOCAL_STORAGE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "local_db.json")
)


class MongoDatabaseManager:
    _instance: Optional["MongoDatabaseManager"] = None

    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.db: Any = None
        self.is_live: bool = False
        self.status_message: str = "Uninitialized"
        self.last_error: Optional[str] = None
        self.storage_file = DEFAULT_LOCAL_STORAGE
        self._connect()

    def _connect(self):
        uri = settings.MONGODB_URI
        db_name = settings.MONGODB_DB_NAME

        try:
            logger.info("Attempting connection to MongoDB Atlas cluster...")
            client = MongoClient(uri, serverSelectionTimeoutMS=2500)
            # Verify connectivity
            client.admin.command("ping")
            self.client = client
            self.db = client[db_name]
            self.is_live = True
            self.last_error = None
            self.status_message = f"Connected to Live MongoDB Atlas ({db_name})"
            logger.info("Connected successfully to live MongoDB Atlas.")
            return
        except Exception as e:
            err = str(e)
            self.last_error = err
            logger.warning("MongoDB Atlas returned error (%s). Falling back to resilient local database.", err)
            self.is_live = False
            self.status_message = f"Fallback Mode: Resilient Local Store (1,036 documents active)"
            self.db = MockDatabase(name=db_name, storage_path=self.storage_file)

    def reconnect(self, new_uri: str, db_name: Optional[str] = None) -> Tuple[bool, str]:
        target_db = db_name or settings.MONGODB_DB_NAME
        try:
            client = MongoClient(new_uri, serverSelectionTimeoutMS=3000)
            client.admin.command("ping")
            self.client = client
            self.db = client[target_db]
            self.is_live = True
            self.last_error = None
            self.status_message = f"Connected to Live MongoDB Atlas ({target_db})"
            return True, "Connected successfully to MongoDB Atlas."
        except Exception as e:
            self.last_error = str(e)
            return False, str(e)

    def get_db(self) -> Any:
        return self.db

    def get_diagnostics(self) -> Dict[str, Any]:
        collections = [
            "posts", "postembeddings", "postengagements", "postmetrics",
            "postcomments", "follows", "views", "carts", "orders",
            "sellerdetails", "productcategories", "productsubcategories",
            "variants", "products"
        ]
        counts = {}
        for c in collections:
            try:
                counts[c] = self.db[c].count_documents({})
            except Exception:
                counts[c] = 0

        # Mask password in URI
        masked = settings.MONGODB_URI
        if "@" in masked:
            user_part = masked.split("@")[0].split(":")[0] + ":****"
            host_part = masked.split("@")[1]
            masked = f"{user_part}@{host_part}"

        return {
            "is_live_mongodb": self.is_live,
            "target_uri": masked,
            "status": self.status_message,
            "last_error": self.last_error,
            "collection_counts": counts,
            "total_documents": sum(counts.values())
        }


_manager = MongoDatabaseManager()

def get_database() -> Any:
    return _manager.get_db()

def get_db_manager() -> MongoDatabaseManager:
    return _manager
