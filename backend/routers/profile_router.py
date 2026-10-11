"""
Fake Social Media Profile Detection Router
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import httpx
import re
import uuid
import logging
from datetime import datetime
from typing import Optional

from utils.auth import get_current_user
from models.scan_result import ScanResult, MediaType, VerdictLevel

router = APIRouter()
logger = logging.getLogger(__name__)


class ProfileScanRequest(BaseModel):
    username: Optional[str] = None
    display_name: Optional[str] = None
    bio: Optional[str] = None
    followers: Optional[int] = None
    following: Optional[int] = None
    post_count: Optional[int] = None
    account_age_days: Optional[int] = None
    profile_pic_url: Optional[str] = None
    platform: Optional[str] = "unknown"
    likes_per_post: Optional[int] = None
    comments_per_post: Optional[int] = None


def analyze_profile_signals(data: ProfileScanRequest) -> tuple[float, list[str], list[str]]:
    score = 0.0
    reasons = []
    recommendations = []

    # Follower/following ratio (bots follow many, have few followers)
    if data.followers is not None and data.following is not None:
        if data.following > 0:
            ratio = data.followers / data.following
            if ratio < 0.05:
                score += 0.25
                reasons.append("Extremely low follower/following ratio (less than 5%) — classic bot-like behavior")
            elif ratio < 0.15:
                score += 0.15
                reasons.append("Low follower/following ratio (less than 15%) — suspicious follower balance")
        if data.following > 3000 and data.followers < 100:
            score += 0.20
            reasons.append("Mass-following behavior with minimal audience")

    # New account with high posting frequency
    if data.account_age_days is not None and data.post_count is not None:
        if data.account_age_days < 30:
            if data.post_count > 150:
                score += 0.25
                reasons.append("Unusually high post frequency for a new account (possible automated botting)")
            else:
                score += 0.10
                reasons.append("Recent account creation (less than 30 days old)")
        elif data.account_age_days > 365 and data.post_count == 0:
            score += 0.10
            reasons.append("Dormant account pattern: over a year old with 0 posts")

    # Generic or suspicious username patterns
    if data.username:
        # Letters followed by 4 or more digits
        if re.match(r'^[a-zA-Z]+\d{4,}$', data.username):
            score += 0.20
            reasons.append("Username matches automated generation pattern (alphabet letters + multiple digits)")
        # String length and special characters
        if len(data.username) > 20:
            score += 0.05
            reasons.append("Unusually long username (length > 20 characters)")

    # Bio quality & spam keywords
    if data.bio:
        bio_lower = data.bio.lower()
        if len(data.bio) < 8:
            score += 0.10
            reasons.append("Minimal or empty bio description")
        
        spam_words = ['crypto', 'whatsapp', 'forex', 'earn money', 'cash', 'investment', 'rich', 'sugar daddy', 'meet me', 'onlyfans', 'giftcard', 'free money', 'telegram', 'inbox me']
        matched = [w for w in spam_words if w in bio_lower]
        if matched:
            spam_score = min(0.10 * len(matched), 0.25)
            score += spam_score
            reasons.append(f"Financial scam/spam keywords detected in bio: {', '.join(matched)}")
    else:
        score += 0.10
        reasons.append("Missing profile bio description")

    # Missing profile picture
    if not data.profile_pic_url:
        score += 0.15
        reasons.append("No profile picture uploaded — common placeholder pattern for bot networks")

    # Engagement analysis
    if data.followers is not None and data.followers > 500:
        likes = data.likes_per_post or 0
        comments = data.comments_per_post or 0
        total_interactions = likes + comments
        engagement_rate = total_interactions / data.followers
        if engagement_rate < 0.002: # 0.2%
            score += 0.20
            reasons.append("Extremely low post engagement rate relative to follower count (possible fake followers)")
        elif engagement_rate < 0.01: # 1.0%
            score += 0.10
            reasons.append("Low profile engagement rate")

    final_score = min(score, 1.0)
    
    # Recommendations based on severity
    if final_score >= 0.7:
        recommendations = [
            "Block and report this profile to the social platform immediately.",
            "Do not accept any direct messages, file sharing, or connection requests.",
            "Do not share any passwords, email links, or OTP verification codes."
        ]
    elif final_score >= 0.3:
        recommendations = [
            "Exercise caution when responding to private messages from this account.",
            "Avoid clicking on any short URLs or links listed in their bio.",
            "Verify their claims through external, reputable channels before engaging."
        ]
    else:
        recommendations = [
            "This profile appears legitimate. No immediate security action needed.",
            "Keep practicing standard cyber hygiene when sharing information online."
        ]

    return final_score, reasons, recommendations


@router.post("/profile")
async def scan_profile(
    request: ProfileScanRequest,
    user_id: str = Depends(get_current_user)
):
    """Analyze social media profile for fake/bot indicators"""
    fake_score, reasons, recommendations = analyze_profile_signals(request)

    if fake_score >= 0.7:
        verdict = VerdictLevel.FAKE
        risk = "HIGH"
    elif fake_score >= 0.3:
        verdict = VerdictLevel.SUSPICIOUS
        risk = "MEDIUM"
    else:
        verdict = VerdictLevel.REAL
        risk = "LOW"

    if not reasons:
        reasons.append("Profile appears legitimate — no bot/fake indicators detected")

    scan_id = str(uuid.uuid4())
    result = ScanResult(
        scan_id=scan_id,
        user_id=user_id,
        media_type=MediaType.PROFILE,
        verdict=verdict,
        confidence=round(max(fake_score, 1 - fake_score) * 100, 2),
        fake_probability=round(fake_score * 100, 2),
        real_probability=round((1 - fake_score) * 100, 2),
        risk_level=risk,
        explanations=reasons,
        recommendations=recommendations,
        metadata={"platform": request.platform, "username": request.username},
        timestamp=datetime.utcnow().isoformat()
    )
    
    from utils.database import save_scan_result_and_update_stats
    try:
        await save_scan_result_and_update_stats(user_id, result.scan_id, result.dict())
    except Exception as e:
        logger.error(f"Non-fatal error persisting profile scan to database: {e}")
    
    return result.dict()
