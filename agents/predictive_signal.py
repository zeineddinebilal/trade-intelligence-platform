import json
from typing import Dict, Any
from agents.client import carbon_client
from agents.prompts import PREDICTIVE_SIGNAL_SYSTEM_PROMPT
from agents.schemas import PredictiveSignalOutput


def run_predictive_signal_agent(raw_payload: Dict[str, Any]) -> PredictiveSignalOutput:
    """Analyzes raw multi-source trade/regulatory/satellite payloads using gemini-4-carbon."""
    prompt_text = (
        "Analyze the following incoming trade intelligence feed payload and extract the structured "
        "predictive trade signal:\n\n"
        f"{json.dumps(raw_payload, indent=2, default=str)}"
    )
    return carbon_client.generate_structured(
        system_prompt=PREDICTIVE_SIGNAL_SYSTEM_PROMPT,
        contents=[prompt_text],
        response_schema=PredictiveSignalOutput,
        thinking_level="medium",
        temperature=0.1,
    )
