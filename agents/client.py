import base64
from typing import Any, List, Optional, Type
import httpx
from pydantic import BaseModel
from google import genai
from google.genai import types
from config.settings import settings

THINKING_LEVEL_MAP = {
    "low": types.ThinkingLevel.LOW,
    "medium": types.ThinkingLevel.MEDIUM,
    "high": types.ThinkingLevel.HIGH,
}

# Hard cap on remote evidence downloads (protects the server from huge files)
MAX_REMOTE_EVIDENCE_BYTES = 15 * 1024 * 1024


class GeminiCarbonClient:
    """Wrapper around the official Google Gen AI SDK for gemini-4-carbon with thinking_level support."""

    def __init__(self) -> None:
        self.model_name = settings.gemini_model
        self._client: Optional[genai.Client] = None
        if settings.gemini_api_key and settings.gemini_api_key not in ("dummy_ci_key", "your_gemini_api_key_here"):
            self._client = genai.Client(api_key=settings.gemini_api_key)

    @property
    def is_configured(self) -> bool:
        return self._client is not None

    def build_multimodal_part(self, uri_or_data: str, mime_type: str = "image/png") -> Optional[types.Part]:
        """Loads inline base64 data URIs or remote HTTPS imagery into a Gen AI Part for multi-modal verification."""
        try:
            if uri_or_data.startswith("data:"):
                header, payload = uri_or_data.split(",", 1)
                detected_mime = header.split(";")[0].replace("data:", "") or mime_type
                if ";base64" not in header:
                    return None  # non-base64 data URIs (e.g. inline SVG text) are display-only
                raw_bytes = base64.b64decode(payload)
                return types.Part.from_bytes(data=raw_bytes, mime_type=detected_mime)
            if uri_or_data.startswith("https://"):
                with httpx.Client(timeout=15.0, follow_redirects=True) as http_client:
                    resp = http_client.get(uri_or_data)
                    resp.raise_for_status()
                    if len(resp.content) > MAX_REMOTE_EVIDENCE_BYTES:
                        return None
                    content_type = resp.headers.get("content-type", mime_type).split(";")[0]
                    return types.Part.from_bytes(data=resp.content, mime_type=content_type)
        except Exception:
            return None
        return None

    def generate_structured(
        self,
        system_prompt: str,
        contents: List[Any],
        response_schema: Type[BaseModel],
        thinking_level: str = "high",
        temperature: float = 0.2,
    ) -> BaseModel:
        if not self._client:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Configure GEMINI_API_KEY in .env or Render environment variables."
            )

        level_enum = THINKING_LEVEL_MAP.get(thinking_level.lower(), types.ThinkingLevel.HIGH)

        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=temperature,
            response_mime_type="application/json",
            response_schema=response_schema,
            thinking_config=types.ThinkingConfig(
                thinking_level=level_enum,
            ),
        )

        response = self._client.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=config,
        )

        if getattr(response, "parsed", None) is not None:
            return response.parsed
        return response_schema.model_validate_json(response.text)


carbon_client = GeminiCarbonClient()
