FROM tensorflow/tensorflow:2.13.0

WORKDIR /app

COPY . .

# =========================
# 🔹 SYSTEM DEPENDENCIES (FIXED)
# =========================
RUN apt-get update && apt-get install -y \
    ansible \
    git \
    docker.io \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# =========================
# 🔹 PYTHON DEPENDENCIES
# =========================
RUN pip install --no-cache-dir \
    numpy \
    scikit-learn \
    mlflow \
    requests \
    "jinja2<3.1"

# =========================
# 🔹 RUN APP
# =========================
CMD ["python", "main.py"]