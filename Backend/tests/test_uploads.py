from fastapi.testclient import TestClient
from api.main import app
import os
import io

client = TestClient(app)

def test_local_image_upload(monkeypatch):
    """
    Test the hybrid image upload endpoint with USE_LOCAL_STORAGE=True.
    This simulates a local developer uploading a dummy image to the /static/images/ folder.
    """
    # Force the app to believe it's running locally by patching the module variable directly
    import api.routes.uploads as uploads_module
    monkeypatch.setattr(uploads_module, "USE_LOCAL_STORAGE", True)
    
    # Create a 1x1 pixel fake image in memory
    fake_image_bytes = b"fake_image_content"
    fake_file = io.BytesIO(fake_image_bytes)
    
    # The key 'file' matches the `UploadFile = File(...)` parameter in uploads.py
    files = {"file": ("test_concert.jpg", fake_file, "image/jpeg")}
    
    response = client.post("/upload/local?review_id=test-review-123&pic_num=1", files=files)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["method"] == "local"
    assert "url" in data
    assert data["url"].startswith("http://127.0.0.1:8000/static/images/")
    assert data["url"].endswith(".jpg")
    
    # Cleanup: Extract the filename from the URL and delete the generated static file
    filename = data["url"].split("/")[-1]
    filepath = f"Backend/static/images/{filename}"
    if os.path.exists(filepath):
        os.remove(filepath)

def test_s3_presigned_url_generation(monkeypatch):
    """
    Test the hybrid image upload endpoint with USE_LOCAL_STORAGE=False.
    This simulates the production AWS flow where the backend must return an S3 presigned URL.
    Note: We mock the boto3 client so we don't actually hit AWS during unit tests.
    """
    import api.routes.uploads as uploads_module
    monkeypatch.setattr(uploads_module, "USE_LOCAL_STORAGE", False)
    monkeypatch.setattr(uploads_module, "S3_BUCKET_NAME", "test-bucket")
    monkeypatch.setattr(uploads_module, "AWS_REGION", "us-east-1")
    
    # Mocking boto3 client generation to prevent 'NoCredentialsError' in pure offline CI/CD
    class MockS3Client:
        def generate_presigned_post(self, **kwargs):
            return {"url": "https://s3.amazonaws.com/test-bucket", "fields": {"key": "value"}}

    # Patch the s3_client instance in the uploads module
    import api.routes.uploads as uploads_module
    monkeypatch.setattr(uploads_module, "s3_client", MockS3Client())

    response = client.get("/upload/presigned-url?filename=s3_test.png&review_id=test-review-456&pic_num=2&content_type=image/png")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["method"] == "s3_presigned"
    assert "upload_instructions" in data
    assert "future_url" in data
    assert data["future_url"].startswith("https://test-bucket.s3.us-east-1.amazonaws.com/reviews/")
    assert data["future_url"].endswith(".png")
