# EducAgent

An educational AI agent built around *Elements of Causal Inference* (Peters et al., 2017).
The backend exposes a GraphRAG API over a Neo4j knowledge graph of 189 nodes and 332 edges.

---

## Project Layout

```
EducAgent/
├── src/
│   ├── backend/          # FastAPI app
│   │   ├── main.py
│   │   ├── settings.py
│   │   ├── routers/      # concepts, chapters, query, health
│   │   └── services/     # neo4j_client, text2cypher
│   └── graph/            # Graph tools
│       ├── eci_neo4j_importer.py
│       ├── eci_graph_builder.py
│       └── output/       # eci_graph.json (189 nodes, 332 edges)
├── tests/                # 32 unit tests (mock Neo4j, no live DB needed)
├── docker/               # Kubernetes Job specs
├── assets/               # ECI textbook sections
├── .env                  # Local credentials (git-ignored)
├── .env.example          # Safe template to copy
├── Makefile
└── pytest.ini
```

---

## Quick Start (local)

### 1. Copy and fill in credentials

```bash
cp .env.example .env
# Edit .env with your Neo4j AuraDB URI and OpenRouter API key
```

### 2. Install dependencies

```bash
conda activate edu
pip install -r docker/requirements.txt
```

### 3. Run tests (no live DB required)

```bash
make test
# or: python -m pytest tests/ -v
```

### 4. Load graph into Neo4j

```bash
make import-graph
# or: python src/graph/eci_neo4j_importer.py
```

### 5. Start the API

```bash
make serve
# or: PYTHONPATH=src uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Open <http://localhost:8000/docs> for the Swagger UI.

---

## Kubernetes Deployment (EIDF cluster + Neo4j AuraDB)

This section covers running EducAgent in a Kubernetes pod while connecting to
**Neo4j AuraDB** (managed cloud) over the public internet — no separate Neo4j
pod required.

### Prerequisites

- `kubectl` configured against the EIDF cluster
- A free Neo4j AuraDB instance: <https://console.neo4j.io>
- An OpenRouter API key: <https://openrouter.ai>

---

### Step 1 — Create a Neo4j AuraDB instance

1. Go to <https://console.neo4j.io> → **New Instance** → choose **Free**.
2. Copy the generated credentials:
   - **Connection URI** — looks like `neo4j+s://xxxxxxxx.databases.neo4j.io`
   - **Username** — `neo4j`
   - **Password** — auto-generated string
3. Save these; you will need them in Step 3.

---

### Step 2 — Submit a Kubernetes Job

Use the provided Job spec:

```bash
kubectl apply -f docker/job.yaml
```

Wait for the pod to be running:

```bash
kubectl get pods -l kueue.x-k8s.io/queue-name=eidf098ns-user-queue
# NAME                  READY   STATUS    RESTARTS   AGE
# edu-xxxx-yyyy         1/1     Running   0          30s
```

---

### Step 3 — Configure credentials inside the pod

Exec into the pod and navigate to the project:

```bash
kubectl exec -it <pod-name> -- /bin/bash
cd /data/users/yyx/onProject/CHAI/EducAgent
conda activate edu
```

Copy the example env file and fill in your AuraDB + OpenRouter credentials:

```bash
cp .env.example .env
```

Edit `.env`:

```env
NEO4J_URI=neo4j+s://xxxxxxxx.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=<your-aura-password>

OPENROUTER_API_KEY=sk-or-v1-<your-key>
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

CORS_ORIGINS=http://localhost:3000
```

> **Note:** `neo4j+s://` (not `bolt://`) is the correct scheme for AuraDB —
> it uses TLS by default.

---

### Step 4 — Run unit tests

Verify the code is intact (no live DB needed):

```bash
make test
# expect: 32 passed
```

---

### Step 5 — Load the graph into AuraDB

```bash
make import-graph
# Connected to Neo4j at neo4j+s://xxxxxxxx.databases.neo4j.io
# 189 nodes, 332 edges found.
# ...
# Done. Import complete (idempotent — safe to re-run).
```

This is idempotent — re-running is safe and will not create duplicates.

---

### Step 6 — Start the API server

```bash
make serve
# INFO:     Started server process
# INFO:     Uvicorn running on http://0.0.0.0:8000
```

Run in the background if you want to keep using the terminal:

```bash
make serve &
```

---

### Step 7 — Smoke-test inside the pod

```bash
# Health check (includes live Neo4j node/edge counts)
curl http://localhost:8000/health | python -m json.tool

# Get prerequisites of a concept
curl http://localhost:8000/api/v1/concepts/d_separation/prerequisites

# Search concepts
curl "http://localhost:8000/api/v1/concepts/search?q=causal"

# All concepts in chapter 1
curl http://localhost:8000/api/v1/chapters/1/concepts

# Natural-language graph query (requires OPENROUTER_API_KEY)
curl -X POST http://localhost:8000/api/v1/query \
     -H "Content-Type: application/json" \
     -d '{"question": "What are the prerequisites of d-separation?"}'
```

---

### Step 8 — Access from your local machine (port-forward)

In a **separate terminal on your local machine**:

```bash
kubectl port-forward <pod-name> 8000:8000
```

Then open:

- <http://localhost:8000/docs> — Swagger UI (all endpoints, interactive)
- <http://localhost:8000/health> — quick health check

---

## API Reference

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Neo4j connectivity + graph node/edge counts |
| GET | `/api/v1/concepts/{id}` | Get a concept by ID |
| GET | `/api/v1/concepts/{id}/prerequisites` | Direct prerequisites |
| GET | `/api/v1/concepts/{id}/next-concepts` | Next concepts to learn |
| GET | `/api/v1/concepts/{id}/related` | Related concepts |
| GET | `/api/v1/concepts/{id}/sections` | Textbook sections covering this concept |
| GET | `/api/v1/concepts/search?q=...&limit=10` | Fulltext search |
| GET | `/api/v1/chapters/{chapter}/concepts` | All concepts in a chapter |
| POST | `/api/v1/query` | Natural-language → Cypher → results |

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NEO4J_URI` | `bolt://localhost:7687` | Neo4j connection URI (`neo4j+s://` for AuraDB) |
| `NEO4J_USER` | `neo4j` | Neo4j username |
| `NEO4J_PASSWORD` | `educagent` | Neo4j password |
| `OPENROUTER_API_KEY` | *(empty)* | OpenRouter API key (required for `/query`) |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | OpenRouter base URL |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated allowed CORS origins |

---

## Makefile Targets

| Target | Command | Description |
|--------|---------|-------------|
| `make serve` | `PYTHONPATH=src uvicorn backend.main:app ...` | Start API on port 8000 |
| `make test` | `python -m pytest tests/ -v` | Run all 32 unit tests |
| `make import-graph` | `python src/graph/eci_neo4j_importer.py` | Load ECI graph into Neo4j |
