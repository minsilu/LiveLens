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

def fetch_venue_review_stats(venue_name: str):
    if not engine:
        return json.dumps({"error": "Database not configured."})
    query = """
        SELECT
            COUNT(*) as total_reviews,
            SUM(CASE WHEN overall_rating = 5 THEN 1 ELSE 0 END) as five_star,
            SUM(CASE WHEN overall_rating = 4 THEN 1 ELSE 0 END) as four_star,
            SUM(CASE WHEN overall_rating = 3 THEN 1 ELSE 0 END) as three_star,
            SUM(CASE WHEN overall_rating = 2 THEN 1 ELSE 0 END) as two_star,
            SUM(CASE WHEN overall_rating = 1 THEN 1 ELSE 0 END) as one_star
        FROM Reviews r
        JOIN Venues v ON r.venue_id = v.id
        WHERE v.name ILIKE :venue_name
    """
    with engine.connect() as conn:
        result = conn.execute(text(query), {"venue_name": f"%{venue_name}%"})
        row = result.fetchone()
        if not row:
            return json.dumps({"error": f"No reviews found for '{venue_name}'."})
        return json.dumps(dict(row._mapping), default=str)

def fetch_venue_reviews(venue_name: str, limit: int = 5, min_rating: int = None):
    if not engine:
        return json.dumps({"error": "Database not configured."})
    query = """
        SELECT r.text, r.overall_rating, r.rating_visual, r.rating_sound, r.rating_value,
               r.section, r.row, r.seat_number, r.created_at
        FROM Reviews r
        JOIN Venues v ON r.venue_id = v.id
        WHERE v.name ILIKE :venue_name
          AND r.text IS NOT NULL AND r.text != ''
          {min_rating_filter}
        ORDER BY r.overall_rating DESC
        LIMIT :limit
    """
    min_rating_filter = "AND r.overall_rating >= :min_rating" if min_rating is not None else ""
    query = query.format(min_rating_filter=min_rating_filter)
    params = {"venue_name": f"%{venue_name}%", "limit": limit}
    if min_rating is not None:
        params["min_rating"] = min_rating
    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        reviews = [dict(row._mapping) for row in result]
    if not reviews:
        return json.dumps({"error": f"No reviews found for '{venue_name}'."})
    return json.dumps(reviews, default=str)

def fetch_best_seats(venue_name: str, limit: int = 10, section: str = None):
    if not engine:
        return json.dumps({"error": "Database not configured."})
    section_filter = "AND s.section ILIKE :section" if section else ""
    query = f"""
        SELECT s.section, s.row, s.seat_number,
               sa.avg_overall, sa.avg_visual, sa.avg_sound, sa.avg_value, sa.review_count
        FROM Seats s
        JOIN Venues v ON s.venue_id = v.id
        JOIN SeatAggregates sa ON s.id = sa.seat_id
        WHERE v.name ILIKE :venue_name
          AND sa.review_count >= 1
          {section_filter}
        ORDER BY sa.avg_overall DESC, sa.review_count DESC
        LIMIT :limit
    """
    params = {"venue_name": f"%{venue_name}%", "limit": limit}
    if section:
        params["section"] = f"%{section}%"
    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        seats = [dict(row._mapping) for row in result]
    if not seats:
        return json.dumps({"error": f"No seat data found for '{venue_name}'" + (f" section {section}" if section else "") + "."})
    return json.dumps(seats, default=str)

def fetch_section_stats(venue_name: str, sort_by: str = "avg_overall"):
    if not engine:
        return json.dumps({"error": "Database not configured."})
    allowed = {"avg_overall", "avg_visual", "avg_sound", "avg_value"}
    if sort_by not in allowed:
        sort_by = "avg_overall"
    query = f"""
        SELECT s.section,
               ROUND(AVG(sa.avg_overall)::numeric, 2) as avg_overall,
               ROUND(AVG(sa.avg_visual)::numeric, 2) as avg_visual,
               ROUND(AVG(sa.avg_sound)::numeric, 2) as avg_sound,
               ROUND(AVG(sa.avg_value)::numeric, 2) as avg_value,
               SUM(sa.review_count) as total_reviews
        FROM Seats s
        JOIN Venues v ON s.venue_id = v.id
        JOIN SeatAggregates sa ON s.id = sa.seat_id
        WHERE v.name ILIKE :venue_name
          AND sa.review_count >= 1
        GROUP BY s.section
        ORDER BY {sort_by} DESC
        LIMIT 10
    """
    with engine.connect() as conn:
        result = conn.execute(text(query), {"venue_name": f"%{venue_name}%"})
        sections = [dict(row._mapping) for row in result]
    if not sections:
        return json.dumps({"error": f"No section data found for '{venue_name}'."})
    return json.dumps(sections, default=str)

