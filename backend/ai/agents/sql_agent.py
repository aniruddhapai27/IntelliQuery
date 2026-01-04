import re
from typing import Any, Dict, List, Tuple
import logging

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError

from ai.agents.base import BaseAgent
from datasources.store import decrypt_password

logger = logging.getLogger(__name__)

# Forbidden SQL keywords for write operations
FORBIDDEN_SQL_KEYWORDS = [
    r'\bINSERT\b',
    r'\bUPDATE\b',
    r'\bDELETE\b',
    r'\bDROP\b',
    r'\bCREATE\b',
    r'\bALTER\b',
    r'\bTRUNCATE\b',
    r'\bGRANT\b',
    r'\bREVOKE\b',
    r'\bEXEC\b',
    r'\bEXECUTE\b',
    r'\bMERGE\b',
    r'\bREPLACE\b',
    r'\bCALL\b',
]


class SQLAgent(BaseAgent):
    """
    SQL Agent for handling MySQL and PostgreSQL queries.
    Uses qwen-text2sql:latest via Ollama, with Groq fallback.
    """
    
    def __init__(self):
        super().__init__("sql")
    
    def _build_connection_url(self, datasource: Dict[str, Any]) -> str:
        """Build SQLAlchemy connection URL from datasource details."""
        details = datasource.get("details", {})
        db_type = datasource.get("type", "mysql")
        
        host = details.get("host", "localhost")
        port = details.get("port", 3306 if db_type == "mysql" else 5432)
        username = details.get("username", "")
        password = details.get("password", "")
        database = details.get("database", "")
        
        if db_type == "mysql":
            return f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}"
        else:  # PostgreSQL
            return f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}"
    
    async def get_schema_context(self, datasource: Dict[str, Any]) -> str:
        """
        Extract database schema including tables, columns, and sample data.
        """
        try:
            db_url = self._build_connection_url(datasource)
            engine = create_engine(db_url)
            inspector = inspect(engine)
            
            schema_parts = []
            tables = inspector.get_table_names()
            
            for table_name in tables[:10]:  # Limit to 10 tables to avoid context overflow
                columns_info = inspector.get_columns(table_name)
                pk_info = inspector.get_pk_constraint(table_name)
                fk_info = inspector.get_foreign_keys(table_name)
                
                columns_str = []
                for col in columns_info:
                    col_str = f"  - {col['name']} ({str(col['type'])})"
                    if col['name'] in (pk_info.get('constrained_columns', [])):
                        col_str += " [PRIMARY KEY]"
                    columns_str.append(col_str)
                
                fk_str = ""
                if fk_info:
                    fk_refs = [f"  FK: {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}" for fk in fk_info]
                    fk_str = "\n" + "\n".join(fk_refs)
                
                schema_parts.append(f"Table: {table_name}\nColumns:\n" + "\n".join(columns_str) + fk_str)
            
            engine.dispose()
            return "\n\n".join(schema_parts)
            
        except Exception as e:
            logger.error(f"Error extracting SQL schema: {e}")
            return "Error extracting schema"
    
    def validate_readonly(self, generated_query: str) -> Tuple[bool, str]:
        """
        Validate that the SQL query is read-only (SELECT only).
        """
        query_upper = generated_query.upper().strip()
        
        # Must start with SELECT or WITH (for CTEs)
        if not (query_upper.startswith('SELECT') or query_upper.startswith('WITH')):
            return False, "Query must start with SELECT or WITH"
        
        # Check for forbidden keywords
        for pattern in FORBIDDEN_SQL_KEYWORDS:
            if re.search(pattern, query_upper):
                keyword = pattern.replace(r'\b', '').strip()
                return False, f"Forbidden keyword detected: {keyword}"
        
        # Check for semicolon followed by another statement (SQL injection prevention)
        statements = [s.strip() for s in generated_query.split(';') if s.strip()]
        if len(statements) > 1:
            return False, "Multiple statements not allowed"
        
        return True, ""
    
    async def execute_query(self, query: str, datasource: Dict[str, Any]) -> Tuple[bool, Any]:
        """
        Execute the SQL query and return results.
        """
        try:
            db_url = self._build_connection_url(datasource)
            engine = create_engine(db_url)
            
            with engine.connect() as connection:
                result = connection.execute(text(query))
                
                # Fetch all rows
                rows = result.fetchall()
                columns = list(result.keys())
                
                # Convert to list of dicts
                data = [dict(zip(columns, row)) for row in rows]
                
                # Convert any non-serializable types
                for row in data:
                    for key, value in row.items():
                        if hasattr(value, 'isoformat'):  # datetime objects
                            row[key] = value.isoformat()
                        elif isinstance(value, bytes):
                            row[key] = value.decode('utf-8', errors='ignore')
                
            engine.dispose()
            
            return True, {
                "data": data,
                "columns": columns,
                "row_count": len(data)
            }
            
        except SQLAlchemyError as e:
            logger.error(f"SQL execution error: {e}")
            return False, str(e)
        except Exception as e:
            logger.error(f"Unexpected error executing SQL: {e}")
            return False, str(e)
    
    async def get_tables_info(self, datasource: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get list of tables with their column information."""
        try:
            db_url = self._build_connection_url(datasource)
            engine = create_engine(db_url)
            inspector = inspect(engine)
            
            tables = []
            for table_name in inspector.get_table_names():
                columns = inspector.get_columns(table_name)
                tables.append({
                    "name": table_name,
                    "columns": [{"name": c["name"], "type": str(c["type"])} for c in columns]
                })
            
            engine.dispose()
            return tables
            
        except Exception as e:
            logger.error(f"Error getting tables info: {e}")
            return []
