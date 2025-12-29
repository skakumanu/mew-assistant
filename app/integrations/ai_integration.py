"""
AI integration for OpenAI and Anthropic APIs.
"""

import json
from datetime import datetime
from typing import Any, Dict, Optional

from app.utils.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AIIntegration:
    """AI integration supporting multiple providers."""

    def __init__(self):
        self.openai_api_key = getattr(settings, "OPENAI_API_KEY", "")
        self.anthropic_api_key = getattr(settings, "ANTHROPIC_API_KEY", "")
        self.default_model = getattr(settings, "AI_MODEL", "gpt-4")

        self.openai_client = None
        self.anthropic_client = None

        self._initialize_clients()

    def _initialize_clients(self):
        """Initialize AI provider clients."""
        if self.openai_api_key:
            try:
                from openai import AsyncOpenAI

                self.openai_client = AsyncOpenAI(api_key=self.openai_api_key)
                logger.info("OpenAI client initialized")
            except ImportError:
                logger.warning("OpenAI package not installed")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI: {str(e)}")

        if self.anthropic_api_key:
            try:
                from anthropic import AsyncAnthropic

                self.anthropic_client = AsyncAnthropic(api_key=self.anthropic_api_key)
                logger.info("Anthropic client initialized")
            except ImportError:
                logger.warning("Anthropic package not installed")
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic: {str(e)}")

    async def generate_text(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 500,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate text using AI model."""
        model = model or self.default_model

        try:
            if model.startswith("gpt") or model.startswith("o1"):
                return await self._generate_openai(
                    prompt, model, max_tokens, temperature, system_prompt
                )
            elif model.startswith("claude"):
                return await self._generate_anthropic(
                    prompt, model, max_tokens, temperature, system_prompt
                )
            else:
                return {"success": False, "message": f"Unsupported model: {model}"}

        except Exception as e:
            logger.error(f"AI generation failed: {str(e)}")
            return {"success": False, "message": f"AI generation failed: {str(e)}"}

    async def _generate_openai(
        self,
        prompt: str,
        model: str,
        max_tokens: int,
        temperature: float,
        system_prompt: Optional[str],
    ) -> Dict[str, Any]:
        """Generate text using OpenAI."""
        if not self.openai_client:
            return {"success": False, "message": "OpenAI not configured"}

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await self.openai_client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        return {
            "success": True,
            "text": response.choices[0].message.content,
            "model": model,
            "tokens_used": response.usage.total_tokens,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def _generate_anthropic(
        self,
        prompt: str,
        model: str,
        max_tokens: int,
        temperature: float,
        system_prompt: Optional[str],
    ) -> Dict[str, Any]:
        """Generate text using Anthropic Claude."""
        if not self.anthropic_client:
            return {"success": False, "message": "Anthropic not configured"}

        response = await self.anthropic_client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt or "",
            messages=[{"role": "user", "content": prompt}],
        )

        return {
            "success": True,
            "text": response.content[0].text,
            "model": model,
            "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def generate_summary(
        self, content: str, summary_type: str = "daily"
    ) -> Dict[str, Any]:
        """Generate a summary of content."""
        prompts = {
            "daily": "Summarize the following daily activities clearly and concisely:",
            "weekly": "Create a weekly summary highlighting patterns and key events:",
            "activity": "Summarize this activity log focusing on important events:",
        }

        system_prompt = """You are Mew, a helpful assistant for special needs families.
    Create clear, compassionate summaries."""

        prompt = f"{prompts.get(summary_type, prompts['daily'])}\n\n{content}"

        result = await self.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=800,
            temperature=0.5,
        )

        if result.get("success"):
            result["summary_type"] = summary_type

        return result

    async def analyze_message(
        self, message: str, context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze a message to determine intent."""
        system_prompt = """Extract intent and key information. Return JSON:
{
  "intent": "schedule|reminder|question|report|other",
  "priority": "high|medium|low",
  "entities": {"date": "", "time": "", "activity": ""},
  "response_needed": true/false
}"""

        prompt = f"Analyze: {message}"
        if context:
            prompt += f"\n\nContext: {context}"

        result = await self.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=200,
            temperature=0.3,
        )

        if result.get("success"):
            try:
                analysis = json.loads(result["text"])
                result["analysis"] = analysis
            except json.JSONDecodeError:
                result["analysis"] = {"intent": "unknown"}

        return result
