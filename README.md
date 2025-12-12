# AML Policy FAQ Bot

A chatbot for answering compliance officers' questions on AML (Anti-Money Laundering) policies using **RAG** with **LangChain**, **LangGraph**, and **NVIDIA LLM**.

## Project Structure

```
AML_Policy_FAQ_BOT/
├── backend/                 # FastAPI application
│   ├── app/                 # Application code
│   ├── handler.py           # Lambda entry point
│   └── pyproject.toml       # Dependencies
├── infrastructure/          # Terraform
│   ├── bootstrap/           # State management (run locally first)
│   └── backend/             # Backend infrastructure
└── .github/workflows/       # CI/CD
    ├── infrastructure.yml   # Terraform deploy
    └── deploy-backend.yml   # Lambda deploy
```

## Local Development

```bash
# Install dependencies
cd backend
uv sync

# Create .env file
cp ../.env.example .env
# Edit .env and add your NVIDIA_API_KEY

# Run server
uv run uvicorn app.main:app --reload --port 8000
```

## AWS Deployment

### 1. Bootstrap (Run Once Locally)

```bash
cd infrastructure/bootstrap
terraform init
terraform apply
# Note the outputs for state bucket and DynamoDB table
```

### 2. Configure GitHub Secrets

Add these secrets to your GitHub repository:

| Secret | Description |
|--------|-------------|
| `AWS_ACCESS_KEY_ID` | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key |
| `NVIDIA_API_KEY` | NVIDIA API key |
| `NVIDIA_MODEL_NAME` | e.g. `meta/llama-3.1-70b-instruct` |
| `NVIDIA_EMBEDDING_MODEL_NAME` | e.g. `nvidia/nv-embedqa-e5-v5` |

### 3. Update Terraform Backend

Edit `infrastructure/backend/main.tf` and uncomment the S3 backend configuration with your bootstrap outputs.

### 4. Deploy

Push to `main` branch or trigger workflows manually:

1. **infrastructure.yml** - Provisions Lambda, S3, API Gateway, Secrets Manager
2. **deploy-backend.yml** - Builds and deploys Lambda code

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Health check |
| POST | `/api/v1/ingest` | Upload documents |
| POST | `/api/v1/query` | Query (sync) |
| WS | `/api/v1/ws/query` | Query (streaming) |

## Environment Variables

| Variable | Local | Lambda | Description |
|----------|-------|--------|-------------|
| `NVIDIA_API_KEY` | ✓ .env | Secrets Manager | NVIDIA API key |
| `NVIDIA_MODEL_NAME` | ✓ .env | Secrets Manager | LLM model |
| `NVIDIA_EMBEDDING_MODEL_NAME` | ✓ .env | Secrets Manager | Embedding model |
| `S3_BUCKET` | - | Lambda env | S3 bucket for Chroma |
| `VECTOR_STORE_PATH` | ✓ .env | Lambda env | Local Chroma path |

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   API Gateway   │────▶│     Lambda      │────▶│  NVIDIA LLM     │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
            ┌───────▼───────┐         ┌───────▼───────┐
            │  S3 (Chroma)  │         │ Secrets Mgr   │
            └───────────────┘         └───────────────┘
```
