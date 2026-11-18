import json
from typing import Any, Dict, List
from agents.client import carbon_client
from agents.prompts import FACT_CHECKER_SYSTEM_PROMPT
from agents.schemas import FactCheckOutput, PredictiveSignalOutput


def run_multimodal_fact_checker(
    signal: PredictiveSignalOutput,
    raw_content: str,
    evidence_items: List[Dict[str, Any]],
    satellite_observations: List[Dict[str, Any]],
    corroborating_context: Dict[str, Any],
) -> FactCheckOutput:
    """
    Executes multi-modal verification on gemini-4-carbon (thinking_level='high'),
    attaching actual image/document bytes alongside Sentinel/Planet satellite telemetry.
    """
    textual_dossier = {
        "candidate_signal": signal.model_dump(),
        "raw_report_text": raw_content,
        "satellite_telemetry": satellite_observations,
        "attached_evidence_manifest": [
            {"modality": item.get("modality"), "caption": item.get("caption"), "uri": item.get("uri_or_path")}
            for item in evidence_items
        ],
        "corroborating_trade_and_regulatory_data": corroborating_context,
    }

    contents: List[Any] = [
        "Verify the candidate trade signal below using all primary data, satellite metrics, "
        "and any attached multi-modal image/document parts:\n\n"
        f"{json.dumps(textual_dossier, indent=2, default=str)}"
    ]

    # Attach visual document scans, customs charts, or satellite preview rasters directly for Gemini vision
    for item in evidence_items:
        uri = item.get("uri_or_path", "")
        mime = item.get("mime_type", "image/png")
        part = carbon_client.build_multimodal_part(uri_or_data=uri, mime_type=mime)
        if part is not None:
            contents.append(f"Attached Multi-Modal Evidence ({item.get('modality')}): {item.get('caption', '')}")
            contents.append(part)

    for sat in satellite_observations:
        preview_url = sat.get("preview_image_url")
        if preview_url:
            sat_part = carbon_client.build_multimodal_part(uri_or_data=preview_url, mime_type="image/png")
            if sat_part is not None:
                contents.append(
                    f"Satellite Imagery Raster ({sat.get('provider')} - {sat.get('region_name')} - {sat.get('metric_type')})"
                )
                contents.append(sat_part)

    return carbon_client.generate_structured(
        system_prompt=FACT_CHECKER_SYSTEM_PROMPT,
        contents=contents,
        response_schema=FactCheckOutput,
        thinking_level="high",
        temperature=0.1,
    )
