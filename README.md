# AML Policy FAQ Bot

AI-powered AML (Anti-Money Laundering) compliance chatbot using **RAG** with **LangChain**, **LangGraph**, **NVIDIA LLM**, and **Qdrant Cloud**.

---

## Project Structure

```
AML_Policy_FAQ_BOT/
├── backend/                 # FastAPI + Lambda
│   ├── app/                 # Application code
│   ├── handler.py           # Lambda entry point
│   └── pyproject.toml       # Dependencies (uv)
├── frontend/                # Vite + React
│   ├── src/                 # React components
│   └── package.json
├── infrastructure/
│   ├── bootstrap/           # Terraform state (run first)
│   ├── backend/             # Lambda, API Gateway, S3
│   └── frontend/            # S3, CloudFront
└── .github/workflows/
    ├── infrastructure.yml         # Backend infra
    ├── infrastructure-frontend.yml # Frontend infra
    ├── deploy-backend.yml         # Deploy Lambda
    └── deploy-frontend.yml        # Deploy React
```

---

## Quick Start (Local Development)

### Backend

```bash
cd backend
uv sync

# Create .env
cat > .env << EOF
NVIDIA_API_KEY=your_nvidia_api_key
NVIDIA_MODEL_NAME=meta/llama-3.1-70b-instruct
NVIDIA_EMBEDDING_MODEL_NAME=nvidia/nv-embedqa-e5-v5
QDRANT_URL=https://your-cluster.qdrant.io:6333
QDRANT_API_KEY=your_qdrant_api_key
EOF

# Run
uv run uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install

# Create .env
echo 'VITE_API_URL=http://localhost:8000' > .env

# Run
npm run dev
```

Open http://localhost:5173

---

## AWS Deployment

### Prerequisites

1. **AWS Account** with admin access
2. **NVIDIA API Key** from [build.nvidia.com](https://build.nvidia.com)
3. **Qdrant Cloud** account from [cloud.qdrant.io](https://cloud.qdrant.io)

### Step 1: Bootstrap (Run Once Locally)

```bash
cd infrastructure/bootstrap
terraform init
terraform apply
```

Note the outputs: S3 bucket and DynamoDB table names.

### Step 2: Configure GitHub Secrets

Add these secrets to your GitHub repository:

| Secret | Description |
|--------|-------------|
| `AWS_ACCESS_KEY_ID` | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key |
| `NVIDIA_API_KEY` | NVIDIA API key |
| `NVIDIA_MODEL_NAME` | `meta/llama-3.1-70b-instruct` |
| `NVIDIA_EMBEDDING_MODEL_NAME` | `nvidia/nv-embedqa-e5-v5` |
| `QDRANT_URL` | Qdrant Cloud URL |
| `QDRANT_API_KEY` | Qdrant Cloud API key |

### Step 3: Deploy Infrastructure

Run workflows in this order:

```
1. Infrastructure (Backend)     → apply → Creates Lambda, API Gateway, S3
2. Infrastructure (Frontend)    → apply → Creates S3, CloudFront
3. Deploy Backend               → Deploys Lambda code
4. Deploy Frontend              → Builds React, uploads to S3
```

### Step 4: Access Your App

After deployment, you'll see URLs in the workflow summary:
- **Frontend**: `https://d1234567890.cloudfront.net`
- **Backend API**: `https://xxxx.execute-api.ap-south-1.amazonaws.com`

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Health check |
| POST | `/api/v1/ingest` | Upload documents |
| POST | `/api/v1/query` | Query (sync) |
| WS | `/api/v1/ws/query` | Query (streaming) |
| GET | `/docs` | Swagger UI |

---

## Architecture

```
                    ┌─────────────────┐
                    │   CloudFront    │
                    │  (Frontend CDN) │
                    └────────┬────────┘
                             │
┌────────────────────────────┼────────────────────────────────┐
│                            │                                │
│   ┌────────────────┐       │       ┌────────────────┐       │
│   │   S3 Bucket    │◀──────┘       │  API Gateway   │       │
│   │  (React App)   │               │   (HTTP API)   │       │
│   └────────────────┘               └───────┬────────┘       │
│                                            │                │
│                                    ┌───────▼────────┐       │
│                                    │     Lambda     │       │
│                                    │   (FastAPI)    │       │
│                                    └───┬────────┬───┘       │
│                                        │        │           │
│                            ┌───────────▼──┐  ┌──▼──────────┐|
│                            │ Qdrant Cloud │  │ NVIDIA LLM  │|
│                            │ (Vectors)    │  │ (Inference) │|
│                            └──────────────┘  └─────────────┘|
└─────────────────────────────────────────────────────────────┘
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `NVIDIA_API_KEY` | ✅ | NVIDIA API key for LLM |
| `NVIDIA_MODEL_NAME` | ✅ | LLM model name |
| `NVIDIA_EMBEDDING_MODEL_NAME` | ✅ | Embedding model name |
| `QDRANT_URL` | ✅ | Qdrant Cloud cluster URL |
| `QDRANT_API_KEY` | ✅ | Qdrant Cloud API key |
| `S3_BUCKET` | Lambda | S3 bucket for documents |
| `VITE_API_URL` | Frontend | Backend API URL |

---

## Destroy Infrastructure

To tear down AWS resources:

```bash
# Via GitHub Actions
1. Run "Infrastructure (Frontend)" → destroy
2. Run "Infrastructure (Backend)" → destroy

# Or locally
cd infrastructure/frontend && terraform destroy
cd infrastructure/backend && terraform destroy
```

---

## Tech Stack

- **Backend**: FastAPI, LangChain, LangGraph, NVIDIA AI Endpoints
- **Frontend**: React, Vite
- **Vector Store**: Qdrant Cloud
- **Infrastructure**: Terraform, AWS Lambda, API Gateway, CloudFront
- **CI/CD**: GitHub Actions
