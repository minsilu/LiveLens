import os
import json
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Any, Dict, Union, Optional

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

@router.post("/analyze")
async def analyze_data(request: AnalyzeRequest):
    """
    Endpoint to analyze text or JSON data using Zhipu GLM-4 API.
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
        response = client.chat.completions.create(
            model="glm-4",
            messages=[
                {"role": "system", "content": instruction_text},
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.7,
            timeout=60,
        )
        
        # Return the generated text
        return {
            "status": "success",
            "analysis": response.choices[0].message.content
        }
    except Exception as e:
         raise HTTPException(status_code=500, detail=f"Failed to analyze data with ZhipuAI: {str(e)}")
