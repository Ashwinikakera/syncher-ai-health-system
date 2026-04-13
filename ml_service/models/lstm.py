"""
ml_service/models/lstm.py
LSTM model for cycle-length prediction using sequential cycle history.
Uses TensorFlow/Keras. Falls back to regression if model not available.

FIX:
  predict_confidence: changed variance divisor from 80.0 → 100.0 to match
  regression.py, so confidence is consistent regardless of which model fires.
  With 80.0, the same user with variance=40 got LSTM conf=0.55 but
  regression conf=0.60 — inconsistent dashboard display.
"""

import logging
import pickle
from pathlib import Path
from typing import Optional, Tuple

import numpy as np

from config import (
    LSTM_MODEL_PATH, LSTM_SCALER_PATH,
    LSTM_SEQUENCE_LEN, LSTM_EPOCHS, LSTM_BATCH_SIZE, LSTM_UNITS,
    FEATURE_COLUMNS,
)

logger = logging.getLogger(__name__)

try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential, load_model
    from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
    from tensorflow.keras.optimizers import Adam
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    logger.warning("TensorFlow not installed. LSTM model unavailable.")


class CycleLSTMModel:
    """
    LSTM model that predicts next cycle length from a sequence of past cycles.
    Input shape:  (batch, LSTM_SEQUENCE_LEN, n_features)
    Output shape: (batch, 1) — next cycle length in days
    """

    def __init__(self):
        self.model:      Optional[object] = None
        self.scaler:     Optional[object] = None
        self.is_trained: bool = False
        self.n_features: int  = len(FEATURE_COLUMNS)
        self._load()

    # ─── Persistence ──────────────────────────────────────────────────────────

    def _load(self):
        if not TF_AVAILABLE:
            return
        model_path  = Path(LSTM_MODEL_PATH)
        scaler_path = Path(LSTM_SCALER_PATH)

        if model_path.exists() and scaler_path.exists():
            try:
                self.model = load_model(str(model_path))
                with open(scaler_path, "rb") as f:
                    self.scaler = pickle.load(f)
                self.is_trained = True
                logger.info("LSTM model loaded from %s", model_path)
            except Exception as exc:
                logger.warning("Failed to load LSTM model: %s", exc)
                self.model      = None
                self.scaler     = None
                self.is_trained = False

    def save(self):
        if not TF_AVAILABLE or self.model is None:
            return
        Path(LSTM_MODEL_PATH).parent.mkdir(exist_ok=True)
        self.model.save(str(LSTM_MODEL_PATH))
        with open(LSTM_SCALER_PATH, "wb") as f:
            pickle.dump(self.scaler, f)
        logger.info("LSTM model saved.")

    # ─── Architecture ─────────────────────────────────────────────────────────

    def _build_model(self) -> "Sequential":
        model = Sequential([
            LSTM(LSTM_UNITS, input_shape=(LSTM_SEQUENCE_LEN, self.n_features),
                 return_sequences=True),
            BatchNormalization(),
            Dropout(0.2),
            LSTM(LSTM_UNITS // 2, return_sequences=False),
            BatchNormalization(),
            Dropout(0.2),
            Dense(32, activation="relu"),
            Dense(1,  activation="linear"),
        ])
        model.compile(
            optimizer=Adam(learning_rate=1e-3),
            loss="huber",
            metrics=["mae"],
        )
        return model

    # ─── Training ─────────────────────────────────────────────────────────────

    def train(
        self,
        X: np.ndarray,   # (n_samples, seq_len, n_features)
        y: np.ndarray,   # (n_samples,)
    ) -> dict:
        """
        Trains (or retrains) the LSTM model.
        X must already be shaped (samples, LSTM_SEQUENCE_LEN, n_features).
        """
        if not TF_AVAILABLE:
            raise RuntimeError("TensorFlow is required to train the LSTM model.")

        from sklearn.preprocessing import MinMaxScaler

        n_samples, seq_len, n_feat = X.shape
        X_flat   = X.reshape(-1, n_feat)
        self.scaler = MinMaxScaler()
        X_scaled = self.scaler.fit_transform(X_flat).reshape(n_samples, seq_len, n_feat)

        y_scaled = (y - 21.0) / (45.0 - 21.0)

        self.model = self._build_model()

        callbacks = [
            EarlyStopping(monitor="val_loss", patience=8, restore_best_weights=True),
            ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=4, min_lr=1e-6),
        ]

        val_split = 0.2 if len(X) >= 10 else 0.0

        history = self.model.fit(
            X_scaled, y_scaled,
            epochs=LSTM_EPOCHS,
            batch_size=LSTM_BATCH_SIZE,
            validation_split=val_split,
            callbacks=callbacks,
            verbose=0,
        )

        self.is_trained = True
        self.save()

        y_pred_scaled = self.model.predict(X_scaled, verbose=0).flatten()
        y_pred = y_pred_scaled * (45.0 - 21.0) + 21.0
        mae    = float(np.mean(np.abs(y - y_pred)))
        rmse   = float(np.sqrt(np.mean((y - y_pred) ** 2)))

        logger.info("LSTM trained — MAE=%.2f RMSE=%.2f", mae, rmse)
        return {"mae": mae, "rmse": rmse}

    # ─── Inference ────────────────────────────────────────────────────────────

    def predict_cycle_length(self, sequence: np.ndarray) -> Optional[float]:
        """
        sequence shape: (1, LSTM_SEQUENCE_LEN, n_features)
        Returns next cycle length (days) or None.
        """
        if not self.is_trained or self.model is None or self.scaler is None:
            logger.warning("LSTM model not trained. Cannot predict.")
            return None
        if not TF_AVAILABLE:
            return None

        try:
            _, seq_len, n_feat = sequence.shape
            seq_flat    = sequence.reshape(-1, n_feat)
            seq_scaled  = self.scaler.transform(seq_flat).reshape(1, seq_len, n_feat)
            pred_scaled = float(self.model.predict(seq_scaled, verbose=0)[0][0])
            pred        = pred_scaled * (45.0 - 21.0) + 21.0
            return float(np.clip(pred, 21.0, 45.0))
        except Exception as exc:
            logger.error("LSTM predict failed: %s", exc)
            return None

    def predict_confidence(self, feature_vector: np.ndarray) -> float:
        """
        Confidence based on cycle_variance from the last step of the sequence.

        FIX: divisor changed from 80.0 → 100.0 to match regression.py,
        ensuring consistent confidence values across models for same user data.
        """
        if not self.is_trained:
            return 0.5
        try:
            var_idx  = FEATURE_COLUMNS.index("cycle_variance")
            variance = float(feature_vector.flatten()[-len(FEATURE_COLUMNS) + var_idx])
            # FIX: was 80.0, now 100.0 — unified with regression.py
            return round(max(0.55, min(0.95, 1.0 - (variance / 100.0))), 2)
        except Exception:
            return 0.65