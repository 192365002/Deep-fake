"""
Test Data for Social Shield Appium E2E Automation
Includes valid/invalid credentials, multi-modal payload samples, and expected verdicts.
"""

# Authentication Test Data
VALID_USER = {
    "email": "testuser_automation@socialshield.ai",
    "password": "Password123!",
    "full_name": "Automation Tester"
}

INVALID_USERS = [
    {"email": "", "password": "Password123!", "expected_error": "Email and password required"},
    {"email": "invalid_email_format", "password": "Password123!", "expected_error": "Invalid email"},
    {"email": "valid@email.com", "password": "123", "expected_error": "Password must be at least 6 characters"},
    {"email": "nonexistent_user_9999@socialshield.ai", "password": "WrongPassword999!", "expected_error": "Invalid login credentials"}
]

# Text Scam Test Samples
TEXT_SAMPLES = {
    "phishing_urgent": "URGENT: Your bank account will be suspended within 24 hours. Click here immediately to verify your credentials: https://bank-verify-alert.com",
    "crypto_scam": "Congratulations! You won 2.5 Bitcoin in our annual prize draw. Send 0.05 BTC to claim your wallet reward now.",
    "otp_fraud": "SocialShield Alert: Enter OTP 849201 to confirm your wire transfer of $4,500. Do not share this code.",
    "legitimate_text": "Hi Alex, please review the quarterly security compliance report before tomorrow's team sync. Thanks!"
}

# URL Threat Samples
URL_SAMPLES = {
    "phishing_url": "http://secure-login-account-update-portal-paypal.xyz/login.php",
    "safe_url": "https://www.google.com",
    "suspicious_ip": "http://192.168.1.100/wp-content/fake-invoice.pdf"
}

# Profile Bot Samples
PROFILE_SAMPLES = {
    "bot_profile": {
        "username": "crypto_moon_airdrop_bot99",
        "followers": "12",
        "following": "7500",
        "bio": "DM FOR 100X CRYPTO SIGNALS 🚀🚀 JOIN TELEGRAM NOW FREE MONEY",
        "account_age_days": "2",
        "post_count": "1"
    },
    "authentic_profile": {
        "username": "sarah_security_dev",
        "followers": "1840",
        "following": "620",
        "bio": "Cybersecurity Engineer & Open Source Contributor. Passionate about AI safety.",
        "account_age_days": "1420",
        "post_count": "230"
    }
}
