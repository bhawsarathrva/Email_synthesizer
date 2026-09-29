import json
import re
import logging
from typing import Optional, List, Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from backend.app.config import settings
from backend.app.schemas.classification import ClassificationResult
from backend.app.agent.prompts import SYSTEM_CLASSIFICATION_PROMPT, generate_classification_user_prompt

logger = logging.getLogger("email_agent.classifier")


def get_llm():
    """Initializes and returns the configured LLM."""
    provider = settings.LLM_PROVIDER.lower()

    if provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.MODEL_NAME,
            temperature=0.1,
            format="json"
        )
    elif provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=settings.MODEL_NAME or "gemini-2.5-flash",
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.1
        )
    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=settings.MODEL_NAME or "gpt-4o-mini",
            api_key=settings.OPENAI_API_KEY,
            temperature=0.1
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


def _extract_json_from_text(text: str) -> dict:
    """Safely extracts JSON object from text even if surrounded by thoughts or code fences."""
    text = text.strip()
    # Check for markdown code blocks
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        text = match.group(1)
    else:
        # Search for first { to last }
        first_brace = text.find("{")
        last_brace = text.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            text = text[first_brace:last_brace + 1]

    return json.loads(text)


def classify_email_content(
    subject: str,
    body: str,
    sender: str = "",
    recipient: str = "",
    similar_examples: Optional[List[Dict[str, Any]]] = None
) -> ClassificationResult:
    """
    Directly classifies an email subject & body into Payroll, Benefits, or Tax.
    Returns a validated ClassificationResult.
    """
    llm = get_llm()
    system_msg = SystemMessage(content=SYSTEM_CLASSIFICATION_PROMPT)
    user_prompt = generate_classification_user_prompt(
        subject=subject,
        body=body,
        sender=sender,
        recipient=recipient,
        similar_examples=similar_examples
    )
    user_msg = HumanMessage(content=user_prompt)

    try:
        response = llm.invoke([system_msg, user_msg])
        content_str = response.content if hasattr(response, "content") else str(response)

        # Parse JSON
        parsed = _extract_json_from_text(content_str)

        # Normalize category
        cat = parsed.get("category", "").strip().capitalize()
        if cat not in ["Payroll", "Benefits", "Tax"]:
            # Fallback heuristic mapping if casing or prefix differed
            if "pay" in cat.lower() or "salary" in cat.lower():
                cat = "Payroll"
            elif "benefit" in cat.lower() or "health" in cat.lower() or "insur" in cat.lower():
                cat = "Benefits"
            elif "tax" in cat.lower() or "tds" in cat.lower() or "w-2" in cat.lower():
                cat = "Tax"
            else:
                cat = "Payroll"

        conf = float(parsed.get("confidence", 0.9))
        conf = max(0.0, min(1.0, conf))
        reason = parsed.get("reasoning", "Classified based on content analysis.")

        return ClassificationResult(
            category=cat,
            confidence=conf,
            reasoning=reason
        )

    except Exception as e:
        logger.error(f"Classification failed via LLM: {e}")
        # Rule-based fallback if LLM is temporarily unreachable
        content_lower = f"{subject} {body}".lower()
        if any(w in content_lower for w in ["tds", "tax", "w-2", "1099", "withholding", "deduction"]):
            return ClassificationResult(category="Tax", confidence=0.80, reasoning="Fallback classification based on tax keywords.")
        elif any(w in content_lower for w in ["insurance", "health", "dental", "vision", "benefit", "wellness", "401k"]):
            return ClassificationResult(category="Benefits", confidence=0.80, reasoning="Fallback classification based on benefits keywords.")
        else:
            return ClassificationResult(category="Payroll", confidence=0.80, reasoning="Fallback classification based on payroll keywords.")
