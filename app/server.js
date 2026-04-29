// ===============================
// 🔥 1. OPENTELEMETRY (FIXED)
// ===============================
const { NodeSDK } = require("@opentelemetry/sdk-node");
const { OTLPTraceExporter } = require("@opentelemetry/exporter-trace-otlp-http");
const { getNodeAutoInstrumentations } = require("@opentelemetry/auto-instrumentations-node");
const { resourceFromAttributes } = require("@opentelemetry/resources");
const { SemanticResourceAttributes } = require("@opentelemetry/semantic-conventions");

// 🔥 force proper instrumentation
const instrumentations = getNodeAutoInstrumentations({
  "@opentelemetry/instrumentation-http": { enabled: true },
  "@opentelemetry/instrumentation-express": { enabled: true },
});

const traceExporter = new OTLPTraceExporter({
  url: "http://otel-collector:4318/v1/traces",
});

const sdk = new NodeSDK({
  traceExporter,
  instrumentations,
  resource: resourceFromAttributes({
    [SemanticResourceAttributes.SERVICE_NAME]: "aiops-app",
  }),
});

// 🔥 IMPORTANT: start synchronously (NO async)
sdk.start();
console.log("✅ OpenTelemetry started");


// ===============================
// 🔥 2. IMPORTS
// ===============================
const express = require("express");
const client = require("prom-client");
const winston = require("winston");
const fs = require("fs");
const { trace } = require("@opentelemetry/api"); // 🔥 NEW


// ===============================
// 🔥 3. LOGGING SETUP (LOKI)
// ===============================
const logDir = "/app/logs";

if (!fs.existsSync(logDir)) {
  fs.mkdirSync(logDir, { recursive: true });
}

const logger = winston.createLogger({
  level: "info",
  format: winston.format.json(),
  transports: [
    new winston.transports.File({
      filename: `${logDir}/app.log`,
    }),
    new winston.transports.Console(),
  ],
});


// ===============================
// 🔥 4. APP SETUP
// ===============================
const app = express();
app.use(express.json());


// ===============================
// 🔥 5. PROMETHEUS METRICS
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


// ===============================
// 🔥 6. REQUEST LOGGING + TRACE
// ===============================
app.use((req, res, next) => {
  const start = Date.now();
  const end = httpRequestDuration.startTimer();

  // 🔥 CREATE MANUAL SPAN (IMPORTANT FIX)
  const tracer = trace.getTracer("http-middleware");
  const span = tracer.startSpan(`${req.method} ${req.path}`);

  res.on("finish", () => {
    const duration = Date.now() - start;

    const labels = {
      method: req.method,
      route: req.route?.path || req.path,
      status: res.statusCode,
    };

    httpRequestCounter.inc(labels);
    end(labels);

    // 🔥 close span
    span.setAttribute("http.method", req.method);
    span.setAttribute("http.route", req.path);
    span.setAttribute("http.status_code", res.statusCode);
    span.end();

    logger.info({
      type: "http_request",
      method: req.method,
      route: req.path,
      status: res.statusCode,
      duration_ms: duration,
    });
  });

  next();
});


// ===============================
// 🔥 7. ROUTES (WITH SPANS)
// ===============================
app.get("/", (req, res) => {
  const tracer = trace.getTracer("routes");
  const span = tracer.startSpan("home-endpoint");

  logger.info({ message: "Health check hit" });

  span.end();

  res.json({
    status: "AIOps App Running",
    service: "aiops-app",
  });
});

app.get("/load", async (req, res) => {
  const tracer = trace.getTracer("routes");
  const span = tracer.startSpan("load-endpoint");

  const delay = Math.random() * 2000;
  await new Promise((r) => setTimeout(r, delay));

  if (Math.random() > 0.8) {
    logger.error({
      type: "application_error",
      message: "Simulated failure",
      delay,
    });

    span.recordException(new Error("Simulated failure"));
    span.end();

    return res.status(500).json({
      error: "Simulated failure",
      delay,
    });
  }

  logger.info({
    type: "load_test",
    message: "Request successful",
    delay,
  });

  span.end();

  res.json({
    message: "OK",
    delay,
  });
});

app.get("/trace-test", (req, res) => {
  const tracer = trace.getTracer("routes");
  const span = tracer.startSpan("trace-test-endpoint");

  logger.info({
    type: "trace_test",
    message: "Trace endpoint hit",
  });

  span.end();

  res.json({ traced: true });
});


// ===============================
// 🔥 8. METRICS ENDPOINT
// ===============================
app.get("/metrics", async (req, res) => {
  res.set("Content-Type", client.register.contentType);
  res.end(await client.register.metrics());
});


// ===============================
// 🔥 9. START SERVER
// ===============================
app.listen(3000, "0.0.0.0", () => {
  logger.info({
    type: "startup",
    message: "🚀 App running on port 3000",
  });

  console.log("🚀 App running on port 3000");
});