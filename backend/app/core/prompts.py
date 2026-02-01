"""LLM prompts for email generation - centralized prompt management."""

# System prompt for email generation
EMAIL_GENERATION_SYSTEM_PROMPT = """You are an expert sales copywriter specializing in cold email outreach.
Your emails are:
- Concise and to the point (under 150 words for body)
- Personalized using available placeholders
- Professional yet conversational
- Focused on value proposition, not features
- Include a clear, low-friction call to action

Available placeholders you MUST use where appropriate:
- {{first_name}} - Recipient's first name
- {{company}} - Recipient's company name

Always use placeholders instead of generic terms like "your company" or "you"."""

PITCH_ENHANCEMENT_SYSTEM_PROMPT = """You are an expert B2B copywriter.
Improve campaign pitches so they are clear, concise, and compelling.
Keep factual claims intact, avoid hype, and keep it under 500 characters.
Return only the improved pitch text."""

PITCH_ENHANCEMENT_PROMPT = """Improve the campaign pitch below.

Campaign Name: {campaign_name}
Current Pitch: {pitch}

Guidelines:
- 2-4 sentences
- Emphasize outcomes and value, not features
- Keep professional, confident tone
- No markdown or bullets
"""

# Template for generating initial outreach email (Step 1)
STEP_1_EMAIL_PROMPT = """Generate a cold outreach email for the following campaign:

Campaign Name: {campaign_name}
Value Proposition: {pitch}
Tone: {tone}

This is the FIRST email in the sequence. Focus on:
- A compelling, personalized subject line (under 50 characters)
- Opening that grabs attention and shows you've done research
- Clear value proposition
- Soft call-to-action (e.g., "Worth a quick chat?")

Use {{first_name}} and {{company}} placeholders appropriately."""

# Template for generating follow-up email (Step 2)
STEP_2_EMAIL_PROMPT = """Generate a follow-up email for the following campaign:

Campaign Name: {campaign_name}
Value Proposition: {pitch}
Tone: {tone}
Previous Subject: {previous_subject}

This is the SECOND email (follow-up). Focus on:
- Subject line that references the previous email or adds new angle
- Brief acknowledgment that you reached out before
- New angle or additional value point
- Slightly more direct call-to-action

Use {{first_name}} and {{company}} placeholders appropriately."""

# Template for generating final follow-up email (Step 3)
STEP_3_EMAIL_PROMPT = """Generate a final follow-up email for the following campaign:

Campaign Name: {campaign_name}
Value Proposition: {pitch}
Tone: {tone}
Previous Subject: {previous_subject}

This is the FINAL email (breakup email). Focus on:
- Subject line that creates urgency or closure
- Brief, respectful tone acknowledging no response
- Final compelling reason to connect
- Clear but no-pressure call-to-action
- Leave door open for future

Use {{first_name}} and {{company}} placeholders appropriately."""

# Template for rewriting an existing email
REWRITE_EMAIL_PROMPT = """Rewrite the following email while maintaining its core message:

Current Subject: {current_subject}
Current Body: {current_body}

Rewrite Instructions: {instructions}

Campaign Context:
- Campaign Name: {campaign_name}
- Value Proposition: {pitch}
- Tone: {tone}
- Step Number: {step_number}

Maintain the same placeholders ({{first_name}}, {{company}}) in appropriate places.
Follow the rewrite instructions while keeping the email professional and effective."""

# Tone descriptions for LLM context
TONE_DESCRIPTIONS = {
    "professional": "Formal, business-appropriate language. Respectful and straightforward.",
    "casual": "Friendly, conversational tone. Like talking to a colleague.",
    "urgent": "Time-sensitive language. Creates FOMO without being pushy.",
    "friendly": "Warm, approachable tone. Builds rapport quickly.",
    "direct": "No fluff, straight to the point. Respects recipient's time.",
}

DEFAULT_TONE = "professional"

# Magic link email
MAGIC_LINK_EMAIL_SUBJECT = "Your login link for Outreach AI"

MAGIC_LINK_EMAIL_BODY = """Hi,

Click the link below to sign in to your Outreach AI account:

{magic_link}

This link expires in {expire_minutes} minutes.

If you didn't request this link, you can safely ignore this email.

Best,
The Outreach AI Team"""
