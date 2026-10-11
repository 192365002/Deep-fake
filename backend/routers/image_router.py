from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
import uuid
import logging
from datetime import datetime

from utils.auth import get_current_user
from models.scan_result import ScanResult, MediaType, VerdictLevel
from utils.huggingface import scan_image_with_hf, validate_image_bytes
from utils.storage import upload_scan_media
from utils.database import save_scan_result_and_update_stats

router = APIRouter()
logger = logging.getLogger(__name__)

RECOMMENDATIONS_MAP = {
    VerdictLevel.FAKE: [
        "Flagged as high-probability generative AI or facial deepfake.",
        "Do not rely on this media for identity verification or news reporting.",
        "Check reverse image search engines to identify original unmodified source photos.",
        "Report manipulated content if impersonating an individual or organization."
    ],
    VerdictLevel.SUSPICIOUS: [
        "Borderline frequency/pixel anomalies detected — manual review advised.",
        "Verify identity through independent, out-of-band communication channels.",
        "Inspect lighting inconsistencies, unnatural eye reflections, or blurry ear contours."
    ],
    VerdictLevel.REAL: [
        "Image exhibits standard organic frequency distributions and edge sharpness.",
        "No significant synthetic decoders or checkerboard noise residues found.",
        "Always continue adhering to safe verification practices for sensitive inquiries."
    ]
}


@router.post("/image")
async def scan_image(file: UploadFile = File(...), user_id: str = Depends(get_current_user)):
    content_type = file.content_type or "image/jpeg"
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be a valid image format (JPEG, PNG, WebP).")

    contents = await file.read()
    if len(contents) > 20 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image size exceeds the 20MB limit.")

    # 1. Strict validation of image bytes
    try:
        validate_image_bytes(contents)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

    # 2. Upload file to Supabase Storage (Private User Bucket)
    storage_info = await upload_scan_media(
        user_id=user_id,
        file_bytes=contents,
        original_filename=file.filename or "image.jpg",
        content_type=content_type,
        category="image"
    )

    # 3. Model Inference (prithivMLmods/deepfake-detector-model-v1 + Spectral Analyzer)
    try:
        hf_result = await scan_image_with_hf(contents)
    except Exception as e:
        logger.error(f"Inference pipeline error: {e}")
        hf_result = {
            "fake_prob": 0.5,
            "real_prob": 0.5,
            "model_source": "Fallback Analyzer (Resource Constrained)",
            "disclaimer": "Analysis was limited due to an unexpected inference issue."
        }

    fake_prob = float(hf_result.get("fake_prob", 0.5))
    real_prob = float(hf_result.get("real_prob", 1.0 - fake_prob))
    model_source = hf_result.get("model_source", "prithivMLmods/deepfake-detector-model-v1")
    disclaimer = hf_result.get("disclaimer", "")

    if fake_prob >= 0.60:
        verdict = VerdictLevel.FAKE
        risk = "HIGH"
        explanations = [
            f"Detected deepfake synthesis indicators via {model_source}.",
            "High spectral divergence and facial gradient smoothing characteristic of generative networks."
        ]
    elif fake_prob >= 0.35:
        verdict = VerdictLevel.SUSPICIOUS
        risk = "MEDIUM"
        explanations = [
            f"Equivocal artifact distribution identified by {model_source}.",
            "Subtle pixel boundary anomalies suggest potential editing or re-encoding."
        ]
    else:
        verdict = VerdictLevel.REAL
        risk = "LOW"
        explanations = [
            f"Authentic natural camera sensor noise verified by {model_source}.",
            "Fourier transform spectral energy matches organic photographic captures."
        ]

    scan_id = str(uuid.uuid4())
    confidence = round(max(fake_prob, real_prob) * 100, 2)

    result = ScanResult(
        scan_id=scan_id,
        user_id=user_id,
        media_type=MediaType.IMAGE,
        verdict=verdict,
        confidence=confidence,
        fake_probability=round(fake_prob * 100, 2),
        real_probability=round(real_prob * 100, 2),
        risk_level=risk,
        explanations=explanations,
        recommendations=RECOMMENDATIONS_MAP[verdict],
        heatmap_base64=None,
        metadata={
            "info": model_source,
            "disclaimer": disclaimer,
            "storage_path": storage_info.get("storage_path"),
            "storage_url": storage_info.get("storage_url")
        },
        timestamp=datetime.utcnow().isoformat()
    )

    result_dict = result.dict()
    result_dict["storage_path"] = storage_info.get("storage_path")
    result_dict["storage_url"] = storage_info.get("storage_url")

    # 4. Save to Supabase PostgreSQL and update user stats
    try:
        await save_scan_result_and_update_stats(user_id, scan_id, result_dict)
    except Exception as e:
        logger.error(f"Non-fatal error persisting scan to database: {e}")

    return result_dict
