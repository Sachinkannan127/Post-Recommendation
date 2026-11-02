"""
In-memory and file-backed MongoDB collection emulator for seamless development,
testing, and fallback when remote MongoDB Atlas is unreachable or unauthenticated.
Implements the essential PyMongo Collection and Database interfaces.
"""
import copy
import json
import os
import re
from typing import Any, Dict, List, Optional, Union
from bson import ObjectId


def _match_condition(field_val: Any, cond_val: Any) -> bool:
    if isinstance(cond_val, dict):
        for op, val in cond_val.items():
            if op == "$eq":
                if field_val != val:
                    return False
            elif op == "$ne":
                if field_val == val:
                    return False
            elif op == "$in":
                if field_val not in val:
                    return False
            elif op == "$nin":
                if field_val in val:
                    return False
            elif op == "$gt":
                if field_val is None or not (field_val > val):
                    return False
            elif op == "$gte":
                if field_val is None or not (field_val >= val):
                    return False
            elif op == "$lt":
                if field_val is None or not (field_val < val):
                    return False
            elif op == "$lte":
                if field_val is None or not (field_val <= val):
                    return False
            elif op == "$exists":
                if (field_val is not None) != val:
                    return False
            elif op == "$regex":
                if not isinstance(field_val, str) or not re.search(val, field_val, re.IGNORECASE):
                    return False
        return True
    return field_val == cond_val


def _matches_filter(doc: Dict[str, Any], query: Dict[str, Any]) -> bool:
    if not query:
        return True
    
    for k, v in query.items():
        if k == "$or":
            if not any(_matches_filter(doc, subq) for subq in v):
                return False
        elif k == "$and":
            if not all(_matches_filter(doc, subq) for subq in v):
                return False
        else:
            # Handle nested key access like "a.b"
            curr = doc
            keys = k.split(".")
            found = True
            for part in keys:
                if isinstance(curr, dict) and part in curr:
                    curr = curr[part]
                else:
                    curr = None
                    found = False
                    break
            
            if not _match_condition(curr if found else None, v):
                return False
    return True


class MockCursor:
    def __init__(self, docs: List[Dict[str, Any]]):
        self._docs = copy.deepcopy(docs)
        self._limit = None
        self._skip = 0

    def sort(self, key_or_list: Union[str, List[tuple]], direction: int = 1):
        if isinstance(key_or_list, str):
            sort_keys = [(key_or_list, direction)]
        else:
            sort_keys = key_or_list

        def sort_key_func(doc):
            vals = []
            for k, d in sort_keys:
                v = doc.get(k)
                if v is None:
                    vals.append((0, 0.0))
                elif isinstance(v, (int, float)):
                    vals.append((1, float(v)))
                else:
                    vals.append((2, str(v)))
            return tuple(vals)

        # Apply primary sort direction
        reverse = sort_keys[0][1] == -1 if sort_keys else False
        self._docs.sort(key=sort_key_func, reverse=reverse)
        return self

    def skip(self, count: int):
        self._skip = count
        return self

    def limit(self, count: int):
        self._limit = count
        return self

    def __iter__(self):
        start = self._skip
        end = (start + self._limit) if self._limit is not None else None
        for doc in self._docs[start:end]:
            yield copy.deepcopy(doc)

    def to_list(self, length: Optional[int] = None) -> List[Dict[str, Any]]:
        start = self._skip
        max_items = length if length is not None else self._limit
        end = (start + max_items) if max_items is not None else None
        return copy.deepcopy(self._docs[start:end])


