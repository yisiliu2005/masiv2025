"""
LLM Query Processor module.
Integrates with Hugging Face API to parse natural language queries
into structured filter conditions.
"""

import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Initialize Hugging Face client with default key
api_key = os.getenv("HF_TOKEN")

client = None
if api_key:
    client = OpenAI(
        base_url="https://router.huggingface.co/v1",
        api_key=api_key,
    )

# Model to use for query interpretation
MODEL = "moonshotai/Kimi-K2-Instruct-0905"

# Valid attributes and operators for filtering
VALID_ATTRIBUTES = ["height", "land_use_designation", "assessed_value", "address", "year_of_construction"]
VALID_OPERATORS = [">", "<", "==", "contains"]


def get_client(api_key=None):
    """Get or create OpenAI client with optional override API key."""
    if api_key:
        return OpenAI(
            base_url="https://router.huggingface.co/v1",
            api_key=api_key,
        )
    return client


def parse_query(user_query, api_key=None):
    """
    Use LLM to parse a natural language query into a structured filter.
    
    Args:
        user_query (str): Natural language query from the user
        api_key (str): Optional Hugging Face API key override
    
    Returns:
        dict: Parsed filter with keys: attribute, operator, value
        Returns None if parsing fails or query is invalid
    """
    
    llm_client = get_client(api_key)
    if not llm_client:
        raise ValueError("No Hugging Face API key available. Provide HF_TOKEN in .env or pass api_key parameter.")
    
    prompt = f"""Extract filter conditions from this user query: '{user_query}'
Return ONLY a valid JSON object (no extra text) with these fields:
- attribute: one of [height, land_use_designation, assessed_value, address, year_of_construction]
- operator: one of ['>', '<', '==', 'contains']
- value: the filter value

IMPORTANT CONVERSION RULES:
- If user mentions feet/ft: convert to meters (1 foot = 0.3048 meters)
- If user mentions dollars/$ or "million": convert to number (e.g., "$1 million" → 1000000)
- For year/date filters: use year_of_construction attribute
- For zoning/building type filters: use land_use_designation with 'contains' operator

CALGARY LAND USE CODE MAPPINGS (use exact prefixes to avoid overlap):
- "residential" or "house" → "R-" (matches R-CG, R-MH)
- "multi-residential" or "apartment" or "condo" → "M-" (matches M-1, M-2, M-C1, M-C2, M-CG, M-G, M-H1, M-H2, M-H3, M-X1, M-X2)
- "commercial" or "retail" or "shopping" → "C-C" or "C-N" or "C-O" or "C-R" or "C-COR" (NOT "CC-" which is downtown)
- "industrial" or "factory" or "warehouse" → "I-" (matches I-B, I-C, I-E, I-G, I-H, I-O, I-R)
- "office" or "business park" → "C-O" or "I-B"
- "downtown" or "centre city" or "CC" → "CC-" (matches CC-COR, CC-MH, CC-MHX, CC-X, CC-E)
- "mixed use" → "MU-"
- "park" or "school" or "special purpose" → "S-"

Examples:
- "buildings over 100 feet" → {{"attribute": "height", "operator": ">", "value": 30.48}}
- "buildings built after 2010" → {{"attribute": "year_of_construction", "operator": ">", "value": 2010}}
- "buildings worth more than $1 million" → {{"attribute": "assessed_value", "operator": ">", "value": 1000000}}
- "commercial buildings" → {{"attribute": "land_use_designation", "operator": "contains", "value": "C-C"}}
- "residential buildings" → {{"attribute": "land_use_designation", "operator": "contains", "value": "R-"}}
- "apartment buildings" → {{"attribute": "land_use_designation", "operator": "contains", "value": "M-"}}
- "industrial buildings" → {{"attribute": "land_use_designation", "operator": "contains", "value": "I-"}}
- "downtown buildings" → {{"attribute": "land_use_designation", "operator": "contains", "value": "CC-"}}
- "office buildings" → {{"attribute": "land_use_designation", "operator": "contains", "value": "C-O"}}

User query: {user_query}
Response JSON:"""
    
    try:
        completion = llm_client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
        )
        
        response_text = completion.choices[0].message.content
        print(f"LLM Response: {response_text}")
        
        # Parse the JSON response
        filter_dict = json.loads(response_text)
        
        # Validate the parsed filter
        if not validate_filter(filter_dict):
            return None
        
        # Convert value types as needed
        filter_dict = normalize_filter_values(filter_dict)
        
        return filter_dict
        
    except json.JSONDecodeError as e:
        print(f"Failed to parse LLM response as JSON: {e}")
        return None
    except Exception as e:
        print(f"Error calling LLM API: {e}")
        return None


