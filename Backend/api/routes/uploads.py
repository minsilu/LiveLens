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

@router.post("/local")
async def upload_local_image(file: UploadFile = File(...)):
    """
    Local Development Only: Physically accept the file bytes and save to local disk.
    This simulates the S3 upload process so developers can test the frontend locally.
    """
    if not USE_LOCAL_STORAGE:
        raise HTTPException(status_code=403, detail="Local storage is disabled. Use /upload/presigned-url instead.")
        
    file_extension = file.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    
    os.makedirs("static/images", exist_ok=True)
    file_location = f"static/images/{unique_filename}"
    
    with open(file_location, "wb+") as file_object:
        file_object.write(await file.read())
        
    return {"url": f"http://127.0.0.1:8000/static/images/{unique_filename}", "method": "local"}

@router.get("/presigned-url")
def generate_s3_presigned_url(filename: str, content_type: str):
    """
    Production S3 Flow: Generates a temporary, secure "upload ticket" (Pre-signed URL).
    The backend NEVER touches the file bytes. It just hands this ticket to the Frontend via GET,
    and the Frontend makes a POST directly to Amazon S3.
    """
    if USE_LOCAL_STORAGE:
        raise HTTPException(status_code=400, detail="Running in local mode. Use POST /upload/local instead.")
        
    file_extension = filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    
    try:
        presigned_post = s3_client.generate_presigned_post(
            Bucket=S3_BUCKET_NAME,
            Key=f"reviews/{unique_filename}",
            Fields={"acl": "public-read", "Content-Type": content_type},
            Conditions=[
                {"acl": "public-read"},
                {"Content-Type": content_type},
                ["content-length-range", 1, 10485760] # Max 10MB
            ],
            ExpiresIn=3600
        )
        
        final_image_url = f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/reviews/{unique_filename}"
        
        return {
            "upload_instructions": presigned_post,
            "future_url": final_image_url,
            "method": "s3_presigned"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not generate S3 presigned URL: {str(e)}")
