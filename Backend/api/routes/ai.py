import os
import json
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Any, Dict, Union, Optional
from sqlalchemy import text
from ..database import engine

try:
    from zhipuai import ZhipuAI
except ImportError:
    ZhipuAI = None

router = APIRouter()

class AnalyzeRequest(BaseModel):
    # We accept either a plain string or a JSON object/list
    input_data: Union[str, Dict[str, Any], list]
    # Optional system prompt or extra instructions
    instructions: Optional[str] = None

def fetch_top_venues(limit: int = 5):
    if not engine:
        return json.dumps({"error": "Database not configured."})
    query = """
        SELECT v.name, v.city, AVG(r.overall_rating) as avg_rating, COUNT(r.id) as review_count
        FROM Venues v
        JOIN Reviews r ON v.id = r.venue_id
        GROUP BY v.id, v.name, v.city
        ORDER BY avg_rating DESC
        LIMIT :limit
    """
    with engine.connect() as conn:
        result = conn.execute(text(query), {"limit": limit})
        venues = [dict(row._mapping) for row in result]
    return json.dumps(venues, default=str)

def fetch_venue_stats(venue_name: str):
    if not engine:
        return json.dumps({"error": "Database not configured."})
    query = """
        SELECT v.name, v.city, v.capacity,
               AVG(r.overall_rating) as avg_overall,
               AVG(r.rating_visual) as avg_visual,
               AVG(r.rating_sound) as avg_sound,
               AVG(r.rating_value) as avg_value,
               COUNT(r.id) as review_count
        FROM Venues v
        LEFT JOIN Reviews r ON v.id = r.venue_id
        WHERE v.name ILIKE :venue_name
        GROUP BY v.id, v.name, v.city, v.capacity
        LIMIT 5
    """
    with engine.connect() as conn:
        result = conn.execute(text(query), {"venue_name": f"%{venue_name}%"})
        venues = [dict(row._mapping) for row in result]
    if not venues:
        return json.dumps({"error": f"No venue found matching '{venue_name}'."})
    return json.dumps(venues, default=str)

def fetch_seat_stats(venue_name: str, section: str, row: str, seat_number: str):
    if not engine:
        return json.dumps({"error": "Database not configured."})
    query = """
        SELECT v.name as venue_name, s.section, s.row, s.seat_number,
               sa.avg_overall, sa.avg_visual, sa.avg_sound, sa.avg_value, sa.review_count
        FROM Venues v
        JOIN Seats s ON v.id = s.venue_id
        LEFT JOIN SeatAggregates sa ON s.id = sa.seat_id
        WHERE v.name ILIKE :venue_name 
          AND s.section ILIKE :section 
          AND s.row ILIKE :row 
          AND s.seat_number ILIKE :seat_number
        LIMIT 1
    """
    with engine.connect() as conn:
        result = conn.execute(text(query), {
            "venue_name": f"%{venue_name}%",
            "section": section,
            "row": row,
            "seat_number": seat_number
        })
        seat = result.fetchone()
        if not seat:
            return json.dumps({"error": "Seat not found in the specified venue."})
        return json.dumps(dict(seat._mapping), default=str)

TOOL_FUNCTIONS = {
    "get_top_venues": fetch_top_venues,
    "get_venue_stats": fetch_venue_stats,
    "get_seat_stats": fetch_seat_stats
}

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_top_venues",
            "description": "Get the top highest-rated venues from the database based on user reviews.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Number of top venues to return. Default is 5."}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_venue_stats",
            "description": "Get average ratings and basic information for a specific venue by name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "venue_name": {"type": "string", "description": "The name of the venue to search for."}
                },
                "required": ["venue_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_seat_stats",
            "description": "Get the average rating statistics for a specific seat in a specific venue.",
            "parameters": {
                "type": "object",
                "properties": {
                    "venue_name": {"type": "string", "description": "The name of the venue."},
                    "section": {"type": "string", "description": "The section name or number of the seat."},
                    "row": {"type": "string", "description": "The row name or number of the seat."},
                    "seat_number": {"type": "string", "description": "The specific seat."}
                },
                "required": ["venue_name", "section", "row", "seat_number"]
            }
        }
    }
]

