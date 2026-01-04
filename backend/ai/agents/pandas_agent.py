import re
import ast
from typing import Any, Dict, List, Tuple
import logging
import pandas as pd

from ai.agents.base import BaseAgent

logger = logging.getLogger(__name__)

# Forbidden Pandas operations and Python constructs
FORBIDDEN_PATTERNS = [
    r'\.to_sql\s*\(',
    r'\.to_csv\s*\(',
    r'\.to_excel\s*\(',
    r'\.to_json\s*\(',
    r'\.to_pickle\s*\(',
    r'\.to_parquet\s*\(',
    r'\.to_hdf\s*\(',
    r'\.to_feather\s*\(',
    r'\bopen\s*\(',
    r'\bexec\s*\(',
    r'\beval\s*\(',  # We'll use a safe eval instead
    r'\bimport\s+',
    r'\bfrom\s+\w+\s+import',
    r'\b__\w+__\b',  # Dunder methods
    r'\bos\.',
    r'\bsys\.',
    r'\bsubprocess\.',
    r'\bshutil\.',
    r'\brequests\.',
    r'\burllib\.',
    r'\.drop\s*\(',
    r'\.drop_duplicates\s*\([^)]*inplace\s*=\s*True',
    r'\.fillna\s*\([^)]*inplace\s*=\s*True',
    r'\.replace\s*\([^)]*inplace\s*=\s*True',
    r'\.rename\s*\([^)]*inplace\s*=\s*True',
    r'\.reset_index\s*\([^)]*inplace\s*=\s*True',
    r'\.set_index\s*\([^)]*inplace\s*=\s*True',
    r'\.sort_values\s*\([^)]*inplace\s*=\s*True',
    r'\.sort_index\s*\([^)]*inplace\s*=\s*True',
    r'\bdel\s+',
    r'\.pop\s*\(',
    r'\.insert\s*\(',
    r'\[.*\]\s*=',  # Assignment to slice/index
]

# Allowed safe builtins for eval
SAFE_BUILTINS = {
    'True': True,
    'False': False,
    'None': None,
    'len': len,
    'str': str,
    'int': int,
    'float': float,
    'bool': bool,
    'list': list,
    'dict': dict,
    'tuple': tuple,
    'sum': sum,
    'min': min,
    'max': max,
    'abs': abs,
    'round': round,
    'sorted': sorted,
    'reversed': reversed,
    'enumerate': enumerate,
    'zip': zip,
    'map': map,
    'filter': filter,
    'range': range,
}


