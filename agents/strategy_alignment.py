import json
from typing import Dict, Any
from agents.client import carbon_client
from agents.prompts import STRATEGY_ALIGNMENT_SYSTEM_PROMPT
from agents.schemas import FactCheckOutput, PredictiveSignalOutput, StrategyAlignmentOutput


def run_strategy_alignment_agent(
    stakeholder_profile: Dict[str, Any],
    signal: PredictiveSignalOutput,
    verification: FactCheckOutput,
) -> StrategyAlignmentOutput:
    """Scores verified signal alignment (0-100) against the Ministry's configured strategic profile."""
    payload = {
        "stakeholder_configuration": stakeholder_profile,
        "verified_signal": signal.model_dump(),
        "verification_summary": verification.model_dump(),
    }
    return carbon_client.generate_structured(
        system_prompt=STRATEGY_ALIGNMENT_SYSTEM_PROMPT,
        contents=[f"Evaluate strategic alignment for this Ministry:\n\n{json.dumps(payload, indent=2, default=str)}"],
        response_schema=StrategyAlignmentOutput,
        thinking_level="low",
        temperature=0.1,
    )
