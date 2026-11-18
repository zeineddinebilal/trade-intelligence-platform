import json
from typing import Any, Dict, List
from agents.client import carbon_client
from agents.prompts import OPPORTUNITY_SYNTHESIS_SYSTEM_PROMPT
from agents.schemas import (
    FactCheckOutput,
    OpportunitySynthesisOutput,
    PredictiveSignalOutput,
    StrategyAlignmentOutput,
)


def run_opportunity_synthesis_agent(
    stakeholder_profile: Dict[str, Any],
    signal: PredictiveSignalOutput,
    verification: FactCheckOutput,
    alignment: StrategyAlignmentOutput,
    market_context: Dict[str, Any],
    satellite_observations: List[Dict[str, Any]],
) -> OpportunitySynthesisOutput:
    """Synthesizes an executive ministerial brief using gemini-4-carbon with thinking_level='high'."""
    synthesis_context = {
        "stakeholder_ministry": stakeholder_profile,
        "predictive_signal": signal.model_dump(),
        "multimodal_fact_check": verification.model_dump(),
        "strategy_alignment": alignment.model_dump(),
        "trade_flows_freight_and_fx_context": market_context,
        "satellite_observations": satellite_observations,
    }
    return carbon_client.generate_structured(
        system_prompt=OPPORTUNITY_SYNTHESIS_SYSTEM_PROMPT,
        contents=[
            "Generate the structured executive trade opportunity brief (<= 600 words Markdown) "
            f"from this verified intelligence package:\n\n{json.dumps(synthesis_context, indent=2, default=str)}"
        ],
        response_schema=OpportunitySynthesisOutput,
        thinking_level="high",
        temperature=0.2,
    )
