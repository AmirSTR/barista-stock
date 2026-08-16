import base64
import json
import logging
import re
import httpx
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.ocr import InvoiceItemOCR, InvoiceOCRResponse

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Ты ассистент складского учета сети кофеен. Твоя задача — проанализировать фотографию накладной/чека/ТОРГ-12/УПД, извлечь из неё таблицу с товарами и вернуть строгий JSON по схеме:
{
  "invoice_number": "номер документа или null",
  "items": [
    {"raw_name": "наименование как в чеке", "quantity": 10.0, "unit": "шт/уп/кг/бут"}
  ]
}
Извлекай только фактические товарные позиции и количество. Никакого вводного текста или пояснений вне JSON."""


class OCRConfigurationError(RuntimeError):
    """Raised when OCR is invoked without a valid production configuration."""


class OCRService:
    """Service for extracting line items from supply invoices and receipts using Vision LLMs."""

    @classmethod
    def _clean_json_response(cls, text: str) -> str:
        """Strip markdown code fences and extraneous text from LLM response."""
        cleaned = text.strip()
        # Strip ```json ... ``` or ``` ... ```
        if "```" in cleaned:
            match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
            if match:
                cleaned = match.group(1).strip()
        return cleaned

    @classmethod
    async def _call_gemini_vision(cls, image_bytes: bytes, api_key: str, model_name: str) -> str:
        """Send image to Google Gemini Vision API."""
        encoded_image = base64.b64encode(image_bytes).decode("utf-8")
        
        # Clean model name if full path passed
        model = model_name.replace("models/", "")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": SYSTEM_PROMPT},
                        {
                            "inlineData": {
                                "mimeType": "image/jpeg",
                                "data": encoded_image,
                            }
                        },
                    ],
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.1,
            },
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload)
            if response.status_code != 200:
                logger.error(f"Gemini API error ({response.status_code}): {response.text}")
                raise RuntimeError(f"Gemini API returned error {response.status_code}: {response.text}")

            data = response.json()
            try:
                raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                return raw_text
            except (KeyError, IndexError) as e:
                logger.error(f"Unexpected Gemini API response structure: {data}")
                raise ValueError(f"Failed to extract text from Gemini response: {e}")

    @classmethod
    async def _call_openai_vision(cls, image_bytes: bytes, api_key: str, model_name: str) -> str:
        """Send image to OpenAI GPT-4o-mini Vision API."""
        encoded_image = base64.b64encode(image_bytes).decode("utf-8")
        url = "https://api.openai.com/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model_name or "gpt-4o-mini",
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Распознай товарные позиции и количество из этой накладной:",
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{encoded_image}",
                                "detail": "high",
                            },
                        },
                    ],
                },
            ],
            "temperature": 0.1,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code != 200:
                logger.error(f"OpenAI API error ({response.status_code}): {response.text}")
                raise RuntimeError(f"OpenAI API returned error {response.status_code}: {response.text}")

            data = response.json()
            try:
                raw_text = data["choices"][0]["message"]["content"]
                return raw_text
            except (KeyError, IndexError) as e:
                logger.error(f"Unexpected OpenAI API response structure: {data}")
                raise ValueError(f"Failed to extract text from OpenAI response: {e}")

    @classmethod
    async def parse_invoice_photo(cls, image_bytes: bytes) -> InvoiceOCRResponse:
        """Analyze invoice image using Vision LLM and return validated InvoiceOCRResponse."""
        provider = (settings.OCR_PROVIDER or "gemini").lower()
        gemini_key = settings.GEMINI_API_KEY
        openai_key = settings.OPENAI_API_KEY

        if settings.OCR_DEMO_MODE:
            logger.warning("OCR_DEMO_MODE is enabled; returning deterministic demo invoice data.")
            return InvoiceOCRResponse(
                invoice_number="Б/Н (Демо)",
                items=[
                    InvoiceItemOCR(raw_name="Сироп Солёная карамель", quantity=12.0, unit="бут"),
                    InvoiceItemOCR(raw_name="Молоко кокосовое", quantity=24.0, unit="шт"),
                    InvoiceItemOCR(raw_name="Порошок Манго", quantity=5.0, unit="уп"),
                ],
            )

        if provider == "gemini":
            if not gemini_key:
                raise OCRConfigurationError(
                    "OCR_PROVIDER=gemini requires GEMINI_API_KEY (or AI_API_KEY)"
                )
            raw_json_str = await cls._call_gemini_vision(
                image_bytes,
                gemini_key,
                settings.OCR_MODEL or "gemini-2.5-flash",
            )
        elif provider == "openai":
            if not openai_key:
                raise OCRConfigurationError(
                    "OCR_PROVIDER=openai requires OPENAI_API_KEY"
                )
            raw_json_str = await cls._call_openai_vision(
                image_bytes,
                openai_key,
                settings.OCR_MODEL or "gpt-4o-mini",
            )
        else:
            raise OCRConfigurationError(
                f"Unsupported OCR_PROVIDER={provider!r}; expected 'gemini' or 'openai'"
            )

        cleaned_text = cls._clean_json_response(raw_json_str)

        try:
            parsed_dict = json.loads(cleaned_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode LLM response as JSON: {cleaned_text}")
            raise ValueError(f"Vision LLM returned invalid JSON: {e}")

        try:
            validated = InvoiceOCRResponse.model_validate(parsed_dict)
            return validated
        except ValidationError as e:
            logger.error(f"Pydantic validation failed for OCR response: {e}")
            raise ValueError(f"Vision LLM response does not match expected schema: {e}")


# Global convenience function
async def parse_invoice_photo(image_bytes: bytes) -> dict:
    """Convenience function matching the interface specification."""
    result = await OCRService.parse_invoice_photo(image_bytes)
    return result.model_dump()