def fetch_worst_seats(venue_name: str, limit: int = 5, section: str = None):
    if not engine:
        return json.dumps({"error": "Database not configured."})
    section_filter = "AND s.section ILIKE :section" if section else ""
    query = f"""
        SELECT s.section, s.row, s.seat_number,
               sa.avg_overall, sa.avg_visual, sa.avg_sound, sa.avg_value, sa.review_count
        FROM Seats s
        JOIN Venues v ON s.venue_id = v.id
        JOIN SeatAggregates sa ON s.id = sa.seat_id
        WHERE v.name ILIKE :venue_name
          AND sa.review_count >= 2
          {section_filter}
        ORDER BY sa.avg_overall ASC, sa.review_count DESC
        LIMIT :limit
    """
    params = {"venue_name": f"%{venue_name}%", "limit": limit}
    if section:
        params["section"] = f"%{section}%"
    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        seats = [dict(row._mapping) for row in result]
    if not seats:
        return json.dumps({"error": f"No seat data found for '{venue_name}'."})
    return json.dumps(seats, default=str)

def fetch_past_events(venue_name: str, limit: int = 10):
    if not engine:
        return json.dumps({"error": "Database not configured."})
    query = """
        SELECT e.name, e.artist, e.genre, e.event_date
        FROM Events e
        JOIN Venues v ON e.venue_id = v.id
        WHERE v.name ILIKE :venue_name
          AND e.event_date < CURRENT_DATE
        ORDER BY e.event_date DESC
        LIMIT :limit
    """
    with engine.connect() as conn:
        result = conn.execute(text(query), {"venue_name": f"%{venue_name}%", "limit": limit})
        events = [dict(row._mapping) for row in result]
    if not events:
        return json.dumps({"message": f"No past events found for '{venue_name}'."})
    return json.dumps(events, default=str)

