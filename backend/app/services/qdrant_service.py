from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import os
from pathlib import Path
from .memory_service import MemoryService

class QdrantService:
    def __init__(self):
        # Use local storage in backend directory
        self.storage_path = Path.cwd() / "qdrant_storage"
        if not self.storage_path.exists():
            self.storage_path.mkdir(parents=True, exist_ok=True)
            
        print(f"DEBUG: Qdrant Local Storage at: {self.storage_path}")
        self.client = QdrantClient(path=str(self.storage_path))
        self.collection_name = "crime_records"
        
        # Initialize memory service
        self.memory_service = MemoryService()
        
        # Ensure collection exists
        self._ensure_collection()

    def _ensure_collection(self):
        try:
            collections = self.client.get_collections()
            exists = any(c.name == self.collection_name for c in collections.collections)
            
            if not exists:
                print(f"DEBUG: Creating Qdrant collection '{self.collection_name}'...")
                # Vector size: Facenet=512
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=512, distance=Distance.COSINE),
                )
                print("DEBUG: Collection created.")
            
            # Create payload index on original_index for fast sorted retrieval
            try:
                from qdrant_client.models import PayloadSchemaType
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="original_index",
                    field_schema=PayloadSchemaType.INTEGER
                )
                print("DEBUG: Created index on original_index field")
            except Exception as e:
                # Index might already exist
                print(f"DEBUG: Payload index note: {e}")
                
        except Exception as e:
            print(f"Error ensuring collection: {e}")

    def search_similar(self, vector: list, limit: int = 5):
        """
        Search for similar vectors in Qdrant.
        """
        try:
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=vector,
                limit=limit
            )
            return results
        except Exception as e:
            print(f"Qdrant search error: {e}")
            return []

    def insert_record(self, vector: list, metadata: dict):
        """
        Insert a new record with memory metadata initialization.
        """
        try:
            import uuid
            # Use deterministic ID if filename provided, else random
            if "filename" in metadata:
                 # simple hash to uuid
                 point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, metadata["filename"]))
            else:
                 point_id = str(uuid.uuid4())
            
            # Initialize memory metadata
            metadata = self.memory_service.initialize_metadata(metadata)
            
            point = PointStruct(
                id=point_id,
                vector=vector,
                payload=metadata
            )
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            return point_id
        except Exception as e:
            print(f"Insert error: {e}")
            return None

    def index_count(self):
        try:
             info = self.client.get_collection(self.collection_name)
             return info.points_count
        except:
             return 0

    def get_record(self, point_id: str, update_access: bool = True):
        """Get a single record by ID and optionally update access metadata"""
        try:
            result = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[point_id]
            )
            
            if result and len(result) > 0 and update_access:
                # Update access metadata
                record = result[0]
                updated_metadata = self.memory_service.update_access_metadata(record.payload)
                self.update_record(point_id, updated_metadata)
                record.payload = updated_metadata
                return record
            
            return result[0] if result else None
        except Exception as e:
            print(f"Get record error: {e}")
            return None

    def update_record(self, point_id: str, metadata: dict):
        """Update record metadata (keeps vector unchanged)"""
        try:
            self.client.set_payload(
                collection_name=self.collection_name,
                payload=metadata,
                points=[point_id]
            )
            return True
        except Exception as e:
            print(f"Update error: {e}")
            return False

    def delete_record(self, point_id: str):
        """Delete a record by ID"""
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=[point_id]
            )
            return True
        except Exception as e:
            print(f"Delete error: {e}")
            return False

    def delete_multiple(self, point_ids: list):
        """Delete multiple records"""
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=point_ids
            )
            return True
        except Exception as e:
            print(f"Bulk delete error: {e}")
            return False

    def list_records(self, limit: int = 100, offset: int = 0):
        """List records with pagination - O(log n) with indexed original_index"""
        try:
            from qdrant_client.models import OrderBy, Direction
            
            # Use scroll with order_by for efficient sorted retrieval
            # This uses the payload index on original_index
            result = self.client.scroll(
                collection_name=self.collection_name,
                limit=limit,
                offset=offset,
                with_payload=True,
                with_vectors=False,
                order_by=OrderBy(
                    key="original_index",
                    direction=Direction.ASC
                )
            )
            
            return result[0] if result else []
        except Exception as e:
            print(f"List error: {e}")
            # Fallback to unordered if order_by not supported
            try:
                result = self.client.scroll(
                    collection_name=self.collection_name,
                    limit=limit,
                    with_payload=True,
                    with_vectors=False
                )
                records = result[0] if result else []
                records.sort(key=lambda x: x.payload.get('original_index', 999999))
                return records[offset:offset + limit]
            except:
                return []

    def search_by_filters(self, crime_type: str = None, limit: int = 100):
        """Search records by metadata filters"""
        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            
            filters = None
            if crime_type:
                filters = Filter(
                    must=[
                        FieldCondition(
                            key="crime_type",
                            match=MatchValue(value=crime_type)
                        )
                    ]
                )
            
            result = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=filters,
                limit=limit,
                with_payload=True,
                with_vectors=False
            )
            return result[0] if result else []
        except Exception as e:
            print(f"Filter search error: {e}")
            return []

    def get_stats(self):
        """Get collection statistics"""
        try:
            info = self.client.get_collection(self.collection_name)
            
            # Just return basic stats without loading all records
            # Crime distribution can be calculated on-demand if needed
            return {
                "total_records": info.points_count,
                "vector_size": info.config.params.vectors.size,
                "crime_distribution": {}  # Empty for now to avoid performance issues
            }
        except Exception as e:
            print(f"Stats error: {e}")
            return {"total_records": 0, "crime_distribution": {}}

