from fastapi import APIRouter, File, UploadFile, HTTPException
import boto3
import os
import uuid
from botocore.exceptions import NoCredentialsError, ClientError
from botocore.config import Config

router = APIRouter()

# Read Environment Variables
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "livelens-images")
AWS_REGION = os.getenv("AWS_REGION", "us-east-2")

# Initialize S3 Client (only used if not local)
s3_client = boto3.client(
    's3', 
    region_name=AWS_REGION,
    config=Config(
        s3={'addressing_style': 'virtual'},
        signature_version='s3v4'
    )
)

@router.get("/presigned-url")
def generate_s3_presigned_url(filename: str, review_id: str, pic_num: int, content_type: str):
    """
    Generate a pre-signed URL for the frontend to upload an image directly to S3.

    - filename: Original name (e.g., "my_photo.jpg"). We only extract the extension.
    - review_id: The UUID of the review this image belongs to.
    - pic_num: Sequence number for multiple uploads (e.g., 1, 2, 3).
    - content_type: The MIME type of the file. 
        - Common values: `image/jpeg`, `image/png`, `image/webp`
        - Tip: In JS, get this from `file.type`.
    """

    file_extension = filename.split(".")[-1]
    unique_filename = f"{review_id}_{pic_num}.{file_extension}"
    
    try:
        presigned_post = s3_client.generate_presigned_post(
            Bucket=S3_BUCKET_NAME,
            Key=f"reviews/{unique_filename}",   ### TODO: change here 
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