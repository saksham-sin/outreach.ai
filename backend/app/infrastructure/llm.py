"""LLM client for AI email generation using LangChain."""

from typing import Optional
from pydantic import BaseModel, Field
import logging

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.core.config import get_settings
from app.core.prompts import (
    EMAIL_GENERATION_SYSTEM_PROMPT,
    PITCH_ENHANCEMENT_SYSTEM_PROMPT,
    PITCH_ENHANCEMENT_PROMPT,
    STEP_1_EMAIL_PROMPT,
    STEP_2_EMAIL_PROMPT,
    STEP_3_EMAIL_PROMPT,
    REWRITE_EMAIL_PROMPT,
    TONE_DESCRIPTIONS,
    DEFAULT_TONE,
)
from app.domain.enums import EmailTone

logger = logging.getLogger(__name__)
settings = get_settings()


class GeneratedEmail(BaseModel):
    """Structured output schema for AI-generated emails."""
    
    subject: str = Field(
        description="Email subject line, max 60 characters, compelling and personalized"
    )
    body: str = Field(
        description="Email body in HTML format with proper paragraphs. Use {{first_name}} and {{company}} placeholders."
    )


class EnhancedPitch(BaseModel):
    """Structured output schema for enhanced pitch text."""

    pitch: str = Field(
        description="Improved campaign pitch, concise and compelling."
    )


class LLMClient:
    """Client for AI email generation using LangChain and OpenAI."""

    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=0.7,
            api_key=settings.OPENAI_API_KEY,
        )
        self.structured_llm = self.llm.with_structured_output(GeneratedEmail)
        self.pitch_llm = self.llm.with_structured_output(EnhancedPitch)

    def _get_step_prompt(self, step_number: int) -> str:
        """Get the appropriate prompt template for a step number."""
        prompts = {
            1: STEP_1_EMAIL_PROMPT,
            2: STEP_2_EMAIL_PROMPT,
            3: STEP_3_EMAIL_PROMPT,
        }
        return prompts.get(step_number, STEP_1_EMAIL_PROMPT)

    def _get_tone_description(self, tone: EmailTone) -> str:
        """Get the description for a tone."""
        return TONE_DESCRIPTIONS.get(tone.value, TONE_DESCRIPTIONS[DEFAULT_TONE])

    async def generate_email(
        self,
        campaign_name: str,
        pitch: str,
        step_number: int,
        tone: EmailTone = EmailTone.PROFESSIONAL,
        previous_subject: Optional[str] = None,
    ) -> GeneratedEmail:
        """
        Generate an email template for a campaign step.
        
        Args:
            campaign_name: Name of the campaign
            pitch: Value proposition / campaign pitch
            step_number: Step number (1-3)
            tone: Email tone
            previous_subject: Subject of previous email (for follow-ups)
            
        Returns:
            GeneratedEmail with subject and body
        """
        prompt_template = self._get_step_prompt(step_number)
        tone_description = self._get_tone_description(tone)
        
        # Format the prompt with campaign details
        user_prompt = prompt_template.format(
            campaign_name=campaign_name,
            pitch=pitch,
            tone=f"{tone.value} - {tone_description}",
            previous_subject=previous_subject or "N/A",
        )
        
        messages = [
            SystemMessage(content=EMAIL_GENERATION_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ]
        
        try:
            result = await self.structured_llm.ainvoke(messages)
            logger.info(f"Generated email for step {step_number}: {result.subject}")
            return result
        except Exception as e:
            logger.error(f"Error generating email: {str(e)}")
            raise

    async def rewrite_email(
        self,
        current_subject: str,
        current_body: str,
        instructions: str,
        campaign_name: str,
        pitch: str,
        step_number: int,
        tone: EmailTone = EmailTone.PROFESSIONAL,
    ) -> GeneratedEmail:
        """
        Rewrite an existing email template based on instructions.
        
        Args:
            current_subject: Current email subject
            current_body: Current email body
            instructions: Rewrite instructions from user
            campaign_name: Name of the campaign
            pitch: Value proposition / campaign pitch
            step_number: Step number (1-3)
            tone: Email tone
            
        Returns:
            GeneratedEmail with rewritten subject and body
        """
        tone_description = self._get_tone_description(tone)
        
        user_prompt = REWRITE_EMAIL_PROMPT.format(
            current_subject=current_subject,
            current_body=current_body,
            instructions=instructions,
            campaign_name=campaign_name,
            pitch=pitch,
            tone=f"{tone.value} - {tone_description}",
            step_number=step_number,
        )
        
        messages = [
            SystemMessage(content=EMAIL_GENERATION_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ]
        
        try:
            result = await self.structured_llm.ainvoke(messages)
            logger.info(f"Rewrote email for step {step_number}: {result.subject}")
            return result
        except Exception as e:
            logger.error(f"Error rewriting email: {str(e)}")
            raise

    async def enhance_pitch(
        self,
        campaign_name: str,
        pitch: str,
    ) -> str:
        """
        Enhance a campaign pitch using AI.

        Args:
            campaign_name: Name of the campaign
            pitch: Current pitch text

        Returns:
            Enhanced pitch text
        """
        user_prompt = PITCH_ENHANCEMENT_PROMPT.format(
            campaign_name=campaign_name,
            pitch=pitch,
        )

        messages = [
            SystemMessage(content=PITCH_ENHANCEMENT_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ]

        try:
            result: EnhancedPitch = await self.pitch_llm.ainvoke(messages)
            logger.info("Enhanced campaign pitch")
            return result.pitch.strip()
        except Exception as e:
            logger.error(f"Error enhancing pitch: {str(e)}")
            raise


# Singleton instance
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get or create LLM client instance."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
