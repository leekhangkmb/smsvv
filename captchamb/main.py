import base64
import io
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from PIL import Image
from mb_capcha_ocr import OcrModel

app = FastAPI(
    title="MB Bank Captcha OCR",
    description="API captcha MB Bank to base64",
    version="1.0.0"
)

ocr_model = OcrModel()

class CaptchaRequest(BaseModel):
    base64: str

@app.get("/")
def health():
    return {"status": "ok"}

@app.post("/api/captcha/mbbank")
def solve_captcha(req: CaptchaRequest):
    b64_str = req.base64
    if "," in b64_str:
        b64_str = b64_str.split(",", 1)[1]

    try:
        img_bytes = base64.b64decode(b64_str)
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="Base64 khong hop le")

    text = ocr_model.predict(img)
    return {"captcha": text, "status": "success"}


if __name__ == "__main__":
    import os
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        workers=1
    )
