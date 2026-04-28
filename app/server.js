// ===============================
// 🔥 1. OPENTELEMETRY (MUST BE FIRST)
// ===============================
const { NodeSDK } = require("@opentelemetry/sdk-node");
const { OTLPTraceExporter } = require("@opentelemetry/exporter-trace-otlp-http");
const { getNodeAutoInstrumentations } = require("@opentelemetry/auto-instrumentations-node");

// ✅ OTLP Collector endpoint
const traceExporter = new OTLPTraceExporter({
  url: "http://otel-collector:4318/v1/traces",
});

// ✅ Correct modern config
const sdk = new NodeSDK({
  traceExporter,
  instrumentations: [getNodeAutoInstrumentations()],
  serviceName: "aiops-engine", // supported in latest SDK
});

// Start OTEL BEFORE anything else
(async () => {
  try {
    await sdk.start();
    console.log("✅ OpenTelemetry started");
  } catch (err) {
    console.error("❌ OTEL failed", err);
  }
})();

// ===============================
// 🔥 2. IMPORTS
// ===============================
const express = require("express");
const client = require("prom-client");

// ===============================
// 🔥 3. APP SETUP
// ===============================
const app = express();
app.use(express.json());

// ===============================
// 🔥 4. PROMETHEUS METRICS
// ===============================
client.collectDefaultMetrics();

const httpRequestCounter = new client.Counter({
  name: "http_requests_total",
  help: "Total HTTP requests",
  labelNames: ["method", "route", "status"],
});

const httpRequestDuration = new client.Histogram({
  name: "http_request_duration_seconds",
  help: "Request duration",
  labelNames: ["method", "route", "status"],
  buckets: [0.1, 0.5, 1, 2, 5],
});

// Middleware
app.use((req, res, next) => {
  const end = httpRequestDuration.startTimer();

  res.on("finish", () => {
    const labels = {
      method: req.method,
      route: req.route?.path || req.path,
      status: res.statusCode,
    };

    httpRequestCounter.inc(labels);
    end(labels);
  });

  next();
});

// ===============================
// 🔥 5. ROUTES
// ===============================
app.get("/", (req, res) => {
  res.json({
    status: "AIOps App Running",
    service: "aiops-engine",
  });
});

app.get("/load", async (req, res) => {
  const delay = Math.random() * 2000;
  await new Promise((r) => setTimeout(r, delay));

  if (Math.random() > 0.8) {
    return res.status(500).json({
      error: "Simulated failure",
      delay,
    });
  }

  res.json({
    message: "OK",
    delay,
  });
});

app.get("/trace-test", (req, res) => {
  res.json({ traced: true });
});

// Metrics endpoint
app.get("/metrics", async (req, res) => {
  res.set("Content-Type", client.register.contentType);
  res.end(await client.register.metrics());
});

// ===============================
// 🔥 6. START SERVER (LAST)
// ===============================
app.listen(3000, "0.0.0.0", () => {
  console.log("🚀 App running on port 3000");
});