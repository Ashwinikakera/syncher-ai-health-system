# ml_service/models/lstm.py

import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3" #suppress tensorflow 
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

import numpy as np
import joblib

import tensorflow as tf
tf.get_logger().setLevel("ERROR")
LSTM_MODEL_PATH  = "ml_service/saved_models/lstm_model.keras"
SCALER_PATH      = "ml_service/saved_models/lstm_scaler.pkl"
SEQUENCE_LENGTH  = 3   # how many past cycles to look at


def _generate_sequence_data(n_users: int = 100, cycles_per_user: int = 12):
    """
    Generates synthetic sequential cycle data to train LSTM.

    Each sample = sequence of SEQUENCE_LENGTH past cycles
    Each timestep features:
        [cycle_length, period_length, avg_pain, avg_stress, avg_sleep]

    Target = next cycle length
    """
    np.random.seed(42)

    X_all, y_all = [], []

    for _ in range(n_users):
        # Each user has a base cycle length with personal variation
        base_cycle  = np.random.normal(28, 3)
        stress_bias = np.random.uniform(0, 2)

        cycles = []
        for i in range(cycles_per_user):
            stress      = np.random.uniform(2, 9)
            sleep       = np.random.uniform(4, 9)
            pain        = np.random.uniform(1, 8)
            period_len  = np.random.normal(5, 1)
            cycle_len   = (
                base_cycle
                + (stress - 5) * 0.4
                - (sleep - 7)  * 0.3
                + stress_bias
                + np.random.normal(0, 1)
            )
            cycles.append([
                np.clip(cycle_len, 21, 45),
                np.clip(period_len, 2, 9),
                np.clip(pain, 1, 10),
                np.clip(stress, 1, 10),
                np.clip(sleep, 3, 10),
            ])

        # Build sequences
        cycles = np.array(cycles)
        for i in range(len(cycles) - SEQUENCE_LENGTH):
            X_all.append(cycles[i : i + SEQUENCE_LENGTH])
            y_all.append(cycles[i + SEQUENCE_LENGTH][0])  # next cycle_length

    return np.array(X_all), np.array(y_all)


def train_and_save():
    """Build, train, and save the LSTM model."""
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from tensorflow.keras.callbacks import EarlyStopping
    from sklearn.preprocessing import MinMaxScaler
    from sklearn.model_selection import train_test_split

    print("🔧 Training LSTM model...")

    X, y = _generate_sequence_data(n_users=150, cycles_per_user=12)

    # ── Scale features ────────────────────────────────────────────
    n_samples, seq_len, n_features = X.shape
    X_flat   = X.reshape(-1, n_features)
    scaler   = MinMaxScaler()
    X_scaled = scaler.fit_transform(X_flat).reshape(n_samples, seq_len, n_features)
    y_scaled = y / 45.0   # normalize target to 0–1

    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y_scaled, test_size=0.2, random_state=42
    )

    # ── Build LSTM ────────────────────────────────────────────────
    model = Sequential([
        LSTM(64, input_shape=(seq_len, n_features), return_sequences=True),
        Dropout(0.2),
        LSTM(32, return_sequences=False),
        Dropout(0.2),
        Dense(16, activation="relu"),
        Dense(1),
    ])

    model.compile(optimizer="adam", loss="mse", metrics=["mae"])

    early_stop = EarlyStopping(
        monitor="val_loss", patience=5, restore_best_weights=True
    )

    print("  Training in progress...")
    model.fit(
        X_train, y_train,
        epochs=50,
        batch_size=16,
        validation_split=0.1,
        callbacks=[early_stop],
        verbose=0,
    )

    # ── Evaluate ──────────────────────────────────────────────────
    _, mae = model.evaluate(X_test, y_test, verbose=0)
    mae_days = mae * 45.0
    print(f"  ✅ LSTM trained — MAE: {mae_days:.2f} days")

    # ── Save model + scaler ───────────────────────────────────────
    os.makedirs("ml_service/saved_models", exist_ok=True)
    model.save(LSTM_MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    print(f"  ✅ LSTM saved  → {LSTM_MODEL_PATH}")
    print(f"  ✅ Scaler saved → {SCALER_PATH}")

    return model, scaler


def load_lstm():
    """Load LSTM model + scaler from disk. Train fresh if not found."""
    from tensorflow.keras.models import load_model

    if not os.path.exists(LSTM_MODEL_PATH) or not os.path.exists(SCALER_PATH):
        print("  ⚠️  No saved LSTM found — training fresh...")
        return train_and_save()

    model  = load_model(LSTM_MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    print(f"  ✅ LSTM loaded from {LSTM_MODEL_PATH}")
    return model, scaler


def predict_with_lstm(model, scaler, cycle_records: list) -> tuple[float, float]:
    """
    Predict next cycle length using LSTM.

    Args:
        model:          trained Keras LSTM model
        scaler:         fitted MinMaxScaler
        cycle_records:  list of raw cycle dicts (needs at least 3)

    Returns:
        (predicted_cycle_length, confidence_score)
    """
    from ml_service.preprocessing.cleaning import clean_cycle_data

    df = clean_cycle_data(cycle_records)

    required_cols = ["cycle_length", "period_length"]
    for col in required_cols:
        if col not in df.columns:
            df[col] = 28 if col == "cycle_length" else 5

    # Fill symptom columns with neutral defaults if not present
    for col, default in [("avg_pain", 3.0), ("avg_stress", 4.0), ("avg_sleep", 7.0)]:
        if col not in df.columns:
            df[col] = default

    # Build sequence — use last SEQUENCE_LENGTH cycles
    sequence_data = df[["cycle_length", "period_length",
                         "avg_pain", "avg_stress", "avg_sleep"]].tail(SEQUENCE_LENGTH)

    # Pad with mean values if fewer than SEQUENCE_LENGTH cycles
    while len(sequence_data) < SEQUENCE_LENGTH:
        mean_row = sequence_data.mean()
        sequence_data = sequence_data._append(mean_row, ignore_index=True)

    # Scale
    X_flat   = sequence_data.values
    X_scaled = scaler.transform(X_flat).reshape(1, SEQUENCE_LENGTH, X_flat.shape[1])

    # Predict
    y_pred_scaled = model.predict(X_scaled, verbose=0)[0][0]
    predicted_length = float(y_pred_scaled * 45.0)
    predicted_length = round(max(21.0, min(45.0, predicted_length)), 1)

    # Confidence: based on how consistent the input sequence is
    std = float(sequence_data["cycle_length"].std())
    confidence = round(max(0.0, 1.0 - (std / 14.0)), 2)  # 14 = max expected std

    return predicted_length, confidence