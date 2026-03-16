"""
model.py — Prophet-based Pod Resource Predictor & Recommendation Engine

This module provides:
  1. Metrics preprocessing (JSON → pandas DataFrames)
  2. Time-series forecasting using Facebook Prophet for CPU and memory
  3. Actionable recommendations (scale up/down, relocation, merge/split)

All thresholds are configurable via environment variables.
"""

import os
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

import pandas as pd
import numpy as np
from prophet import Prophet

# ──────────────────────────────────────────────────────────────────────
# Configuration from environment variables (with sane defaults)
# ──────────────────────────────────────────────────────────────────────
PREDICTION_HORIZON = int(os.environ.get("PREDICTION_HORIZON_MINUTES", "30"))
CPU_HIGH           = float(os.environ.get("CPU_HIGH_THRESHOLD", "0.80"))
CPU_LOW            = float(os.environ.get("CPU_LOW_THRESHOLD", "0.10"))
MEM_HIGH           = float(os.environ.get("MEMORY_HIGH_THRESHOLD", "0.85"))
MEM_LOW            = float(os.environ.get("MEMORY_LOW_THRESHOLD", "0.10"))
CONFIDENCE_THRESH  = float(os.environ.get("CONFIDENCE_THRESHOLD", "0.70"))
LOG_LEVEL          = os.environ.get("LOG_LEVEL", "INFO")

# Logger setup
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("pod-predictor")


