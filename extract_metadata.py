
import logging
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import os
from PIL import Image
from io import BytesIO
from abilities import upload_file_to_storage
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

class ImageMetaData(BaseModel):
    format: str
    mode: str
    size: tuple
    info: dict

def extract_image_metadata(image_bytes):
    with Image.open(image_bytes) as img:
        metadata = ImageMetaData(
            format=img.format,
            mode=img.mode,
            size=img.size,
            info=img.info
        )
    return metadata

@app.post("/upload_image", summary="Upload Image", description="Endpoint to upload an image and extract metadata.")
async def upload_image(file: UploadFile = File(...)):
    if not file.content_type.startswith('image/'):
        logger.error("Uploaded file is not an image")
        raise HTTPException(status_code=400, detail="File is not an image.")

    try:
        # Read the image file
        image_bytes = await file.read()
        metadata = extract_image_metadata(BytesIO(image_bytes))
        metadata_dict = metadata.dict()
        image_metadata = json.dumps(metadata_dict, indent=4)
        return {"message": "Image metadata extraction completed", "image_metadata": image_metadata}

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="Failed to process the image file.")

@app.get("/", response_class=HTMLResponse, summary="Main Page", description="Serves the main page with the file upload form.")
def main_page():
    content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Image Metadata Extractor</title>
        <style>
            /* Styles for the page */
            body { font-family: Arial, sans-serif; margin: 0; padding: 0; background: #f7f7f7; }
            .container { max-width: 700px; margin: auto; padding: 20px; background: #fff; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1); }
            h1 { text-align: center; }
            form { display: flex; flex-direction: column; gap: 10px; }
            input[type=file] { border: 1px solid #ddd; padding: 10px; }
            input[type=submit] { padding: 10px 20px; background: #007bff; color: white; border: none; cursor: pointer; }
            input[type=submit]:hover { background: #0056b3; }
            #download-link { display: block; margin-top: 20px; text-align: center; padding: 10px 20px; background: #007bff; color: white; border: none; cursor: pointer;}
            #download-link:hover {background: #0056b3;}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Upload an Image to Extract Metadata</h1>
            <form onsubmit="handleForm(event)">
                <input type="file" name="file" accept="image/*">
                <input type="submit" value="Extract Metadata">
            </form>
            <button id= "download-link" onclick="downloadFile()" style="display: none;">Download Metadata</button>
            
        </div>
        <script>
            let downloadUrl = "";

            async function handleForm(event) {
                event.preventDefault();
                const formData = new FormData(event.target);
                const response = await fetch('/upload_image', {
                    method: 'POST',
                    body: formData,
                });

                // Check if the request was successful
                if(response.ok){
                    const data = await response.json();
                    
                    if (data.image_metadata) {
                        const downloadLink = document.getElementById('download-link');
                        downloadLink.style.display = 'block';

                        // Create a Blob from the text data
                        const blob = new Blob([data.image_metadata], {type: "text/json"});
                        downloadUrl = URL.createObjectURL(blob);
                    }
                } else {
                    alert(`Error: ${response.status}`);
                }
            }
            
            function downloadFile() {
                if (downloadUrl !== "") {
                    // Create a link and trigger the download
                    const downloadLink = document.createElement('a');
                    downloadLink.href = downloadUrl;
                    downloadLink.download = "image_metadata.txt";
                    document.body.appendChild(downloadLink);
                    downloadLink.click();
                    document.body.removeChild(downloadLink);

                    // Reset the form
                    const form = document.querySelector('form');
                    form.reset();
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=content, status_code=200)

def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")

if __name__ == "__main__":
    main()
