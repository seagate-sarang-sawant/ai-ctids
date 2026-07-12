"""FastAPI application for AI-CTIDS threat detection.

Provides REST endpoints for real-time and batch threat prediction.
"""

import logging
import time
from typing import List

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse, PlainTextResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from pydantic import BaseModel

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from shared.schemas import (
    NetworkFlowEvent,
    PredictionEvent,
    BatchPredictionRequest,
    BatchPredictionResponse
)
from shared.config import settings
from predictor import ThreatPredictor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI-CTIDS Inference API",
    description="Real-time cyber threat detection and classification",
    version="1.0.0"
)

# Global predictor instance
predictor: ThreatPredictor = None


@app.on_event("startup")
async def startup_event():
    """Initialize model on startup."""
    global predictor
    logger.info("Starting AI-CTIDS Inference API")
    logger.info(f"Model: {settings.MODEL_NAME} v{settings.MODEL_VERSION}")

    try:
        predictor = ThreatPredictor()
        if predictor.is_ready:
            logger.info("Model loaded successfully - API ready")
        else:
            logger.warning("API started but model is not loaded. Train models and restart to enable predictions.")
    except Exception as e:
        logger.error(f"Failed to initialize predictor: {e}")
        # Don't raise - allow API to start for health checks and status queries
        predictor = None


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down AI-CTIDS Inference API")


@app.get("/", tags=["Info"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "AI-CTIDS Inference API",
        "version": "1.0.0",
        "model": settings.MODEL_NAME,
        "model_version": settings.MODEL_VERSION,
        "status": "running"
    }


@app.get("/healthz", tags=["Health"], status_code=status.HTTP_200_OK)
async def health_check():
    """Health check endpoint - returns 200 if service is alive."""
    return {"status": "healthy"}


@app.get("/readyz", tags=["Health"], status_code=status.HTTP_200_OK)
async def readiness_check():
    """Readiness check - returns 200 if service is ready to serve requests."""
    if predictor is None or not predictor.is_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not loaded - service not ready"
        )
    
    return {
        "status": "ready",
        "model": settings.MODEL_NAME,
        "model_version": settings.MODEL_VERSION
    }


@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """Prometheus metrics endpoint."""
    return PlainTextResponse(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@app.post("/predict", response_model=PredictionEvent, tags=["Prediction"])
async def predict_single(flow: NetworkFlowEvent):
    """Predict threat classification for a single network flow.
    
    Args:
        flow: Network flow event with features
    
    Returns:
        Prediction event with threat classification and confidence
    """
    if predictor is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not loaded"
        )
    
    try:
        prediction = predictor.predict_single(flow)
        return prediction
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )


@app.post("/predict/batch", response_model=BatchPredictionResponse, tags=["Prediction"])
async def predict_batch(request: BatchPredictionRequest):
    """Predict threat classification for multiple network flows.
    
    Args:
        request: Batch request containing list of network flows
    
    Returns:
        Batch response with predictions for all flows
    """
    if predictor is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not loaded"
        )
    
    try:
        start_time = time.time()
        predictions = predictor.predict_batch(request.flows)
        total_time_ms = (time.time() - start_time) * 1000
        
        response = BatchPredictionResponse(
            predictions=predictions,
            total_count=len(predictions),
            total_inference_time_ms=total_time_ms,
            average_inference_time_ms=total_time_ms / len(predictions)
        )
        
        return response
    except Exception as e:
        logger.error(f"Batch prediction failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch prediction failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        workers=settings.API_WORKERS,
        reload=settings.API_RELOAD
    )
