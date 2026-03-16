"""
inference.py — KServe InferenceService handler for Pod Resource Predictor

Exposes a REST API that accepts pod metrics and returns Prophet-based
forecasts with actionable recommendations.

Endpoints (provided by KServe / custom HTTP server):
  POST /v1/models/pod-predictor:predict
  POST /predict          (convenience shortcut)
  GET  /health           (liveness / readiness)
"""

import json
import logging
import os
from typing import Dict, Any

try:
    from kserve import Model, ModelServer
    KSERVE_AVAILABLE = True
except ImportError:
    KSERVE_AVAILABLE = False

from model import run_prediction_pipeline

logger = logging.getLogger("pod-predictor-inference")


# ──────────────────────────────────────────────────────────────────────
# KServe Model Handler
# ──────────────────────────────────────────────────────────────────────
if KSERVE_AVAILABLE:
    class PodPredictor(Model):
        """KServe-compatible model wrapper."""

        def __init__(self, name: str = "pod-predictor"):
            super().__init__(name)
            self.name = name
            self.ready = False
            self.load()

        def load(self):
            """Mark model as ready (Prophet trains on each request)."""
            logger.info("PodPredictor model loaded and ready")
            self.ready = True

        def predict(self, payload: Dict[str, Any], headers: dict = None) -> Dict[str, Any]:
            """
            Handle prediction request.

            Args:
                payload: JSON body with pod metrics:
                    {
                      "pods": {
                        "nginx-abc123": [
                          {"timestamp": "2026-02-17T10:00:00Z", "cpu": 0.5, "memory": 0.4},
                          {"timestamp": "2026-02-17T10:01:00Z", "cpu": 0.55, "memory": 0.42},
                          ...
                        ],
                        ...
                      }
                    }

            Returns:
                Prediction results with forecasts and recommendations.
            """
            logger.info("Received prediction request")
            try:
                result = run_prediction_pipeline(payload)
                return result
            except Exception as exc:
                logger.error("Prediction failed: %s", exc, exc_info=True)
                return {
                    "status": "error",
                    "message": str(exc),
                    "forecasts": [],
                    "recommendations": [],
                }

# ──────────────────────────────────────────────────────────────────────
# Fallback: standalone Flask server (when KServe is not installed)
# ──────────────────────────────────────────────────────────────────────
else:
    from http.server import HTTPServer, BaseHTTPRequestHandler

    class PredictorHandler(BaseHTTPRequestHandler):
        """Minimal HTTP handler for environments without KServe."""

        def do_GET(self):
            if self.path in (
                "/health",
                "/v1/models/pod-predictor",
                "/v2/health/ready",
                "/v2/health/live",
            ):
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "healthy"}).encode())
            else:
                self.send_response(404)
                self.end_headers()

        def do_POST(self):
            if self.path in ("/predict", "/v1/models/pod-predictor:predict"):
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length)
                try:
                    payload = json.loads(body)
                    result = run_prediction_pipeline(payload)
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(result, default=str).encode())
                except Exception as exc:
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(
                        json.dumps({"status": "error", "message": str(exc)}).encode()
                    )
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, format, *args):
            logger.info(format, *args)


# ──────────────────────────────────────────────────────────────────────
# Entry Point
# ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PREDICTOR_PORT", "8080"))

    if KSERVE_AVAILABLE:
        logger.info("Starting KServe ModelServer on port %d", port)
        model = PodPredictor()
        ModelServer(http_port=port).start([model])
    else:
        logger.info("KServe not available — starting standalone HTTP server on port %d", port)
        server = HTTPServer(("0.0.0.0", port), PredictorHandler)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            logger.info("Server stopped")
            server.server_close()
