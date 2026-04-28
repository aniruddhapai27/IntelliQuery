import os
import logging
from typing import Optional
from groq import Groq, APIError

logger = logging.getLogger(__name__)

# Primary Groq LLM model
GROQ_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"


def get_groq_client() -> Optional[Groq]:
    """Get Groq client with API key from environment."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        logger.error("GROQ_API_KEY not set in environment")
        return None
    return Groq(api_key=api_key)


async def generate_with_groq(
    prompt: str,
    query_type: str,
    schema_context: str
) -> Optional[str]:
    """
    Generate query using Groq LLM.
    
    Args:
        prompt: The user's natural language query
        query_type: One of 'sql', 'mongo', 'pandas'
        schema_context: Schema information for the datasource
        
    Returns:
        Generated query string or None if failed
    """
    client = get_groq_client()
    if not client:
        return None
    
    system_prompts = {
        "sql": """You are an expert SQL query generator. Given a natural language question and database schema, 
generate ONLY a valid SELECT SQL query. Do not include any explanations, just the raw SQL query.
IMPORTANT: Only generate READ-ONLY queries (SELECT). Never generate INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, or any other modifying queries.
Return ONLY the SQL query, nothing else.""",
        
        "mongo": """You are an expert MongoDB query generator. Given a natural language question and collection schema,
generate a valid MongoDB query in JSON format.

IMPORTANT:
- Only generate READ-ONLY queries (find, aggregate, count, distinct)
- Never generate insert, update, delete, drop, or any modifying operations
- Return pure JSON only, no explanation

SUPPORTED FORMATS:
For aggregate: {"aggregate": [{"$group": {...}}, {"$sort": {...}}]}
For find: {"find": {...}, "projection": {...}, "sort": {...}, "limit": 10}
For count: {"count": {...}}
For distinct: {"distinct": "field_name", "filter": {...}}

Return ONLY the MongoDB query as a JSON object.""",
        
        "pandas": """You are an expert Pandas code generator. Given a natural language question and DataFrame columns,
generate ONLY valid Pandas code to query the data. Assume the DataFrame is named 'df'.
IMPORTANT: Only generate READ-ONLY operations. Never generate operations that modify the original DataFrame.
Return ONLY the Pandas code, nothing else. The code should return a DataFrame or Series."""
    }
    
    system_prompt = system_prompts.get(query_type, system_prompts["sql"])
    
    user_message = f"""Schema/Columns:
{schema_context}

Natural Language Query: {prompt}

Generate the {query_type.upper()} query:"""

    try:
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.1,
            max_completion_tokens=1024,
            top_p=0.9,
            stream=False
        )
        
        if completion.choices and len(completion.choices) > 0:
            return completion.choices[0].message.content.strip()
        return None
        
    except APIError as e:
        logger.error(f"Groq API error: {e}")
        return None
    except Exception as e:
        logger.error(f"Groq request failed: {e}")
        return None


async def generate_with_groq_streaming(
    prompt: str,
    query_type: str,
    schema_context: str
):
    """
    Generate query using Groq with streaming (for future use).
    
    Yields chunks of the response as they come in.
    """
    client = get_groq_client()
    if not client:
        return
    
    system_prompts = {
        "sql": "You are an expert SQL query generator. Generate ONLY valid SELECT queries.",
        "mongo": "You are an expert MongoDB query generator. Generate ONLY valid read queries.",
        "pandas": "You are an expert Pandas code generator. Generate ONLY read operations."
    }
    
    try:
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompts.get(query_type, "")},
                {"role": "user", "content": f"Schema: {schema_context}\n\nQuery: {prompt}"}
            ],
            temperature=0.1,
            max_completion_tokens=1024,
            top_p=0.9,
            stream=True
        )
        
        for chunk in completion:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
                
    except Exception as e:
        logger.error(f"Groq streaming failed: {e}")


async def classify_query_relevance(natural_query: str) -> dict:
    """
    Classify whether a user query is a data-analytical question.
    Returns {"is_relevant": bool, "reason": str}.
    Non-analytical questions (greetings, opinions, coding help, etc.) are rejected.
    """
    client = get_groq_client()
    if not client:
        # If we can't classify, allow the query through
        return {"is_relevant": True, "reason": ""}

    system_prompt = """You are a strict query classifier for a data analytics platform.
Your job is to decide whether a user's question is a DATA-ANALYTICAL question that can be answered by querying a database, collection, or DataFrame.

DATA-ANALYTICAL questions include:
- Questions about counts, sums, averages, min/max of data
- Filtering, searching, or looking up records
- Aggregations, groupings, rankings, trends
- Comparisons between data fields or time periods
- Any question that requires reading data from a database/table/collection/file

NON-ANALYTICAL questions include:
- Greetings ("hi", "hello", "how are you")
- General knowledge ("what is Python?", "who is the president?")
- Opinions or advice ("should I use SQL or NoSQL?")
- Coding help ("how to write a for loop?")
- Math problems unrelated to data ("what is 2+2?")
- Anything that does NOT require querying a data source

