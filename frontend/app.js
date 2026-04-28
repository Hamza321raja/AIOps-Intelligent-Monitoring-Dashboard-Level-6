const API_BASE = "http://localhost:3000";

let totalRequests = 0;
let workers = [];

// Update UI
function updateUI() {
    document.getElementById("counter").innerText = totalRequests;
    document.getElementById("workers").innerText = workers.length;
}

// ✅ FIXED BACKEND CHECK
async function checkBackend() {
    try {
        const res = await fetch(`${API_BASE}/`);

        const data = await res.json();

        console.log("Backend response:", data);

        if (data && data.status) {
            document.getElementById("status").innerText = "Healthy ✅";
        } else {
            throw new Error("Invalid response");
        }

    } catch (error) {
        console.error("Backend error:", error);
        document.getElementById("status").innerText = "Backend Down ❌";
    }
}

// 🔥 REAL LOAD WORKER
function createWorker(rps) {
    const worker = setInterval(() => {
        for (let i = 0; i < rps; i++) {
            fetch(`${API_BASE}/load`)
                .catch(err => {
                    console.warn("Request failed", err);
                });

            totalRequests++;
        }

        updateUI();
    }, 1000);

    workers.push(worker);
}

// 🔥 STACK LOAD
function startLoad(rps) {
    createWorker(rps);

    document.getElementById("status").innerText =
        `Running Load (${workers.length} workers) 🔥`;

    updateUI();
}

// 🔥 STOP ALL
function stopLoad() {
    workers.forEach(w => clearInterval(w));
    workers = [];

    document.getElementById("status").innerText = "Stopped";
    updateUI();
}

// Health check every 3s
setInterval(checkBackend, 3000);
checkBackend();