class PandasAgent(BaseAgent):
    """
    Pandas Agent for handling CSV/Excel file queries.
    Uses qwen-text2pandas:latest via Ollama, with Groq fallback.
    """
    
    def __init__(self):
        super().__init__("pandas")
    
    def _load_dataframe(self, datasource: Dict[str, Any]) -> pd.DataFrame:
        """Load DataFrame from file path in datasource."""
        details = datasource.get("details", {})
        file_path = details.get("path", "")
        filename = details.get("filename", "")
        
        if file_path.endswith('.csv') or filename.endswith('.csv'):
            return pd.read_csv(file_path)
        elif file_path.endswith(('.xlsx', '.xls')) or filename.endswith(('.xlsx', '.xls')):
            return pd.read_excel(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_path}")
    
    async def get_schema_context(self, datasource: Dict[str, Any]) -> str:
        """
        Extract DataFrame schema including columns, dtypes, and sample data.
        """
        try:
            df = self._load_dataframe(datasource)
            
            # Get column info
            columns_info = []
            for col in df.columns:
                dtype = str(df[col].dtype)
                non_null = df[col].count()
                unique = df[col].nunique()
                columns_info.append(f"  - {col} (type: {dtype}, non-null: {non_null}, unique: {unique})")
            
            # Get sample values for context
            sample_values = {}
            for col in df.columns[:10]:  # Limit columns for sample
                sample = df[col].dropna().head(3).tolist()
                sample_values[col] = sample
            
            schema = f"""DataFrame Info:
- Total rows: {len(df)}
- Total columns: {len(df.columns)}

Columns:
{chr(10).join(columns_info)}

Sample values:
{chr(10).join([f'  {k}: {v}' for k, v in sample_values.items()])}"""
            
            return schema
            
        except Exception as e:
            logger.error(f"Error extracting Pandas schema: {e}")
            return "Error extracting schema"
    
    def validate_readonly(self, generated_query: str) -> Tuple[bool, str]:
        """
        Validate that the Pandas code is read-only and safe.
        """
        # Check for forbidden patterns
        for pattern in FORBIDDEN_PATTERNS:
            if re.search(pattern, generated_query, re.IGNORECASE):
                return False, f"Forbidden pattern detected: {pattern}"
        
        # Try to parse as valid Python
        try:
            ast.parse(generated_query)
        except SyntaxError as e:
            return False, f"Invalid Python syntax: {e}"
        
        # Check for assignments that modify df directly
        if re.search(r'^df\s*=', generated_query, re.MULTILINE):
            # Allow df = df.something() patterns
            if not re.search(r'^df\s*=\s*df\.', generated_query, re.MULTILINE):
                return False, "Direct DataFrame reassignment not allowed"
        
        return True, ""
    
    def _safe_eval(self, code: str, df: pd.DataFrame) -> Any:
        """
        Safely evaluate Pandas code with restricted namespace.
        """
        # Create a restricted namespace
        namespace = {
            'df': df,
            'pd': pd,
            **SAFE_BUILTINS
        }
        
        # For simple expressions, use eval
        # For statements, we need exec but with restrictions
        try:
            # Try eval first (for expressions)
            result = eval(code, {"__builtins__": SAFE_BUILTINS}, namespace)
            return result
        except SyntaxError:
            # If it's not an expression, try exec
            local_ns = namespace.copy()
            exec(code, {"__builtins__": SAFE_BUILTINS}, local_ns)
            
            # Look for result variable or return the last df operation
            if 'result' in local_ns:
                return local_ns['result']
            elif 'df' in local_ns and local_ns['df'] is not df:
                return local_ns['df']
            else:
                return None
    
    async def execute_query(self, query: str, datasource: Dict[str, Any]) -> Tuple[bool, Any]:
        """
        Execute the Pandas code and return results.
        """
        try:
            df = self._load_dataframe(datasource)
            
            # Clean the query
            clean_query = query.strip()
            
            # Execute safely
            result = self._safe_eval(clean_query, df)
            
            # Convert result to serializable format
            if isinstance(result, pd.DataFrame):
                data = result.head(1000).to_dict(orient='records')  # Limit rows
                columns = list(result.columns)
                row_count = len(result)
            elif isinstance(result, pd.Series):
                data = result.head(1000).to_frame().to_dict(orient='records')
                columns = [result.name or 'value']
                row_count = len(result)
            elif isinstance(result, (int, float, str, bool)):
                data = [{"result": result}]
                columns = ["result"]
                row_count = 1
            elif isinstance(result, dict):
                data = [result]
                columns = list(result.keys())
                row_count = 1
            elif isinstance(result, list):
                if result and isinstance(result[0], dict):
                    data = result[:1000]
                    columns = list(result[0].keys()) if result else []
                else:
                    data = [{"value": v} for v in result[:1000]]
                    columns = ["value"]
                row_count = len(result)
            else:
                data = [{"result": str(result)}]
                columns = ["result"]
                row_count = 1
            
            # Convert any non-serializable types
            for row in data:
                for key, value in row.items():
                    if hasattr(value, 'isoformat'):
                        row[key] = value.isoformat()
                    elif pd.isna(value):
                        row[key] = None
                    elif hasattr(value, 'item'):  # numpy types
                        row[key] = value.item()
            
            return True, {
                "data": data,
                "columns": columns,
                "row_count": row_count
            }
            
        except Exception as e:
            logger.error(f"Pandas execution error: {e}")
            return False, str(e)
    
    async def get_dataframe_info(self, datasource: Dict[str, Any]) -> Dict[str, Any]:
        """Get DataFrame information including columns and basic stats."""
        try:
            df = self._load_dataframe(datasource)
            
            columns = []
            for col in df.columns:
                col_info = {
                    "name": col,
                    "dtype": str(df[col].dtype),
                    "non_null_count": int(df[col].count()),
                    "unique_count": int(df[col].nunique())
                }
                
                # Add stats for numeric columns
                if df[col].dtype in ['int64', 'float64']:
                    col_info["min"] = float(df[col].min()) if not pd.isna(df[col].min()) else None
                    col_info["max"] = float(df[col].max()) if not pd.isna(df[col].max()) else None
                    col_info["mean"] = float(df[col].mean()) if not pd.isna(df[col].mean()) else None
                
                columns.append(col_info)
            
            return {
                "filename": datasource.get("details", {}).get("filename", ""),
                "rows": len(df),
                "columns": columns
            }
            
        except Exception as e:
            logger.error(f"Error getting DataFrame info: {e}")
            return {}