Respond with ONLY a JSON object (no markdown, no explanation):
{"is_relevant": true/false, "reason": "brief reason if not relevant"}"""

    try:
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"User question: \"{natural_query}\""}
            ],
            temperature=0.0,
            max_completion_tokens=150,
            top_p=1.0,
            stream=False
        )

        if completion.choices and len(completion.choices) > 0:
            import json
            raw = completion.choices[0].message.content.strip()
            # Strip markdown fences if present
            raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            result = json.loads(raw)
            return {
                "is_relevant": bool(result.get("is_relevant", True)),
                "reason": result.get("reason", "")
            }

    except Exception as e:
        logger.warning(f"Query relevance classification failed: {e}")

    # Default: allow through on failure
    return {"is_relevant": True, "reason": ""}


async def refine_query_with_groq(
    original_query: str,
    generated_query: str,
    error_message: str,
    query_type: str,
    schema_context: str
) -> Optional[str]:
    """
    Ask the LLM to refine/fix a generated query based on an error.

    Args:
        original_query: The user's natural language question
        generated_query: The previously generated query that failed
        error_message: The validation or execution error
        query_type: One of 'sql', 'mongo', 'pandas'
        schema_context: Schema information for the datasource

    Returns:
        Refined query string or None if failed
    """
    client = get_groq_client()
    if not client:
        return None

    system_prompts = {
        "sql": """You are an expert SQL query debugger and generator.
You will be given a SQL query that failed along with the error. Fix the query.
Rules:
- ONLY output a valid SELECT SQL query
- No explanations, no markdown, just the raw SQL query
- Ensure correctness against the provided schema""",
        "mongo": """You are an expert MongoDB query debugger and generator.
You will be given a MongoDB query that failed along with the error. Fix the query.
Rules:
- ONLY output a valid read-only MongoDB query as a JSON object
- No explanations, no markdown, just the raw JSON
- Supported formats: {"aggregate": [...]}, {"find": {...}}, {"count": {...}}, {"distinct": ...}""",
        "pandas": """You are an expert Pandas code debugger and generator.
You will be given Pandas code that failed along with the error. Fix the code.
Rules:
- ONLY output valid read-only Pandas code (no inplace modifications)
- Assume DataFrame is named 'df'
- No explanations, no markdown, just the raw code"""
    }

    system_prompt = system_prompts.get(query_type, system_prompts["sql"])

    user_message = f"""Schema/Columns:
{schema_context}

Original question: "{original_query}"

Previously generated {query_type.upper()} query:
{generated_query}

Error encountered:
{error_message}

Please generate a corrected {query_type.upper()} query:"""

    try:
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.15,
            max_completion_tokens=1024,
            top_p=0.9,
            stream=False
        )

        if completion.choices and len(completion.choices) > 0:
            return completion.choices[0].message.content.strip()
        return None

    except APIError as e:
        logger.error(f"Groq refinement API error: {e}")
        return None
    except Exception as e:
        logger.error(f"Groq refinement request failed: {e}")
        return None


async def get_groq_completion(prompt: str, temperature: float = 0.3) -> str:
    """
    Get a general completion from Groq LLM.
    Used for tasks like visualization suggestions and data analysis.
    
    Args:
        prompt: The prompt to send to Groq
        temperature: Sampling temperature (0-1)
        
    Returns:
        Completion text from Groq
    """
    client = get_groq_client()
    if not client:
        raise Exception("Groq client not available. Check GROQ_API_KEY environment variable.")
    
    try:
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_completion_tokens=2048,
            top_p=0.95,
            stream=False
        )
        
        if completion.choices and len(completion.choices) > 0:
            return completion.choices[0].message.content.strip()
        
        raise Exception("No response from Groq")
        
    except APIError as e:
        logger.error(f"Groq API error: {e}")
        raise Exception(f"Groq API error: {str(e)}")
    except Exception as e:
        logger.error(f"Groq request failed: {e}")
        raise Exception(f"Failed to get Groq completion: {str(e)}")


async def validate_query_with_llm(
    natural_query: str,
    generated_query: str,
    query_type: str,
    schema_context: str
) -> dict:
    """
    Use an LLM as a secondary validator to check if the generated query correctly answers the user's natural language query.
    Returns: {"is_valid": bool, "confidence": float, "feedback": str}
    """
    client = get_groq_client()
    if not client:
        return {"is_valid": True, "confidence": 1.0, "feedback": ""}

    validator_model = "llama-3.3-70b-versatile"  # Use a stronger model for validation

    system_prompt = f"""You are an expert {query_type.upper()} query validator for a data platform.
Given a natural language query, a database/collection schema, and a generated {query_type.upper()} query or code, your task is to validate if the generated query correctly, safely, and optimally answers the user's natural language query using the provided schema.

Consider:
- Does the query use the correct tables/collections and columns/fields?
- Is the logic correct for the requested aggregation, filtering, or sorting?
- Are JOINs correct and complete?
- Are there syntax errors or hallucinations of columns that don't exist?

Respond with ONLY a JSON object (no markdown formatting, no code blocks) with the exact structure:
{{
    "is_valid": true,
    "confidence": 0.95,
    "feedback": "Your detailed feedback on what is wrong and how to fix it. Empty if perfectly valid."
}}
Ensure 'is_valid' is a boolean, 'confidence' is a float between 0.0 and 1.0, and 'feedback' is a string. If confidence is below 0.8 or is_valid is false, you must provide feedback."""

    user_message = f"""Schema/Columns:
{schema_context}

Natural Language Query: {natural_query}

Generated {query_type.upper()} Query / Code:
{generated_query}

Validate the query and return ONLY the JSON representation:"""

    try:
        completion = client.chat.completions.create(
            model=validator_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.0,
            max_completion_tokens=500,
            top_p=1.0,
            stream=False
        )

        if completion.choices and len(completion.choices) > 0:
            import json
            raw = completion.choices[0].message.content.strip()
            # Clean possible markdown formatting
            raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            
            result = json.loads(raw)
            return {
                "is_valid": bool(result.get("is_valid", True)),
                "confidence": float(result.get("confidence", 1.0)),
                "feedback": str(result.get("feedback", ""))
            }
            
    except Exception as e:
        logger.warning(f"LLM validation failed, skipping validator check: {e}")

    # Fallback if the validation fails
    return {"is_valid": True, "confidence": 1.0, "feedback": ""}

