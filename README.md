# DeepSeek-Alpha

The purpose of this project is to undertake a simple training of a self-hosted version of a DeepSeek model.

The following is based on a conversation with ChatGPT 5.1:

## Initial query

What I'd like is for you to design for me a sample project useful in a business ense that uses, say, DeepSeek-R1 self-hosted? Can you give me the outline of such. project, including such things as deployment pipeline, service on AWS?
You said:
So how do I get Deepseek into AWS in a way I can use it?

### Response

Here’s a concrete, business-useful project built around self-hosting DeepSeek-R1 on AWS, with a full outline: architecture, components, and deployment pipeline.

I’ll assume:

You want real business value, not just a toy.

You’re happy with containerized inference on AWS (ECS or EKS; I’ll pick ECS Fargate for clarity).

Infra managed with Terraform, CI/CD with GitHub Actions (swap for Jenkins if you want).

1. Project concept: “Decision Copilot” for internal documents
Business idea

Decision Copilot: an internal tool that helps a company’s teams make complex decisions by:

Ingesting internal documents (requirements, specs, contracts, meeting notes, financial summaries).

Building a RAG index over them.

Using self-hosted DeepSeek-R1 for:

Deep reasoning (“should we choose Vendor A or B given these constraints?”)

Chain-of-thought analysis of tradeoffs

Drafting decision memos and risk assessments

It’s useful for product managers, legal, procurement, execs.
You can easily imagine selling this as: “Bring your own cloud, your own data, our reasoning engine and UI.”

2. High-level architecture
Components

DeepSeek-R1 Inference Service (Docker on ECS Fargate with GPU)

RAG API Backend (FastAPI on ECS Fargate CPU)

Vector store (e.g., pgvector on Amazon RDS, or Qdrant on EC2/ECS)

Document ingestion pipeline (AWS Lambda + S3 + Step Functions)

Web frontend (React app served via S3 + CloudFront)

Auth & access control (Cognito or your existing IdP via OIDC)

CI/CD pipeline (GitHub Actions → ECR → Terraform apply / CodeDeploy step)

Data flow

User uploads docs (PDF, DOCX, MD) → S3 “ingest” bucket.

Lambda triggers → extracts text → chunks it → embeds via your self-hosted embedder (or an API) → writes embeddings to vector DB.

User opens web app, logs in, asks a question about some project/decision.

Backend:

Finds relevant chunks by vector similarity.

Builds a prompt + retrieved context.

Sends to DeepSeek-R1 inference service.

Returns structured answer + reasoning chain.

Frontend shows:

Final answer

Optional “show reasoning” mode

Links back to source docs and passages.

3. DeepSeek-R1 self-hosting on AWS
3.1 Container image

Repo structure (simplified):

/decision-copilot/
  infra/                  # Terraform, env configs
  services/
    r1-inference/         # DeepSeek-R1 inference service
      Dockerfile
      app/
        main.py           # simple HTTP server (FastAPI) that calls the model
        model_loader.py
    rag-api/
      Dockerfile
      app/
        main.py           # RAG logic, routes /chat, /reason
  frontend/
    web/                  # React app
  .github/
    workflows/
      ci-cd.yml


DeepSeek inference Dockerfile (conceptual):

FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04

WORKDIR /app

RUN apt-get update && apt-get install -y python3 python3-pip && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY app ./app

ENV MODEL_NAME=deepseek-r1
ENV HF_HOME=/models/cache   # or your own model store

CMD ["python3", "-m", "app.main"]


app/main.py would:

Load DeepSeek-R1 via vLLM / transformers / SGLang.

Expose /generate endpoint with JSON body {prompt, max_tokens, temperature, ...}.

3.2 ECS/Fargate setup

Use ECS with GPU-based Fargate (or EC2-backed ECS cluster if you want specific GPU control):

ECR repo: decision-copilot/deepseek-r1

Task definition:

GPU: 1 (e.g., g5.xlarge)

Memory/CPU sized accordingly

Environment vars: MODEL_NAME, MAX_CONCURRENT_REQUESTS, etc.

Service:

Behind an internal NLB (only accessible inside VPC or via PrivateLink)

Auto-scaling based on CPU/GPU utilization or request rate

