"""
ml_service/models/regression.py
Linear Regression wrapper for next-period-date prediction.
Trains on (feature_vector → days_to_next_period) pairs.
"""

import logging
import pickle
from pathlib import Path
from typing import Optional

import numpy as np
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import cross_val_score

from config import REGRESSION_MODEL_PATH, REGRESSION_MIN_CYCLES, FEATURE_COLUMNS

logger = logging.getLogger(__name__)


class CycleRegressionModel:
    """
    Wraps a sklearn Ridge Regression pipeline (Scaler + Ridge).
    Target = next cycle length in days.
    """

    def __init__(self):
        self.pipeline: Optional[Pipeline] = None
        self.is_trained: bool = False
        self._load()

    # ─── Persistence ──────────────────────────────────────────────────────────

    def _load(self):
        path = Path(REGRESSION_MODEL_PATH)
        if path.exists():
            try:
                with open(path, "rb") as f:
                    self.pipeline = pickle.load(f)
                self.is_trained = True
                logger.info("Regression model loaded from %s", path)
            except Exception as exc:
                logger.warning("Failed to load regression model: %s", exc)
                self.pipeline = None
                self.is_trained = False

    def save(self):
        path = Path(REGRESSION_MODEL_PATH)
        path.parent.mkdir(exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(self.pipeline, f)
        logger.info("Regression model saved to %s", path)

    # ─── Training ─────────────────────────────────────────────────────────────

    def train(self, X: np.ndarray, y: np.ndarray) -> dict:
        """
        Parameters
        ----------
        X : (n_samples, n_features) feature matrix
        y : (n_samples,) target = next cycle length in days

        Returns
        -------
        dict with mae, rmse, cv_mae
        """
        if len(X) < REGRESSION_MIN_CYCLES:
            raise ValueError(
                f"Need at least {REGRESSION_MIN_CYCLES} samples to train regression model. "
                f"Got {len(X)}."
            )

        self.pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("ridge",  Ridge(alpha=1.0)),
        ])
        self.pipeline.fit(X, y)
        self.is_trained = True

        y_pred = self.pipeline.predict(X)
        mae  = float(np.mean(np.abs(y - y_pred)))
        rmse = float(np.sqrt(np.mean((y - y_pred) ** 2)))

        # Cross-val only if enough samples
        cv_mae = None
        if len(X) >= 5:
            cv_scores = cross_val_score(
                self.pipeline, X, y,
                cv=min(5, len(X)),
                scoring="neg_mean_absolute_error",
            )
            cv_mae = float(-cv_scores.mean())

        self.save()
        logger.info("Regression trained — MAE=%.2f RMSE=%.2f CV_MAE=%s", mae, rmse, cv_mae)
        return {"mae": mae, "rmse": rmse, "cv_mae": cv_mae}

    # ─── Inference ────────────────────────────────────────────────────────────

    def predict_cycle_length(self, feature_vector: np.ndarray) -> Optional[float]:
        """
        Returns predicted next cycle length (days) or None if model untrained.
        feature_vector shape: (n_features,) or (1, n_features)
        """
        if not self.is_trained or self.pipeline is None:
            logger.warning("Regression model not trained. Cannot predict.")
            return None

        x = feature_vector.reshape(1, -1) if feature_vector.ndim == 1 else feature_vector
        pred = self.pipeline.predict(x)[0]
        # Clamp to physiological range
        return float(np.clip(pred, 21.0, 45.0))

    def predict_confidence(self, feature_vector: np.ndarray) -> float:
        """
        Heuristic confidence score based on cycle variance feature.
        Lower variance → higher confidence.
        Returns value in [0.5, 0.95].
        """
        if not self.is_trained:
            return 0.5
        try:
            var_idx = FEATURE_COLUMNS.index("cycle_variance")
            variance = float(feature_vector.flatten()[var_idx])
            # Confidence decays with variance; cap between 0.5 and 0.95
            confidence = max(0.5, min(0.95, 1.0 - (variance / 100.0)))
            return round(confidence, 2)
        except (ValueError, IndexError):
            return 0.6