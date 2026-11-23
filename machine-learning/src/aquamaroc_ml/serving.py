def unavailable_forecast() -> dict:
    return {
        "status": "insufficient_history",
        "predicted_storage_mm3": None,
        "prediction_interval_mm3": None,
        "model_name": None,
        "model_version": None,
        "disclaimer": "Aucune prévision validée disponible",
    }
