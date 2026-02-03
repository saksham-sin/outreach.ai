"""
Quick test script to validate dual sender email configuration.

Run this after updating your .env file to verify sender routing works correctly.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import get_settings
from app.core.constants import EmailType
from app.infrastructure.email_factory import get_email_provider, reset_email_provider


async def test_sender_configuration():
    """Test that sender configuration is properly loaded and routed."""
    
    print("🔍 Testing Dual Sender Email Configuration\n")
    print("=" * 60)
    
    # Get settings
    settings = get_settings()
    
    # Check configuration
    print("\n📋 Configuration Check:")
    print(f"\n  AUTH Sender:")
    print(f"    FROM: {settings.EMAIL_AUTH_FROM_ADDRESS or '⚠️  NOT SET (using fallback)'}")
    print(f"    NAME: {settings.EMAIL_AUTH_FROM_NAME}")
    print(f"\n  OUTREACH Sender:")
    print(f"    FROM: {settings.EMAIL_OUTREACH_FROM_ADDRESS or '⚠️  NOT SET (using fallback)'}")
    print(f"    NAME: {settings.EMAIL_OUTREACH_FROM_NAME}")
    print(f"    REPLY-TO: {settings.EMAIL_OUTREACH_REPLY_TO or '⚠️  NOT SET (using from address)'}")
    
    # Test provider initialization
    print("\n" + "=" * 60)
    print("\n🔧 Provider Initialization Test:")
    
    reset_email_provider()
    provider = get_email_provider()
    
    print(f"  ✅ ResendProvider initialized")
    print(f"  AUTH sender: {provider.auth_from_email} <{provider.auth_from_name}>")
    print(f"  OUTREACH sender: {provider.outreach_from_email} <{provider.outreach_from_name}>")
    print(f"  OUTREACH reply-to: {provider.outreach_reply_to}")
    
    # Test sender routing
    print("\n" + "=" * 60)
    print("\n🎯 Sender Routing Test:")
    
    auth_email, auth_name = provider._get_sender_config(EmailType.AUTH)
    outreach_email, outreach_name = provider._get_sender_config(EmailType.OUTREACH)
    
    print(f"\n  EmailType.AUTH routes to:")
    print(f"    {auth_email} <{auth_name}>")
    
    print(f"\n  EmailType.OUTREACH routes to:")
    print(f"    {outreach_email} <{outreach_name}>")
    
    # Validation
    print("\n" + "=" * 60)
    print("\n✅ Validation:")
    
    issues = []
    
    # Check if AUTH and OUTREACH are different (recommended)
    if auth_email == outreach_email:
        issues.append("⚠️  AUTH and OUTREACH use same sender - consider using different addresses")
    
    # Check no-reply pattern
    if not auth_email.startswith("no-reply"):
        issues.append("⚠️  AUTH sender doesn't use no-reply pattern (recommended: no-reply@domain)")
    
    # Check OUTREACH has reply-to
    if not provider.outreach_reply_to:
        issues.append("⚠️  OUTREACH reply-to not configured - replies won't be routed")
    
    # Check domain verification (basic check)
    if "@" in auth_email and "@" in outreach_email:
        auth_domain = auth_email.split("@")[1]
        outreach_domain = outreach_email.split("@")[1]
        if auth_domain != outreach_domain:
            issues.append(f"⚠️  AUTH and OUTREACH use different domains - ensure both are verified in Resend")
    
    if not issues:
        print("  ✅ All checks passed!")
        print("\n  Configuration is correct:")
        print(f"    • AUTH emails will send from: {auth_email}")
        print(f"    • OUTREACH emails will send from: {outreach_email}")
        print(f"    • OUTREACH replies will go to: {provider.outreach_reply_to}")
    else:
        print("  Issues found:")
        for issue in issues:
            print(f"    {issue}")
    
    print("\n" + "=" * 60)
    print("\n🧪 Ready to test with real emails:")
    print("  1. Magic link (AUTH): Request login from frontend")
    print("  2. Campaign (OUTREACH): Launch a campaign and send to test lead")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(test_sender_configuration())
