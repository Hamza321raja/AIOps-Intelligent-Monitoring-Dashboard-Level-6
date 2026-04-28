import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import tensorflow as tf
import mlflow
import logging
from collections import deque
from config import MLFLOW_TRACKING_URI

# =========================
# LOGGING
# =========================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("aiops-ml")

# =========================
# MLFLOW
# =========================
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

# =========================
# STATE
# =========================
history = deque(maxlen=200)

scaler = StandardScaler()
iso_model = IsolationForest(contamination=0.1, random_state=42)
cluster_model = KMeans(n_clusters=3, n_init=10)

# 🔥 Time-aware model (sequence-based)
tf_model = tf.keras.Sequential([
    tf.keras.layers.Dense(32, activation='relu', input_shape=(5,)),
    tf.keras.layers.Dense(16, activation='relu'),
    tf.keras.layers.Dense(1)
])

tf_model.compile(optimizer='adam', loss='mse')

trained = False
mlflow_run_active = False
last_train_size = 0


# =========================
# 🔹 FEATURE ENGINEERING
# =========================
def build_features(X):
    features = []

    for i in range(2, len(X)):
        cpu = X[i][0]
        latency = X[i][1]
        req = X[i][2]

        # 🔥 derived features
        cpu_trend = X[i][0] - X[i-1][0]
        latency_trend = X[i][1] - X[i-1][1]

        features.append([cpu, latency, req, cpu_trend, latency_trend])

    return np.array(features)


# =========================
# 🔹 TRAINING
# =========================
def train():
    global trained, mlflow_run_active, last_train_size

    if len(history) < 60:
        logger.info("Not enough data for training")
        return

    # 🔥 avoid retraining too frequently
    if len(history) - last_train_size < 20:
        return

    X_raw = np.array(history)
    X = build_features(X_raw)

    if len(X) < 20:
        return

    try:
        X_scaled = scaler.fit_transform(X)

        # Train anomaly + clustering
        iso_model.fit(X_scaled)
        cluster_model.fit(X_scaled)

        # 🔥 TRUE PREDICTION TARGET (next-step CPU)
        y = X[1:, 0]  # future CPU
        X_train = X_scaled[:-1]

        tf_model.fit(X_train, y, epochs=5, verbose=0)

        trained = True
        last_train_size = len(history)

        if not mlflow_run_active:
            mlflow.start_run()
            mlflow_run_active = True

        mlflow.log_metric("training_samples", len(X))
        mlflow.log_metric("avg_cpu", float(np.mean(y)))

        logger.info("Models trained successfully")

    except Exception as e:
        logger.error(f"Training error: {e}")


# =========================
# 🔹 ANOMALY DETECTION
# =========================
def detect(x):
    history.append(x)

    train()

    if not trained:
        return False, 0.0

    try:
        X = build_features(np.array(history))

        if len(X) < 1:
            return False, 0.0

        x_scaled = scaler.transform([X[-1]])

        score = iso_model.decision_function(x_scaled)[0]
        anomaly = iso_model.predict(x_scaled)[0] == -1

        return anomaly, float(score)

    except Exception as e:
        logger.error(f"Detection error: {e}")
        return False, 0.0


# =========================
# 🔹 PATTERN RECOGNITION
# =========================
def pattern(x):
    if not trained:
        return "UNKNOWN"

    try:
        X = build_features(np.array(history))
        x_scaled = scaler.transform([X[-1]])
        cluster = cluster_model.predict(x_scaled)[0]

        return f"CLUSTER_{cluster}"

    except Exception as e:
        logger.error(f"Pattern error: {e}")
        return "UNKNOWN"


# =========================
# 🔹 FAILURE PREDICTION (REAL)
# =========================
def predict_failure(x):
    if not trained:
        return "UNKNOWN"

    try:
        X = build_features(np.array(history))

        if len(X) < 2:
            return "UNKNOWN"

        x_scaled = scaler.transform([X[-1]])

        pred_cpu = tf_model.predict(x_scaled, verbose=0)[0][0]

        # 🔥 dynamic threshold
        cpu_hist = [h[0] for h in history]
        threshold = np.mean(cpu_hist) + 1.5 * np.std(cpu_hist)

        if pred_cpu > threshold:
            return "HIGH_RISK"

        return "NORMAL"

    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return "UNKNOWN"