Terraform will define:

aws_ecr_repository for r1-inference

aws_ecs_cluster

aws_ecs_task_definition (with GPU / Fargate)

aws_ecs_service

aws_lb + aws_lb_target_group + aws_lb_listener

4. RAG API backend
4.1 Responsibilities

Handle auth tokens (from Cognito).

Expose endpoints:

POST /chat – normal Q&A

POST /reason – explicitly request deeper chain-of-thought style reasoning

POST /upload-metadata – maybe annotate projects, tags, departments

Implement the RAG pipeline:

Convert question → embedding

Query vector DB

Construct prompt with:

System message (“You are a business decision assistant…”)

Context snippets from vector DB

User question

Call DeepSeek-R1 inference endpoint.

Post-process answer (e.g., extract bullet lists, call a tool to format a decision memo).

4.2 Deployment

Same pattern as R1 but CPU-only:

Docker image decision-copilot/rag-api → ECR

ECS Fargate service, behind:

Public ALB (with WAF & TLS cert) or

API Gateway (HTTP API → ALB/NLB)

Environment:

DB connection string to pgvector / Qdrant

URL of the internal DeepSeek-R1 inference service

Redis (optional) for caching

5. Vector DB and document ingestion
5.1 Vector store

Two practical options:

PostgreSQL + pgvector on Amazon RDS:

Pros: managed; easy backups; you know Postgres.

Store tables: documents, chunks, embeddings, projects.

Qdrant on EC2/ECS:

Pros: purpose-built vector DB, HNSW index, filtering, etc.

Managed options exist, but you can self-host.

For simplicity, start with pgvector.

5.2 Ingestion pipeline (serverless)

Flow:

User drops file into S3 bucket: decision-copilot-docs-raw.

S3 event → triggers Lambda doc_ingestor.

doc_ingestor:

Fetches file from S3

Uses Textract / unstructured / pypdf / docx libs to extract text

Splits into chunks (e.g., 500–1500 tokens)

Calls your embedding model (could be: open embedding model on ECS, or an external API if that’s acceptable)

Writes rows into pgvector:

chunk_id, document_id, text, embedding, metadata (tags, project, department)

Optionally, wrap this in a Step Functions workflow if you want multi-step extraction, language detection, classification, etc.

Terraform bits:

aws_s3_bucket decision-copilot-docs-raw

aws_lambda_function doc-ingestor

S3 → Lambda event notification

RDS instance (Postgres with pgvector)

IAM roles for Lambda to read from S3 + write secrets from Secrets Manager

6. Frontend & UX
Key features

Secure login via Cognito / SSO

“Ask a question about…” textbox

Ability to:

Select project / department / time range (filters passed to RAG)

View answer + optional “show reasoning” (chain-of-thought text from R1, maybe behind a toggle since that’s sensitive)

See the source documents & highlighted passages used

Save decision memos as records (stored in Postgres as decisions with links to conversation + docs)

Deployment

React app built to static assets

Served from S3 + CloudFront with TLS + caching

API calls go to your API Gateway / ALB endpoint for rag-api.

Terraform bits:

aws_s3_bucket for web hosting

aws_cloudfront_distribution

aws_acm_certificate for TLS

Route53 CNAME like decisions.yourcompany.com

7. CI/CD pipeline
Repos

You can do monorepo:

/infra – Terraform

/services/r1-inference – Dockerized inference service

/services/rag-api – backend

/frontend/web – React app

GitHub Actions workflow outline