class MockCollection:
    def __init__(self, name: str, data: Optional[List[Dict[str, Any]]] = None):
        self.name = name
        self._docs: List[Dict[str, Any]] = copy.deepcopy(data) if data else []

    def find(self, filter: Optional[Dict[str, Any]] = None, projection: Optional[Dict[str, Any]] = None) -> MockCursor:
        filter = filter or {}
        matches = [d for d in self._docs if _matches_filter(d, filter)]
        if projection:
            include_fields = {k for k, v in projection.items() if v and k != "_id"}
            exclude_fields = {k for k, v in projection.items() if not v}
            filtered = []
            for d in matches:
                item = {}
                if include_fields:
                    for k in include_fields:
                        if k in d:
                            item[k] = d[k]
                    if projection.get("_id", 1):
                        item["_id"] = d.get("_id")
                elif exclude_fields:
                    item = {k: v for k, v in d.items() if k not in exclude_fields}
                else:
                    item = d
                filtered.append(item)
            return MockCursor(filtered)
        return MockCursor(matches)

    def find_one(self, filter: Optional[Dict[str, Any]] = None, projection: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        cursor = self.find(filter, projection)
        results = cursor.to_list(1)
        return results[0] if results else None

    def insert_one(self, document: Dict[str, Any]):
        doc = copy.deepcopy(document)
        if "_id" not in doc:
            doc["_id"] = str(ObjectId())
        self._docs.append(doc)
        return type("InsertOneResult", (), {"inserted_id": doc["_id"]})()

    def insert_many(self, documents: List[Dict[str, Any]]):
        inserted_ids = []
        for document in documents:
            res = self.insert_one(document)
            inserted_ids.append(res.inserted_id)
        return type("InsertManyResult", (), {"inserted_ids": inserted_ids})()

    def update_one(self, filter: Dict[str, Any], update: Dict[str, Any], upsert: bool = False):
        matched = False
        for doc in self._docs:
            if _matches_filter(doc, filter):
                matched = True
                if "$set" in update:
                    for k, v in update["$set"].items():
                        doc[k] = copy.deepcopy(v)
                if "$inc" in update:
                    for k, v in update["$inc"].items():
                        doc[k] = doc.get(k, 0) + v
                break
        
        if not matched and upsert:
            new_doc = copy.deepcopy(filter)
            if "$set" in update:
                new_doc.update(update["$set"])
            if "_id" not in new_doc:
                new_doc["_id"] = str(ObjectId())
            self._docs.append(new_doc)
            return type("UpdateResult", (), {"matched_count": 0, "modified_count": 1, "upserted_id": new_doc["_id"]})()

        return type("UpdateResult", (), {"matched_count": 1 if matched else 0, "modified_count": 1 if matched else 0})()

    def count_documents(self, filter: Optional[Dict[str, Any]] = None) -> int:
        filter = filter or {}
        return sum(1 for d in self._docs if _matches_filter(d, filter))

    def distinct(self, key: str, filter: Optional[Dict[str, Any]] = None) -> List[Any]:
        filter = filter or {}
        seen = set()
        out = []
        for d in self._docs:
            if _matches_filter(d, filter) and key in d:
                val = d[key]
                if isinstance(val, (str, int, float, bool)):
                    if val not in seen:
                        seen.add(val)
                        out.append(val)
                else:
                    out.append(val)
        return out

    def delete_many(self, filter: Optional[Dict[str, Any]] = None):
        filter = filter or {}
        orig_len = len(self._docs)
        self._docs = [d for d in self._docs if not _matches_filter(d, filter)]
        return type("DeleteResult", (), {"deleted_count": orig_len - len(self._docs)})()


class MockDatabase:
    """Emulates a PyMongo Database with dynamic collection access."""
    def __init__(self, name: str = "social_commerce_db", storage_path: Optional[str] = None):
        self.name = name
        self.storage_path = storage_path
        self._collections: Dict[str, MockCollection] = {}
        if storage_path and os.path.exists(storage_path):
            self.load_from_disk(storage_path)

    def __getitem__(self, item: str) -> MockCollection:
        if item not in self._collections:
            self._collections[item] = MockCollection(item)
        return self._collections[item]

    def __getattr__(self, item: str) -> MockCollection:
        return self[item]

    def list_collection_names(self) -> List[str]:
        return list(self._collections.keys())

    def save_to_disk(self, file_path: Optional[str] = None):
        target = file_path or self.storage_path
        if not target:
            return
        payload = {}
        for coll_name, coll in self._collections.items():
            payload[coll_name] = coll._docs
        with open(target, "w", encoding="utf-8") as f:
            json.dump(payload, f, default=str, indent=2)

    def load_from_disk(self, file_path: str):
        if not os.path.exists(file_path):
            return
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            for coll_name, docs in data.items():
                self._collections[coll_name] = MockCollection(coll_name, docs)
