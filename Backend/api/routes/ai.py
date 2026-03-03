import os
import json
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Any, Dict, Union, Optional
import google.generativeai as genai

# Try to get the API key from environment
gemini_api_key = os.getenv("GEMINI_API_KEY")

if gemini_api_key:
    genai.configure(api_key=gemini_api_key)

router = APIRouter()

class AnalyzeRequest(BaseModel):
    # We accept either a plain string or a JSON object/list
    input_data: Union[str, Dict[str, Any], list]
    # Optional system prompt or extra instructions
    instructions: Optional[str] = None

@router.post("/analyze")
async def analyze_data(request: AnalyzeRequest):
    """
    Endpoint to analyze text or JSON data using Gemini API.
    """
    if not gemini_api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not configured in the environment.")
    
    try:
        # Determine the model to use. flash is usually the best for general fast analysis.
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Format the input data
        formatted_input = ""
        if isinstance(request.input_data, str):
            formatted_input = request.input_data
        else:
            # Convert JSON objects/lists to string representation
            formatted_input = json.dumps(request.input_data, indent=2)
            
        # Construct the final prompt
        system_instruction = (
             "You are an AI assistant analyzing data for the LiveLens application. "
             "Analyze the user's needs or the following input data and provide a detailed, "
             "helpful response based on the provided context."
        )
        
        if request.instructions:
            system_instruction += f"\nExtra instructions from user: {request.instructions}"
            
        full_prompt = f"{system_instruction}\n\nInput Data to Analyze:\n{formatted_input}"
        
        # Generate the response
        response = model.generate_content(full_prompt)
        
        # Return the generated text
        return {
            "status": "success",
            "analysis": response.text
        }
    except Exception as e:
         raise HTTPException(status_code=500, detail=f"Failed to analyze data with Gemini: {str(e)}")
