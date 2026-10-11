"""
History Router for Social Shield - Supabase PostgreSQL Implementation
Replaces Firestore subcollections with relational PostgreSQL queries,
secure storage cleanup, and automated stats recalculation.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, Dict, Any, List
import logging

from utils.auth import get_current_user
from utils.database import get_supabase_client, recalculate_and_update_stats, get_user_stats as db_get_user_stats
from utils.storage import delete_scan_media, get_authorized_url

router = APIRouter()
logger = logging.getLogger(__name__)


def format_scan_record(data: Dict[str, Any]) -> Dict[str, Any]:
    """Formats a database scan record to be compatible with both Android (camelCase) and Web (camelCase/snake_case)"""
    if not data:
        return data

    scan_id = str(data.get("id") or data.get("scan_id") or data.get("scanId"))
    user_id = str(data.get("user_id") or data.get("userId"))
    media_type = str(data.get("media_type") or data.get("mediaType") or "IMAGE")
    verdict = str(data.get("verdict") or "SAFE")
    conf = float(data.get("confidence") or 100.0)
    fake_p = float(data.get("fake_probability") or data.get("fakeProbability") or 0.0)
    real_p = float(data.get("real_probability") or data.get("realProbability") or 100.0)
    risk = str(data.get("risk_level") or data.get("riskLevel") or "LOW")
    explanations = data.get("explanations") or []
    recommendations = data.get("recommendations") or []
    ts = str(data.get("created_at") or data.get("timestamp") or "")

    return {
        "id": scan_id,
        "scan_id": scan_id,
        "scanId": scan_id,
        "user_id": user_id,
        "userId": user_id,
        "media_type": media_type,
        "mediaType": media_type,
        "verdict": verdict,
        "confidence": conf,
        "fake_probability": fake_p,
        "fakeProbability": fake_p,
        "real_probability": real_p,
        "realProbability": real_p,
        "risk_level": risk,
        "riskLevel": risk,
        "explanations": explanations,
        "recommendations": recommendations,
        "heatmap_base64": data.get("heatmap_base64") or data.get("heatmapBase64"),
        "heatmapBase64": data.get("heatmap_base64") or data.get("heatmapBase64"),
        "storage_path": data.get("storage_path"),
        "storage_url": data.get("storage_url"),
        "storageUrl": data.get("storage_url"),
        "metadata": data.get("metadata") or {},
        "timestamp": ts,
        "created_at": ts
    }


@router.get("/history")
async def get_history(
    user_id: str = Depends(get_current_user),
    media_type: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Retrieve paginated scan history for authenticated user from Supabase PostgreSQL"""
    try:
        client = get_supabase_client()
        query = client.table("scans").select("*").eq("user_id", user_id)

        if media_type:
            # Query for matching media type
            res = query.order("created_at", desc=True).execute()
            all_records = res.data or []
            filtered = [r for r in all_records if str(r.get("media_type")).upper() == media_type.upper()]
            total_count = len(filtered)
            paginated = filtered[offset:offset + limit]
        else:
            res = query.order("created_at", desc=True).execute()
            all_records = res.data or []
            total_count = len(all_records)
            paginated = all_records[offset:offset + limit]

        items = []
        for row in paginated:
            formatted = format_scan_record(row)
            # Remove bulky base64 data for efficient list responses
            formatted.pop("heatmap_base64", None)
            formatted.pop("heatmapBase64", None)
            items.append(formatted)

        return {
            "items": items,
            "count": total_count,
            "offset": offset
        }

    except Exception as e:
        logger.error(f"Supabase history query error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve scan history from database.")


@router.get("/history/{scan_id}")
async def get_scan_detail(
    scan_id: str,
    user_id: str = Depends(get_current_user)
):
    """Retrieve detailed scan report by ID from Supabase PostgreSQL"""
    try:
        client = get_supabase_client()
        res = client.table("scans").select("*").eq("id", scan_id).eq("user_id", user_id).execute()

        if not res.data:
            # Check if scan_id was saved with alternate key or UUID
            alt_res = client.table("scans").select("*").eq("user_id", user_id).execute()
            match = next((r for r in (alt_res.data or []) if str(r.get("id")) == scan_id), None)
            if not match:
                raise HTTPException(status_code=404, detail="Scan record not found or access denied.")
            row = match
        else:
            row = res.data[0]

        formatted = format_scan_record(row)

        # Refresh signed access URL if private file exists
        storage_path = formatted.get("storage_path")
        if storage_path:
            fresh_url = await get_authorized_url(storage_path, expires_in=3600)
            if fresh_url:
                formatted["storage_url"] = fresh_url
                formatted["storageUrl"] = fresh_url

        return formatted

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching scan detail: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve scan details.")


@router.delete("/history/{scan_id}")
async def delete_scan(
    scan_id: str,
    user_id: str = Depends(get_current_user)
):
    """Delete a scan record and remove associated private storage media"""
    try:
        client = get_supabase_client()
        # Find record to retrieve storage path
        res = client.table("scans").select("*").eq("id", scan_id).eq("user_id", user_id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Scan record not found or access denied.")

        row = res.data[0]
        storage_path = row.get("storage_path")

        # Delete from PostgreSQL table
        client.table("scans").delete().eq("id", scan_id).eq("user_id", user_id).execute()

        # Clean up Supabase Storage file
        if storage_path:
            await delete_scan_media(storage_path)

        # Recalculate user statistics
        await recalculate_and_update_stats(user_id)

        return {"message": "Scan deleted successfully", "scan_id": scan_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting scan {scan_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete scan record.")


@router.delete("/history")
async def clear_all_history(user_id: str = Depends(get_current_user)):
    """Clear all scan records and associated storage files for the authenticated user"""
    try:
        client = get_supabase_client()
        res = client.table("scans").select("*").eq("user_id", user_id).execute()
        records = res.data or []

        for row in records:
            storage_path = row.get("storage_path")
            if storage_path:
                await delete_scan_media(storage_path)

        client.table("scans").delete().eq("user_id", user_id).execute()
        await recalculate_and_update_stats(user_id)

        return {"message": "All history cleared successfully", "count": len(records)}

    except Exception as e:
        logger.error(f"Error clearing history: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear scan history.")


@router.get("/stats")
async def get_user_statistics(user_id: str = Depends(get_current_user)):
    """Retrieve user aggregate stats (trust score, totals) from Supabase PostgreSQL"""
    try:
        stats = await db_get_user_stats(user_id)
        # Return both snake_case and camelCase
        return {
            "total_scans": stats.get("totalScans", 0),
            "fake_detected": stats.get("fakeDetected", 0),
            "suspicious_detected": stats.get("suspiciousDetected", 0),
            "safe_detected": stats.get("safeDetected", 0),
            "trust_score": stats.get("trustScore", 100),
            "totalScans": stats.get("totalScans", 0),
            "fakeDetected": stats.get("fakeDetected", 0),
            "suspiciousDetected": stats.get("suspiciousDetected", 0),
            "safeDetected": stats.get("safeDetected", 0),
            "trustScore": stats.get("trustScore", 100)
        }
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        return {
            "total_scans": 0, "fake_detected": 0, "suspicious_detected": 0, "safe_detected": 0, "trust_score": 100,
            "totalScans": 0, "fakeDetected": 0, "suspiciousDetected": 0, "safeDetected": 0, "trustScore": 100
        }
