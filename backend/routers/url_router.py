"""
URL / Phishing Detection Router
Uses Google Safe Browsing API + heuristic analysis
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl
import httpx
import re
import os
import uuid
import logging
from datetime import datetime
from urllib.parse import urlparse

from utils.auth import get_current_user
from models.scan_result import ScanResult, MediaType, VerdictLevel

router = APIRouter()
logger = logging.getLogger(__name__)

GOOGLE_SAFE_BROWSING_KEY = os.getenv("GOOGLE_SAFE_BROWSING_API_KEY", "")
VIRUSTOTAL_KEY = os.getenv("VIRUSTOTAL_API_KEY", "")


class URLScanRequest(BaseModel):
    url: str


SUSPICIOUS_TLD = ['.xyz', '.tk', '.ml', '.ga', '.cf', '.gq', '.top', '.work', '.click']
SUSPICIOUS_KEYWORDS = [
    'login', 'signin', 'account', 'secure', 'update', 'verify', 'confirm',
    'paypal', 'amazon', 'netflix', 'google', 'microsoft', 'apple', 'bank',
    'wallet', 'crypto', 'reward', 'prize', 'lucky', 'winner'
]


def heuristic_url_analysis(url: str) -> tuple[float, list[str]]:
    """Rule-based URL threat analysis"""
    parsed = urlparse(url if url.startswith('http') else f'https://{url}')
    domain = parsed.netloc.lower()
    path = parsed.path.lower()
    full = url.lower()
    
    score = 0.0
    reasons = []
    
    # Check TLD
    for tld in SUSPICIOUS_TLD:
        if domain.endswith(tld):
            score += 0.3
            reasons.append(f"Suspicious TLD: {tld}")
            break
    
    # Excessive subdomains
    subdomain_count = len(domain.split('.')) - 2
    if subdomain_count > 3:
        score += 0.2
        reasons.append(f"Excessive subdomains ({subdomain_count}) — common in phishing")
    
    # IP address instead of domain
    if re.match(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', domain):
        score += 0.4
        reasons.append("URL uses IP address instead of domain name")
    
    # Suspicious keywords in domain
    matched_keywords = [kw for kw in SUSPICIOUS_KEYWORDS if kw in domain]
    if matched_keywords:
        score += 0.15 * len(matched_keywords)
        reasons.append(f"Brand impersonation keywords: {', '.join(matched_keywords[:3])}")
    
    # Very long URL
    if len(url) > 150:
        score += 0.15
        reasons.append("Unusually long URL (obfuscation technique)")
    
    # Multiple redirects in URL
    if url.count('http') > 1:
        score += 0.25
        reasons.append("URL-within-URL detected (redirect chain)")
    
    # URL shorteners
    shorteners = ['bit.ly', 'tinyurl', 't.co', 'goo.gl', 'ow.ly', 'short.link']
    if any(s in domain for s in shorteners):
        score += 0.15
        reasons.append("URL shortener detected — destination unknown")
    
    # No HTTPS
    if not url.startswith('https://'):
        score += 0.1
        reasons.append("Non-HTTPS URL — data transmission not encrypted")
    
    # Typosquatting detection (common brands)
    brand_typos = {
        'paypa1': 'PayPal', 'g00gle': 'Google', 'amaz0n': 'Amazon',
        'netf1ix': 'Netflix', 'micros0ft': 'Microsoft'
    }
    for typo, brand in brand_typos.items():
        if typo in domain:
            score += 0.45
            reasons.append(f"Possible typosquatting of {brand}")
    
    return min(score, 1.0), reasons


async def check_google_safe_browsing(url: str) -> tuple[bool, list[str]]:
    """Check URL against Google Safe Browsing API"""
    if not GOOGLE_SAFE_BROWSING_KEY:
        return False, []
    
    api_url = f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={GOOGLE_SAFE_BROWSING_KEY}"
    payload = {
        "client": {"clientId": "socialshield", "clientVersion": "1.0.0"},
        "threatInfo": {
            "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE", "POTENTIALLY_HARMFUL_APPLICATION"],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": url}]
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(api_url, json=payload)
            data = resp.json()
            
            if data.get("matches"):
                threats = [m.get("threatType", "UNKNOWN") for m in data["matches"]]
                reasons = [f"Google Safe Browsing: {t.replace('_', ' ').title()}" for t in threats]
                return True, reasons
    except Exception as e:
        logger.error(f"Safe Browsing API error: {e}")
    
    return False, []


async def check_virustotal(url: str) -> tuple[float, list[str]]:
    """Check URL against VirusTotal"""
    if not VIRUSTOTAL_KEY:
        return 0.0, []
    
    import base64
    url_id = base64.urlsafe_b64encode(url.encode()).decode().strip('=')
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"https://www.virustotal.com/api/v3/urls/{url_id}",
                headers={"x-apikey": VIRUSTOTAL_KEY}
            )
            
            if resp.status_code == 200:
                data = resp.json()
                stats = data.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
                malicious = stats.get("malicious", 0)
                total = sum(stats.values())
                
                if total > 0 and malicious > 0:
                    vt_score = malicious / total
                    return vt_score, [f"VirusTotal: {malicious}/{total} engines flagged as malicious"]
    except Exception as e:
        logger.error(f"VirusTotal error: {e}")
    
    return 0.0, []


@router.post("/url")
async def scan_url(
    request: URLScanRequest,
    user_id: str = Depends(get_current_user)
):
    """Scan a URL for phishing/malware threats"""
    url = request.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL cannot be empty")
    
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # Heuristic analysis
    heuristic_score, heuristic_reasons = heuristic_url_analysis(url)
    
    # Google Safe Browsing
    gsb_flagged, gsb_reasons = await check_google_safe_browsing(url)
    
    # VirusTotal
    vt_score, vt_reasons = await check_virustotal(url)
    
    # Combine scores
    if gsb_flagged:
        final_score = max(heuristic_score, 0.9)
    elif vt_score > 0:
        final_score = max(heuristic_score, vt_score + 0.3)
    else:
        final_score = heuristic_score
    
    final_score = min(final_score, 1.0)
    
    all_reasons = heuristic_reasons + gsb_reasons + vt_reasons
    
    if final_score >= 0.6:
        verdict = VerdictLevel.FAKE
        risk = "HIGH"
    elif final_score >= 0.30:
        verdict = VerdictLevel.SUSPICIOUS
        risk = "MEDIUM"
    else:
        verdict = VerdictLevel.REAL
        risk = "LOW"
    
    if not all_reasons:
        all_reasons.append("No threats detected — URL appears safe")
    
    scan_id = str(uuid.uuid4())
    parsed = urlparse(url)
    
    result = ScanResult(
        scan_id=scan_id,
        user_id=user_id,
        media_type=MediaType.URL,
        verdict=verdict,
        confidence=round(max(final_score, 1 - final_score) * 100, 2),
        fake_probability=round(final_score * 100, 2),
        real_probability=round((1 - final_score) * 100, 2),
        risk_level=risk,
        explanations=all_reasons,
        metadata={
            "url": url,
            "domain": parsed.netloc,
            "heuristic_score": round(heuristic_score * 100, 2),
            "gsb_flagged": gsb_flagged,
            "virustotal_score": round(vt_score * 100, 2)
        },
        timestamp=datetime.utcnow().isoformat()
    )
    
    from utils.database import save_scan_result_and_update_stats
    try:
        await save_scan_result_and_update_stats(user_id, result.scan_id, result.dict())
    except Exception as e:
        logger.error(f"Non-fatal error persisting url scan to database: {e}")
    
    return result.dict()