@router.post("/analyze")
async def analyze_data(request: AnalyzeRequest):
    """
    Endpoint to analyze text or JSON data using Zhipu GLM-4 API with Database Function Calling.
    
    This endpoint allows the AI to answer general queries or automatically fetch real-time 
    venue, event, or seat rating statistics from the database before answering.
    
    Expected Input Payload (JSON):
    {
        "input_data": "string" | { ... } | [ ... ],  // Required. The question or data to analyze.
        "instructions": "string"                     // Optional. Extra system prompt instructions.
    }
    
    Expected Output Response (JSON):
    {
        "status": "success",
        "analysis": "string"  // The final natural language response from the AI.
    }
    
    Example Request:
    POST /analyze
    {
        "input_data": "What is the highest rated venue in the system?"
    }
    """
    zhipu_api_key = os.getenv("ZHIPUAI_API_KEY")
    if not zhipu_api_key:
        raise HTTPException(status_code=500, detail="ZHIPUAI_API_KEY is not configured in the environment.")
    
    if ZhipuAI is None:
        raise HTTPException(status_code=500, detail="ZhipuAI library is not installed.")
        
    try:
        # Initialize ZhipuAI client
        client = ZhipuAI(api_key=zhipu_api_key)
        
        # Format the input data
        formatted_input = ""
        if isinstance(request.input_data, str):
            formatted_input = request.input_data
        else:
            # Convert JSON objects/lists to string representation
            formatted_input = json.dumps(request.input_data, indent=2)
            
        # Construct the final prompt
        instruction_text = (
             "You are an AI assistant analyzing data for the LiveLens application. "
             "Analyze the user's needs or the following input data and provide a detailed, "
             "helpful response based on the provided context."
        )
        
        if request.instructions:
            instruction_text += f"\nExtra instructions from user: {request.instructions}"
            
        full_prompt = f"Input Data to Analyze:\n{formatted_input}"
        
        # Generate the response using Zhipu GLM-4 model
        messages = [
            {"role": "system", "content": instruction_text},
            {"role": "user", "content": full_prompt}
        ]
        
        response = client.chat.completions.create(
            model="glm-4",
            messages=messages,
            tools=TOOLS_SCHEMA,
            temperature=0.7,
            timeout=60,
        )
        
        response_message = response.choices[0].message
        
        # Check if the model wants to call a function
        if response_message.tool_calls:
            assistant_msg = {
                "role": "assistant",
                "content": response_message.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    } for tc in response_message.tool_calls
                ]
            }
            messages.append(assistant_msg)
            
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_to_call = TOOL_FUNCTIONS.get(function_name)
                
                if function_to_call:
                    try:
                        function_args = json.loads(tool_call.function.arguments)
                        function_response = function_to_call(**function_args)
                    except Exception as func_e:
                        function_response = json.dumps({"error": str(func_e)})
                else:
                    function_response = json.dumps({"error": f"Function {function_name} not found."})
                
                messages.append(
                    {
                        "role": "tool",
                        "content": function_response,
                        "tool_call_id": tool_call.id,
                    }
                )
            
            # Send the updated conversation back to the model
            second_response = client.chat.completions.create(
                model="glm-4",
                messages=messages,
                tools=TOOLS_SCHEMA,
                temperature=0.7,
                timeout=60,
            )
            final_content = second_response.choices[0].message.content
        else:
            final_content = response_message.content
        
        # Return the generated text
        return {
            "status": "success",
            "analysis": final_content
        }
    except Exception as e:
         raise HTTPException(status_code=500, detail=f"Failed to analyze data with ZhipuAI: {str(e)}")
