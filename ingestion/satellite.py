from typing import List, Dict, Any


def enrich_agricultural_satellite_metrics(raw_text: str) -> List[Dict[str, Any]]:
    """
    Satellite Earth-Observation hook (Sentinel-2 L2A / PlanetScope / MODIS NDVI & NDWI).

    WARNING: this is a STUB. It returns fixed placeholder telemetry based on keywords, NOT real
    imagery analysis. Every record is tagged "data_status": "SIMULATED_PLACEHOLDER" and labelled
    "[SIMULATED]" so neither the agents nor dashboard users mistake it for real observations.
    Replace with a real EO pipeline (e.g., Copernicus Data Space / Sentinel Hub statistics API).
    """
    lowered = raw_text.lower()
    if any(k in lowered for k in ["shrimp", "prawn", "aquaculture", "pond"]):
        return [
            {
                "data_status": "SIMULATED_PLACEHOLDER",
                "provider": "[SIMULATED] Sentinel-2 L2A",
                "region_name": "[SIMULATED] Coastal Aquaculture Belt - Primary Supplier Delta",
                "bbox": [79.82, 14.10, 82.45, 16.95],
                "metric_type": "ACTIVE_AERATION_AND_NDWI_POND_RATIO",
                "metric_value": 0.61,
                "baseline_delta_pct": -19.4,
                "cloud_cover_pct": 8.2,
                "imagery_confidence": 0.0,
                "preview_image_url": None,
            }
        ]
    if any(k in lowered for k in ["dairy", "milk", "pasture", "drought", "grain", "wheat"]):
        return [
            {
                "data_status": "SIMULATED_PLACEHOLDER",
                "provider": "[SIMULATED] Landsat-9 / Sentinel-2 HLS",
                "region_name": "[SIMULATED] Temperate Dairy & Forage Basin",
                "bbox": [172.10, -43.90, 176.80, -37.50],
                "metric_type": "PASTURE_NDVI_ANOMALY",
                "metric_value": 0.42,
                "baseline_delta_pct": -24.7,
                "cloud_cover_pct": 4.5,
                "imagery_confidence": 0.0,
                "preview_image_url": None,
            }
        ]
    return []
