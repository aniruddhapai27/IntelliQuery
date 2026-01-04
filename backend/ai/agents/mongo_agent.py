import re
import json
from typing import Any, Dict, List, Tuple
import logging

from pymongo import MongoClient
from pymongo.errors import PyMongoError
from bson import json_util, ObjectId

from ai.agents.base import BaseAgent

logger = logging.getLogger(__name__)

# Forbidden MongoDB operations
FORBIDDEN_MONGO_OPERATIONS = [
    'insert', 'insertone', 'insertmany',
    'update', 'updateone', 'updatemany',
    'delete', 'deleteone', 'deletemany',
    'drop', 'dropcollection', 'dropdatabase',
    'create', 'createcollection', 'createindex',
    'remove', 'save', 'replace', 'replaceone',
    'findoneandupdate', 'findoneandreplace', 'findoneanddelete',
    'bulkwrite', 'rename'
]


class MongoAgent(BaseAgent):
    """
    MongoDB Agent for handling MongoDB queries.
    Uses qwen-text2mongo:latest via Ollama, with Groq fallback.
    """
    
    def __init__(self):
        super().__init__("mongo")
    
    def _get_client(self, datasource: Dict[str, Any]) -> MongoClient:
        """Get MongoDB client from datasource details."""
        details = datasource.get("details", {})
        uri = details.get("uri", "mongodb://localhost:27017")
        return MongoClient(uri, serverSelectionTimeoutMS=5000)
    
    async def get_schema_context(self, datasource: Dict[str, Any]) -> str:
        """
        Extract MongoDB collection schema by sampling documents.
        """
        try:
            details = datasource.get("details", {})
            database = details.get("database", "")
            
            client = self._get_client(datasource)
            db = client[database]
            
            schema_parts = []
            collections = db.list_collection_names()[:10]  # Limit to 10 collections
            
            for collection_name in collections:
                collection = db[collection_name]
                
                # Sample a few documents to infer schema
                sample_docs = list(collection.find().limit(3))
                
                if sample_docs:
                    # Extract field names and types from samples
                    fields = {}
                    for doc in sample_docs:
                        for key, value in doc.items():
                            if key not in fields:
                                fields[key] = type(value).__name__
                    
                    fields_str = "\n".join([f"  - {k}: {v}" for k, v in fields.items()])
                    doc_count = collection.estimated_document_count()
                    
                    schema_parts.append(
                        f"Collection: {collection_name}\n"
                        f"Estimated documents: {doc_count}\n"
                        f"Fields:\n{fields_str}"
                    )
            
            client.close()
            return "\n\n".join(schema_parts) if schema_parts else "No collections found"
            
        except Exception as e:
            logger.error(f"Error extracting MongoDB schema: {e}")
            return "Error extracting schema"
    
    def validate_readonly(self, generated_query: str) -> Tuple[bool, str]:
        """
        Validate that the MongoDB query is read-only.
        """
        query_lower = generated_query.lower()
        
        # Check for forbidden operations
        for op in FORBIDDEN_MONGO_OPERATIONS:
            # Check for operation as method call or in JSON
            if re.search(rf'["\']?{op}["\']?\s*[:(]', query_lower):
                return False, f"Forbidden operation detected: {op}"
            if re.search(rf'\.{op}\s*\(', query_lower):
                return False, f"Forbidden method detected: {op}"
        
        # Try to parse as JSON and check operation
        try:
            query_json = json.loads(generated_query)
            operation = query_json.get("operation", "").lower()
            
            if operation not in ["find", "aggregate", "count", "distinct"]:
                return False, f"Only find, aggregate, count, and distinct operations are allowed"
            
        except json.JSONDecodeError:
            # If not JSON, check if it looks like a safe query
            pass
        
        return True, ""
    
    def _parse_query(self, generated_query: str) -> Dict[str, Any]:
        """Parse the generated query into a structured format."""
        try:
            # Try to parse as JSON first
            return json.loads(generated_query)
        except json.JSONDecodeError:
            pass
        
        # Try to extract JSON from the response
        json_match = re.search(r'\{[\s\S]*\}', generated_query)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # Default to a simple find
        return {"operation": "find", "filter": {}}
    
    async def execute_query(self, query: str, datasource: Dict[str, Any]) -> Tuple[bool, Any]:
        """
        Execute the MongoDB query and return results.
        """
        try:
            details = datasource.get("details", {})
            database = details.get("database", "")
            collection_name = details.get("collection", "")
            
            client = self._get_client(datasource)
            db = client[database]
            
            query_obj = self._parse_query(query)
            operation = query_obj.get("operation", "find").lower()
            
            # Get collection name from query or datasource
            coll_name = query_obj.get("collection", collection_name)
            if not coll_name:
                # Try to infer from query or use first collection
                collections = db.list_collection_names()
                if collections:
                    coll_name = collections[0]
                else:
                    return False, "No collection specified or found"
            
            collection = db[coll_name]
            
            if operation == "find":
                filter_query = query_obj.get("filter", {})
                projection = query_obj.get("projection", None)
                sort = query_obj.get("sort", None)
                limit = query_obj.get("limit", 100)  # Default limit
                
                cursor = collection.find(filter_query, projection)
                if sort:
                    sort_list = [(k, v) for k, v in sort.items()]
                    cursor = cursor.sort(sort_list)
                cursor = cursor.limit(limit if limit else 100)
                
                results = list(cursor)
                
            elif operation == "aggregate":
                pipeline = query_obj.get("pipeline", [])
                # Add a limit stage if not present
                has_limit = any(stage.get("$limit") for stage in pipeline)
                if not has_limit:
                    pipeline.append({"$limit": 100})
                
                results = list(collection.aggregate(pipeline))
                
            elif operation == "count":
                filter_query = query_obj.get("filter", {})
                count = collection.count_documents(filter_query)
                results = [{"count": count}]
                
            elif operation == "distinct":
                field = query_obj.get("field", "_id")
                filter_query = query_obj.get("filter", {})
                distinct_values = collection.distinct(field, filter_query)
                results = [{"distinct_values": distinct_values, "count": len(distinct_values)}]
                
            else:
                return False, f"Unsupported operation: {operation}"
            
            client.close()
            
            # Convert BSON types to JSON serializable
            data = json.loads(json_util.dumps(results))
            
            # Extract columns from first document
            columns = list(data[0].keys()) if data else []
            
            return True, {
                "data": data,
                "columns": columns,
                "row_count": len(data)
            }
            
        except PyMongoError as e:
            logger.error(f"MongoDB execution error: {e}")
            return False, str(e)
        except Exception as e:
            logger.error(f"Unexpected error executing MongoDB query: {e}")
            return False, str(e)
    
    async def get_collections_info(self, datasource: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get list of collections with their field information."""
        try:
            details = datasource.get("details", {})
            database = details.get("database", "")
            
            client = self._get_client(datasource)
            db = client[database]
            
            collections = []
            for coll_name in db.list_collection_names():
                collection = db[coll_name]
                sample = collection.find_one()
                fields = list(sample.keys()) if sample else []
                doc_count = collection.estimated_document_count()
                
                collections.append({
                    "name": coll_name,
                    "fields": fields,
                    "document_count": doc_count
                })
            
            client.close()
            return collections
            
        except Exception as e:
            logger.error(f"Error getting collections info: {e}")
            return []
