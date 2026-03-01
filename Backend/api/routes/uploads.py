from fastapi import APIRouter, File, UploadFile, HTTPException
import boto3
import os
import uuid
from botocore.exceptions import NoCredentialsError, ClientError

router = APIRouter()

# Read Environment Variables
USE_LOCAL_STORAGE = os.getenv("USE_LOCAL_STORAGE", "False").lower() in ("true", "1", "t")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "livelens-uploads")
AWS_REGION = os.getenv("AWS_REGION", "us-east-2")

# Initialize S3 Client (only used if not local)
s3_client = boto3.client('s3', region_name=AWS_REGION) if not USE_LOCAL_STORAGE else None

@router.post("/image")
async def upload_image(file: UploadFile = File(...)):
    """
    Hybrid Image Upload Endpoint:
    - If USE_LOCAL_STORAGE=True (Local Dev): Saves the file to Backend/static/images/ and returns a local URL.
    - If USE_LOCAL_STORAGE=False (AWS Prod): Generates an S3 Pre-signed URL so the frontend can upload directly, saving bandwidth.
      (In a pure production flow, we would return just the presigned URL without taking the file bytes, but for maximum compatibility with swagger testing, 
      this endpoint also accepts the file and pushes it to S3 if needed, or returns the presigned URL for frontend direct-upload).
    """
    file_extension = file.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    
    if USE_LOCAL_STORAGE:
        # --- Local File System Mock ---
        os.makedirs("static/images", exist_ok=True)
        file_location = f"static/images/{unique_filename}"
        
        with open(file_location, "wb+") as file_object:
            file_object.write(await file.read())
            
        # Return a relative path that FastAPI StaticFiles can serve
        return {"url": f"http://127.0.0.1:8000/static/images/{unique_filename}", "method": "local"}
        
    else:
        # --- AWS S3 Production ---
        # 1. We can generate a presigned URL for the frontend to upload directly
        try:
            presigned_post = s3_client.generate_presigned_post(
                Bucket=S3_BUCKET_NAME,
                Key=f"reviews/{unique_filename}",
                Fields={"acl": "public-read", "Content-Type": file.content_type},
                Conditions=[
                    {"acl": "public-read"},
                    {"Content-Type": file.content_type},
                    ["content-length-range", 1, 10485760] # Max 10MB
                ],
                ExpiresIn=3600
            )
            
            # The final URL where the image will live after frontend uploads it
            final_image_url = f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/reviews/{unique_filename}"
            
            return {
                "upload_instructions": presigned_post,
                "future_url": final_image_url,
                "method": "s3_presigned"
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Could not generate S3 presigned URL: {str(e)}")