def validate_filter(filter_dict):
    """
    Validate that a parsed filter has all required fields and valid values.
    
    Args:
        filter_dict (dict): Filter dictionary to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    if not isinstance(filter_dict, dict):
        print("Filter must be a dictionary")
        return False
    
    # Check required fields
    if "attribute" not in filter_dict:
        print("Filter missing 'attribute' field")
        return False
    
    if "operator" not in filter_dict:
        print("Filter missing 'operator' field")
        return False
    
    if "value" not in filter_dict:
        print("Filter missing 'value' field")
        return False
    
    # Validate attribute
    if filter_dict["attribute"] not in VALID_ATTRIBUTES:
        print(f"Invalid attribute: {filter_dict['attribute']}")
        return False
    
    # Validate operator
    if filter_dict["operator"] not in VALID_OPERATORS:
        print(f"Invalid operator: {filter_dict['operator']}")
        return False
    
    return True


def normalize_filter_values(filter_dict):
    """
    Convert filter values to appropriate types based on the attribute.
    
    Args:
        filter_dict (dict): Filter dictionary with values to normalize
    
    Returns:
        dict: Filter with normalized values
    """
    numeric_attributes = ["height", "assessed_value", "year_of_construction"]
    
    if filter_dict["attribute"] in numeric_attributes:
        try:
            filter_dict["value"] = float(filter_dict["value"])
        except (ValueError, TypeError):
            print(f"Could not convert value to number: {filter_dict['value']}")
            return None
    
    return filter_dict


def apply_filter(buildings, filter_dict):
    """
    Apply a filter to a list of buildings.
    
    Args:
        buildings (list): List of building dictionaries
        filter_dict (dict): Filter to apply (from parse_query)
    
    Returns:
        list: List of building IDs that match the filter
    """
    if not filter_dict:
        return []
    
    matching_ids = []
    attribute = filter_dict["attribute"]
    operator = filter_dict["operator"]
    value = filter_dict["value"]
    
    print(f"Applying filter: {attribute} {operator} {value}")
    
    for building in buildings:
        try:
            building_value = building.get(attribute)
            
            if building_value is None:
                continue
            
            matches = False
            
            if operator == ">":
                matches = float(building_value) > float(value)
            elif operator == "<":
                matches = float(building_value) < float(value)
            elif operator == "==":
                matches = str(building_value).lower() == str(value).lower()
            elif operator == "contains":
                # For string containment, convert both to lowercase
                if isinstance(building_value, str):
                    matches = str(value).lower() in building_value.lower()
            
            if matches:
                matching_ids.append(building["id"])
        except Exception as e:
            print(f"Error processing building {building.get('id')}: {e}")
            continue
    
    print(f"Filter matched {len(matching_ids)} buildings")
    return matching_ids


def process_query(user_query, buildings, api_key=None):
    """
    Process a user query end-to-end: parse with LLM, apply filter, return results.
    
    Args:
        user_query (str): Natural language query from the user
        buildings (list): List of building dictionaries to filter
        api_key (str): Optional Hugging Face API key override
    
    Returns:
        dict: Result with keys: matching_ids, filter_parsed, error (if any)
    """
    # Parse the query with LLM
    filter_dict = parse_query(user_query, api_key)
    
    if not filter_dict:
        return {
            "matching_ids": [],
            "filter_parsed": None,
            "error": "Failed to parse query with LLM"
        }
    
    # Apply filter to buildings
    matching_ids = apply_filter(buildings, filter_dict)
    
    return {
        "matching_ids": matching_ids,
        "filter_parsed": filter_dict,
        "error": None
    }