# ──────────────────────────────────────────────────────────────────────
# 1. Metrics Preprocessing
# ──────────────────────────────────────────────────────────────────────
def preprocess_metrics(raw: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
    """
    Convert raw JSON metrics into per-pod DataFrames.

    Expected input format:
    {
      "pods": {
        "pod_name": [
          {"timestamp": "2026-02-17T10:00:00Z", "cpu": 0.5, "memory": 0.4},
          ...
        ],
        ...
      }
    }

    Returns:
        Dict mapping pod_name → DataFrame with columns [ds, cpu, memory]
    """
    pods_data = raw.get("pods", {})
    result = {}

    for pod_name, samples in pods_data.items():
        if not samples:
            logger.warning("Pod '%s' has no metric samples, skipping", pod_name)
            continue

        df = pd.DataFrame(samples)

        # Parse timestamps into datetime (strip timezone — Prophet requires tz-naive)
        df["ds"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce").dt.tz_localize(None)
        df = df.dropna(subset=["ds"])

        # Ensure cpu and memory are numeric, fill missing with 0
        df["cpu"] = pd.to_numeric(df.get("cpu", 0), errors="coerce").fillna(0.0)
        df["memory"] = pd.to_numeric(df.get("memory", 0), errors="coerce").fillna(0.0)

        # Sort by time and remove duplicates
        df = df.sort_values("ds").drop_duplicates(subset=["ds"]).reset_index(drop=True)

        # Need at least 2 data points for Prophet
        if len(df) < 2:
            logger.warning("Pod '%s' has fewer than 2 samples, skipping", pod_name)
            continue

        result[pod_name] = df[["ds", "cpu", "memory"]]
        logger.info("Preprocessed %d samples for pod '%s'", len(df), pod_name)

    return result


# ──────────────────────────────────────────────────────────────────────
# 2. Prophet Forecasting
# ──────────────────────────────────────────────────────────────────────
def _fit_and_predict(
    df: pd.DataFrame, column: str, horizon_minutes: int
) -> Tuple[pd.DataFrame, float]:
    """
    Fit a Prophet model on one metric column and return forecasts.

    Args:
        df:              DataFrame with 'ds' and the target column
        column:          'cpu' or 'memory'
        horizon_minutes: how many minutes ahead to forecast

    Returns:
        (forecast_df, confidence)
        forecast_df has columns [ds, yhat, yhat_lower, yhat_upper]
        confidence is 1 - (mean_interval_width / mean_predicted_value)
    """
    # Prophet expects columns 'ds' and 'y'
    prophet_df = df[["ds"]].copy()
    prophet_df["y"] = df[column].values

    # Suppress Prophet's verbose output
    model = Prophet(
        yearly_seasonality=False,
        weekly_seasonality=False,
        daily_seasonality=True,
        changepoint_prior_scale=0.05,
    )
    model.fit(prophet_df)

    # Build future dataframe
    future = model.make_future_dataframe(periods=horizon_minutes, freq="min")
    forecast = model.predict(future)

    # Only keep the forecasted (future) rows
    last_ts = prophet_df["ds"].max()
    forecast_future = forecast[forecast["ds"] > last_ts][
        ["ds", "yhat", "yhat_lower", "yhat_upper"]
    ].copy()

    # Clamp predictions to [0, 1] range (they represent fractions)
    for col in ["yhat", "yhat_lower", "yhat_upper"]:
        forecast_future[col] = forecast_future[col].clip(0.0, 1.0)

    # Calculate confidence: narrower interval = higher confidence
    interval_width = (forecast_future["yhat_upper"] - forecast_future["yhat_lower"]).mean()
    mean_pred = forecast_future["yhat"].mean()
    if mean_pred > 0:
        confidence = max(0.0, min(1.0, 1.0 - (interval_width / (2 * max(mean_pred, 0.01)))))
    else:
        confidence = 0.5  # default when prediction is near zero

    return forecast_future, round(confidence, 3)


def forecast_pod(
    pod_name: str, df: pd.DataFrame, horizon: int = PREDICTION_HORIZON
) -> Dict[str, Any]:
    """
    Run Prophet forecasts for both CPU and memory of a single pod.

    Returns dict with predictions and metadata.
    """
    logger.info("Forecasting pod '%s' (%d min horizon)", pod_name, horizon)
    result = {"pod": pod_name, "horizon_minutes": horizon}

    try:
        cpu_forecast, cpu_conf = _fit_and_predict(df, "cpu", horizon)
        cpu_forecast["ds"] = cpu_forecast["ds"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        result["cpu"] = {
            "predicted_mean": round(float(cpu_forecast["yhat"].mean()), 4),
            "predicted_max": round(float(cpu_forecast["yhat"].max()), 4),
            "predicted_min": round(float(cpu_forecast["yhat"].min()), 4),
            "confidence": cpu_conf,
            "forecast": cpu_forecast.to_dict(orient="records"),
        }
    except Exception as exc:
        logger.error("CPU forecast failed for '%s': %s", pod_name, exc)
        result["cpu"] = {"error": str(exc)}

    try:
        mem_forecast, mem_conf = _fit_and_predict(df, "memory", horizon)
        mem_forecast["ds"] = mem_forecast["ds"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        result["memory"] = {
            "predicted_mean": round(float(mem_forecast["yhat"].mean()), 4),
            "predicted_max": round(float(mem_forecast["yhat"].max()), 4),
            "predicted_min": round(float(mem_forecast["yhat"].min()), 4),
            "confidence": mem_conf,
            "forecast": mem_forecast.to_dict(orient="records"),
        }
    except Exception as exc:
        logger.error("Memory forecast failed for '%s': %s", pod_name, exc)
        result["memory"] = {"error": str(exc)}

    return result


# ──────────────────────────────────────────────────────────────────────
# 3. Recommendation Engine
# ──────────────────────────────────────────────────────────────────────
def generate_recommendations(
    forecasts: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Produce actionable recommendations based on forecasted values.

    For each pod we check:
      - CPU predicted above CPU_HIGH  → recommend CPU increase
      - CPU predicted below CPU_LOW   → recommend CPU decrease
      - Memory predicted above MEM_HIGH → recommend memory increase
      - Memory predicted below MEM_LOW  → recommend memory decrease

    Optional:
      - Pod relocation if one node is predicted to be overloaded
      - Service merge if multiple pods have very low usage

    Returns list of recommendation dicts.
    """
    recommendations = []
    low_usage_pods = []  # track pods with low usage for merge suggestions

    for fc in forecasts:
        pod = fc["pod"]

        # ── CPU recommendations ──
        cpu_data = fc.get("cpu", {})
        if "error" not in cpu_data:
            cpu_mean = cpu_data.get("predicted_mean", 0)
            cpu_max = cpu_data.get("predicted_max", 0)
            cpu_conf = cpu_data.get("confidence", 0)

            if cpu_max > CPU_HIGH and cpu_conf >= CONFIDENCE_THRESH:
                recommendations.append({
                    "pod": pod,
                    "type": "cpu_increase",
                    "action": "Increase CPU request/limit",
                    "reason": (
                        f"Predicted CPU peak of {cpu_max:.1%} exceeds "
                        f"threshold of {CPU_HIGH:.0%} within "
                        f"{fc['horizon_minutes']} minutes"
                    ),
                    "predicted_value": cpu_max,
                    "threshold": CPU_HIGH,
                    "confidence": cpu_conf,
                    "suggested_increase_pct": min(
                        100, int((cpu_max - CPU_HIGH) / CPU_HIGH * 100) + 20
                    ),
                })

            elif cpu_mean < CPU_LOW and cpu_conf >= CONFIDENCE_THRESH:
                recommendations.append({
                    "pod": pod,
                    "type": "cpu_decrease",
                    "action": "Decrease CPU request/limit",
                    "reason": (
                        f"Predicted CPU average of {cpu_mean:.1%} is below "
                        f"threshold of {CPU_LOW:.0%} — resources are wasted"
                    ),
                    "predicted_value": cpu_mean,
                    "threshold": CPU_LOW,
                    "confidence": cpu_conf,
                    "suggested_decrease_pct": min(
                        50, int((CPU_LOW - cpu_mean) / CPU_LOW * 100)
                    ),
                })
                low_usage_pods.append(pod)

        # ── Memory recommendations ──
        mem_data = fc.get("memory", {})
        if "error" not in mem_data:
            mem_mean = mem_data.get("predicted_mean", 0)
            mem_max = mem_data.get("predicted_max", 0)
            mem_conf = mem_data.get("confidence", 0)

            if mem_max > MEM_HIGH and mem_conf >= CONFIDENCE_THRESH:
                recommendations.append({
                    "pod": pod,
                    "type": "memory_increase",
                    "action": "Increase memory request/limit",
                    "reason": (
                        f"Predicted memory peak of {mem_max:.1%} exceeds "
                        f"threshold of {MEM_HIGH:.0%} within "
                        f"{fc['horizon_minutes']} minutes"
                    ),
                    "predicted_value": mem_max,
                    "threshold": MEM_HIGH,
                    "confidence": mem_conf,
                    "suggested_increase_pct": min(
                        100, int((mem_max - MEM_HIGH) / MEM_HIGH * 100) + 20
                    ),
                })

            elif mem_mean < MEM_LOW and mem_conf >= CONFIDENCE_THRESH:
                recommendations.append({
                    "pod": pod,
                    "type": "memory_decrease",
                    "action": "Decrease memory request/limit",
                    "reason": (
                        f"Predicted memory average of {mem_mean:.1%} is below "
                        f"threshold of {MEM_LOW:.0%} — resources are wasted"
                    ),
                    "predicted_value": mem_mean,
                    "threshold": MEM_LOW,
                    "confidence": mem_conf,
                    "suggested_decrease_pct": min(
                        50, int((MEM_LOW - mem_mean) / MEM_LOW * 100)
                    ),
                })
                if pod not in low_usage_pods:
                    low_usage_pods.append(pod)

    # ── Optional: Node relocation suggestions ──
    # If multiple pods on the same forecast have high CPU+memory,
    # suggest spreading them across nodes.
    high_load_pods = [
        fc["pod"]
        for fc in forecasts
        if fc.get("cpu", {}).get("predicted_max", 0) > CPU_HIGH
        and fc.get("memory", {}).get("predicted_max", 0) > MEM_HIGH
    ]
    if len(high_load_pods) >= 2:
        recommendations.append({
            "pod": ", ".join(high_load_pods),
            "type": "relocation",
            "action": "Consider relocating pods to balance node load",
            "reason": (
                f"{len(high_load_pods)} pods are predicted to have high "
                f"CPU and memory usage simultaneously — spreading them "
                f"across different nodes would improve stability"
            ),
            "affected_pods": high_load_pods,
            "confidence": 0.75,
        })

    # ── Optional: Service merge suggestion ──
    # If 3+ pods all have very low usage, suggest merging workloads
    if len(low_usage_pods) >= 3:
        recommendations.append({
            "pod": ", ".join(low_usage_pods),
            "type": "merge_suggestion",
            "action": "Consider merging low-usage workloads",
            "reason": (
                f"{len(low_usage_pods)} pods have consistently low resource "
                f"usage — consolidating them could save cluster resources"
            ),
            "affected_pods": low_usage_pods,
            "confidence": 0.60,
        })

    # ── Sort by confidence (highest first) ──
    recommendations.sort(key=lambda r: r.get("confidence", 0), reverse=True)

    logger.info(
        "Generated %d recommendations for %d pods",
        len(recommendations),
        len(forecasts),
    )
    return recommendations


# ──────────────────────────────────────────────────────────────────────
# 4. Main Pipeline (used by inference.py)
# ──────────────────────────────────────────────────────────────────────
def run_prediction_pipeline(raw_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    End-to-end pipeline: preprocess → forecast → recommend.

    Args:
        raw_input: JSON body matching the expected schema

    Returns:
        Dict with forecasts and recommendations
    """
    logger.info("Starting prediction pipeline")
    start_time = datetime.utcnow()

    # Step 1: Preprocess
    pod_dataframes = preprocess_metrics(raw_input)
    if not pod_dataframes:
        return {
            "status": "error",
            "message": "No valid pod metrics found in input",
            "forecasts": [],
            "recommendations": [],
        }

    # Step 2: Forecast each pod
    forecasts = []
    for pod_name, df in pod_dataframes.items():
        try:
            fc = forecast_pod(pod_name, df)
            forecasts.append(fc)
        except Exception as exc:
            logger.error("Pipeline error for pod '%s': %s", pod_name, exc)
            forecasts.append({"pod": pod_name, "error": str(exc)})

    # Step 3: Generate recommendations
    recommendations = generate_recommendations(forecasts)

    elapsed = (datetime.utcnow() - start_time).total_seconds()
    logger.info("Pipeline completed in %.2f seconds", elapsed)

    return {
        "status": "ok",
        "processed_at": datetime.utcnow().isoformat() + "Z",
        "elapsed_seconds": round(elapsed, 2),
        "pod_count": len(pod_dataframes),
        "horizon_minutes": PREDICTION_HORIZON,
        "thresholds": {
            "cpu_high": CPU_HIGH,
            "cpu_low": CPU_LOW,
            "memory_high": MEM_HIGH,
            "memory_low": MEM_LOW,
            "confidence": CONFIDENCE_THRESH,
        },
        "forecasts": forecasts,
        "recommendations": recommendations,
    }