def fetch_venue_events(venue_name: str):
    if not engine:
        return json.dumps({"error": "Database not configured."})
    query = """
        SELECT e.name, e.artist, e.genre, e.event_date, e.ticket_url
        FROM Events e
        JOIN Venues v ON e.venue_id = v.id
        WHERE v.name ILIKE :venue_name
          AND e.event_date >= CURRENT_DATE
        ORDER BY e.event_date ASC
        LIMIT 10
    """
    with engine.connect() as conn:
        result = conn.execute(text(query), {"venue_name": f"%{venue_name}%"})
        events = [dict(row._mapping) for row in result]
    if not events:
        return json.dumps({"message": f"No upcoming events found for '{venue_name}'."})
    return json.dumps(events, default=str)

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
    "get_seat_stats": fetch_seat_stats,
    "get_venue_review_stats": fetch_venue_review_stats,
    "get_venue_reviews": fetch_venue_reviews,
    "get_venue_events": fetch_venue_events,
    "get_best_seats": fetch_best_seats,
    "get_worst_seats": fetch_worst_seats,
    "get_section_stats": fetch_section_stats,
    "get_past_events": fetch_past_events,
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
            "name": "get_venue_review_stats",
            "description": "Get the rating distribution for a specific venue: how many 1, 2, 3, 4, and 5-star reviews it has, plus total review count.",
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
            "name": "get_venue_reviews",
            "description": "Get actual review texts and ratings for a specific venue. Use this to find the best, most detailed, or most relevant reviews.",
            "parameters": {
                "type": "object",
                "properties": {
                    "venue_name": {"type": "string", "description": "The name of the venue."},
                    "limit": {"type": "integer", "description": "Number of reviews to return. Default is 5."},
                    "min_rating": {"type": "integer", "description": "Optional minimum overall rating filter (1-5)."}
                },
                "required": ["venue_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_venue_events",
            "description": "Get upcoming events at a specific venue including event name, artist, genre, date, and ticket URL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "venue_name": {"type": "string", "description": "The name of the venue."}
                },
                "required": ["venue_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_section_stats",
            "description": "Get average ratings per section for a venue. Use this when the user asks which section has the best sound, best view, best value, or best overall experience.",
            "parameters": {
                "type": "object",
                "properties": {
                    "venue_name": {"type": "string", "description": "The name of the venue."},
                    "sort_by": {"type": "string", "description": "Rating to sort by: avg_overall, avg_visual, avg_sound, or avg_value. Default is avg_overall."}
                },
                "required": ["venue_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_worst_seats",
            "description": "Get the lowest-rated seats in a venue. Use this when the user asks which seats to avoid, worst seats, or bad seats.",
            "parameters": {
                "type": "object",
                "properties": {
                    "venue_name": {"type": "string", "description": "The name of the venue."},
                    "limit": {"type": "integer", "description": "Number of seats to return. Default is 5."},
                    "section": {"type": "string", "description": "Optional section to filter by."}
                },
                "required": ["venue_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_past_events",
            "description": "Get past events that have been held at a venue. Use this when the user asks about events that already happened, event history, or past concerts/shows.",
            "parameters": {
                "type": "object",
                "properties": {
                    "venue_name": {"type": "string", "description": "The name of the venue."},
                    "limit": {"type": "integer", "description": "Number of past events to return. Default is 10."}
                },
                "required": ["venue_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_best_seats",
            "description": "Get the top-rated seats in a venue ranked by overall rating. Use this when the user asks for the best seat, best section, or highest rated seating in a venue, optionally filtered by section.",
            "parameters": {
                "type": "object",
                "properties": {
                    "venue_name": {"type": "string", "description": "The name of the venue."},
                    "limit": {"type": "integer", "description": "Number of top seats to return. Default is 10."},
                    "section": {"type": "string", "description": "Optional section to filter by (e.g. '2', 'A', 'Floor')."}
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
            "You are a helpful venue assistant for the LiveLens application. "
            "ALWAYS call the appropriate database function(s) before answering any question about a venue. "
            "Never guess or make up ratings, reviews, or events — always fetch real data from the DB first. "
            "If the question is about ratings or stars, use get_venue_review_stats. "
            "If the question is about reviews or comments, use get_venue_reviews. "
            "If the question is about upcoming events, use get_venue_events. "
            "If the question is about general venue info or averages, use get_venue_stats. "
            "If the question is about the best seat or top seats, use get_best_seats (pass section param if user specifies a section). "
            "If the question is about seats to avoid or worst seats, use get_worst_seats. "
            "If the question is about which section has the best sound, view, or value, use get_section_stats with the appropriate sort_by. "
            "If the question is about past events or event history, use get_past_events. "
            "When presenting seat results, always show the top 3-5 options with section, row, seat number, rating, and review count. "
            "Emphasize seats with more reviews as they are more reliable. Never pick just one — give a ranked list. "
            "IMPORTANT: Never use markdown formatting. No **, no ##, no bullet points with -, no headers. Use plain text only."
        )

        if request.instructions:
            instruction_text += f"\n{request.instructions}"

        # Support structured input with question + venue context
        if isinstance(request.input_data, dict):
            question = request.input_data.get("question", "")
            venue_name = request.input_data.get("venue_name", "")
            venue_id = request.input_data.get("venue_id", "")
            context_parts = []
            if venue_name:
                context_parts.append(f"Venue: {venue_name}")
            if venue_id:
                context_parts.append(f"Venue ID: {venue_id}")
            if context_parts:
                full_prompt = f"{', '.join(context_parts)}\nQuestion: {question}"
            else:
                full_prompt = question or formatted_input
        else:
            full_prompt = formatted_input
        
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