On push to main or release/*:

Build & test

Run unit tests for backend and frontend.

Lint, static analysis, maybe some prompt-based tests.

Build containers

docker build for r1-inference and rag-api

docker push to ECR with tags like git-sha and latest.

Infra deploy

terraform fmt && terraform validate

terraform plan

Optionally require manual approval for terraform apply in prod.

App deploy

ECS:

Update ECS service task definitions with new image tags using aws ecs update-service --force-new-deployment.

Frontend:

npm run build

Sync build artifacts to S3 aws s3 sync build/ s3://decision-copilot-frontend/

Invalidate CloudFront cache.

You can add environments:

dev → ephemeral branches, smaller GPU, tiny RDS

stage → full stack, but lower capacity

prod → scaled, behind SSO with stricter logging & monitoring

8. Observability, logging, and cost controls
Observability

CloudWatch Logs for ECS tasks (DeepSeek service + RAG API)

Add structured logging (JSON) to both services:

Request ID, user ID, latency, token counts, retrieval stats.

Metrics:

Per-model request count

Latency histograms

GPU utilization (via CloudWatch / exporter)

RDS CPU & connections

Optionally integrate with Datadog (since you already use it) for APM & traces:

Wrap RAG API in ddtrace

Tag traces by project, department, decision_type.

Cost controls

Use auto-scaling on ECS services:

Scale DeepSeek-R1 service down to zero or one during off-hours.

GPU instance selection:

Start with something like g5.xlarge and move up/down depending on load.

Use smaller DeepSeek variants and/or quantization to improve throughput.

9. Why this is “business useful”

Direct value: faster, better-documented internal decisions; improved risk awareness.

Strong AI angle: Deep reasoning with self-hosted DeepSeek-R1, not just superficial RAG.

Enterprise-ready:

Data never leaves your AWS account.

Full audit trail of which docs influenced which decisions.

Regulatory & compliance comfort: you control infra & logs.

Productizable:

You can offer “Decision Copilot” as:

A template deployment for clients (bring your own AWS)

A managed service in your AWS with tenant isolation

Or a consulting + setup package.

If you’d like, next step I can:

Sketch a Terraform skeleton (ECR + ECS GPU service + ALB)

Or outline the FastAPI contracts between:

Frontend → RAG API

RAG API → DeepSeek-R1 inference service

Or focus on prompt & RAG design for deep business reasoning (e.g., structured “decision memo” outputs).

## Follow-up query

Short version: you don’t “upload DeepSeek” to AWS as a magic blob — you run a normal containerized inference server on an AWS GPU, and that server downloads/loads the DeepSeek model weights at startup.

### Response
Let me give you a concrete, minimal path you could actually implement this week.

0. Choose your serving strategy

For self-hosting DeepSeek-R1 on AWS, pick one of these patterns:

Fast path / simple:

A single Docker container running:

Python

vllm or sglang (or plain transformers if you really want)

DeepSeek-R1 weights pulled from Hugging Face or another model hub

Deployed on:

EC2 GPU (e.g. g5.xlarge) or

ECS on EC2 with GPU

More production-y:

Separate container just for inference (vLLM / SGLang)

Fronted by API Gateway / ALB

Managed by ECS / EKS with autoscaling

I’ll describe something in between: one Dockerized inference service on an EC2 GPU, then show how you’d “graduate” it to ECS.

1. High-level steps

Pick the DeepSeek model & serving library

Write a tiny inference service (FastAPI) that wraps the model

Create a Docker image and push to ECR

Run that image on a GPU instance (EC2 or ECS)

Expose it inside your VPC (and optionally to the public)

Call it from your apps like you’d call OpenAI

2. Pick model + serving library

Let’s assume:

Model: a DeepSeek-R1 or DeepSeek-V “chat” variant from Hugging Face

Serving: vLLM (good throughput, relatively simple)

Your inference container will:

On startup: download the model weights (or load them from EFS/S3 cache)

Expose /generate HTTP endpoint

Generate responses using vLLM’s API

3. Minimal inference service (FastAPI + vLLM)
requirements.txt (conceptual)
fastapi
uvicorn[standard]
vllm
transformers
accelerate

app/main.py (sketch)
from fastapi import FastAPI
from pydantic import BaseModel
from vllm import LLM, SamplingParams

#### You’d use the actual DeepSeek model repo name from HF
MODEL_NAME = "deepseek-ai/DeepSeek-R1"  # placeholder

app = FastAPI()

#### Load model at startup
llm = LLM(model=MODEL_NAME, tensor_parallel_size=1)  # adjust for multi-GPU

class GenerateRequest(BaseModel):
    prompt: str
    max_tokens: int = 512
    temperature: float = 0.7

class GenerateResponse(BaseModel):
    text: str

@app.post("/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest):
    sampling_params = SamplingParams(
        max_tokens=req.max_tokens,
        temperature=req.temperature,
    )
    outputs = llm.generate([req.prompt], sampling_params)
    text = outputs[0].outputs[0].text
    return GenerateResponse(text=text)


This is intentionally bare-bones; you’d add:

system prompts

streaming

error handling

logging, etc.

4. Dockerize it
Dockerfile (GPU / CUDA image)
FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04

WORKDIR /app

#### Basic deps
RUN apt-get update && apt-get install -y python3 python3-pip git && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY app ./app

ENV MODEL_NAME=deepseek-ai/DeepSeek-R1
ENV HF_HOME=/models/cache

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]


Build & test locally (on a box with an NVIDIA GPU + Docker):

docker build -t deepseek-r1-inference .
docker run --gpus all -p 8000:8000 deepseek-r1-inference


Call it:

curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Explain quantum tunneling simply", "max_tokens": 256}'

5. Push image to AWS ECR

In AWS:

Create an ECR repository → e.g. deepseek-r1-inference.

Login from your dev machine:

aws ecr get-login-password --region us-west-2 \
  | docker login --username AWS --password-stdin <your-account-id>.dkr.ecr.us-west-2.amazonaws.com


Tag + push:

docker tag deepseek-r1-inference:latest \
  <your-account-id>.dkr.ecr.us-west-2.amazonaws.com/deepseek-r1-inference:latest

docker push <your-account-id>.dkr.ecr.us-west-2.amazonaws.com/deepseek-r1-inference:latest

6. Run it on AWS (simplest: EC2 GPU)
6.1 Create a GPU instance

Launch EC2 instance type e.g. g5.xlarge

Use an AMI with NVIDIA drivers + Docker + nvidia-container-runtime (either:

Deep Learning Base AMI, or

your own baked AMI with drivers installed)

6.2 Pull and run the container

On the instance:

aws ecr get-login-password --region us-west-2 \
  | docker login --username AWS --password-stdin <your-account-id>.dkr.ecr.us-west-2.amazonaws.com

docker pull <your-account-id>.dkr.ecr.us-west-2.amazonaws.com/deepseek-r1-inference:latest

docker run -d --gpus all -p 80:8000 \
  --name deepseek-r1 \
  <your-account-id>.dkr.ecr.us-west-2.amazonaws.com/deepseek-r1-inference:latest


Now you have a running DeepSeek-R1 inference server on that instance.

From inside your VPC, hit: http://<instance-private-ip>/generate

From the internet (if you open it up) hit: http://<public-ip>/generate

You should put it behind an ALB + HTTPS in real life.

7. “Next step up”: ECS instead of raw EC2

Once you’re happy with manual EC2, you can:

Create an ECS cluster.

Create a task definition:

Container: your ECR image

GPU: 1

Port: 8000

Create an ECS service that:

Runs that task on GPU-capable EC2 instances

Attaches to a Network Load Balancer or ALB

Then your DeepSeek endpoint becomes:

https://deepseek.yourdomain.com/generate

…and everything else (FastAPI RAG service, frontends, etc.) just sees “an HTTP LLM endpoint,” not “a weird GPU model.”

8. Using it from your apps

From a Python backend (e.g. your RAG FastAPI):

import httpx

async def call_deepseek(prompt: str) -> str:
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            "https://deepseek.yourdomain.com/generate",
            json={"prompt": prompt, "max_tokens": 512, "temperature": 0.3},
        )
        resp.raise_for_status()
        return resp.json()["text"]


From there, you:

Wrap it in a “LLM client” class

Plug it into your RAG pipeline / tools / agents

Treat it like your own OpenAI clone living in your VPC.

9. Where Terraform / CI/CD fits

You already know this dance, but in outline:

Terraform:

aws_ecr_repository for the image

aws_instance (GPU) or aws_ecs_cluster + aws_ecs_service

aws_lb + listener + target group

aws_security_group firewall rules

Optionally aws_route53_record for a nice domain

CI/CD (GitHub Actions or Jenkins):

On push → build Docker → test → push to ECR

Kick a deployment step:

For EC2: SSH + docker pull + docker restart

For ECS: update service → new task definition revision

If you want, next I can:

Sketch a Terraform module that spins up:

ECR repo

EC2 GPU instance

Security group

Or sketch a minimal ECS task/service definition JSON that you could drop into Terraform.