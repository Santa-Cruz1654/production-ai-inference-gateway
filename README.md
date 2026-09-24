# Production AI Inference Gateway

> An actively developed, production-oriented AI inference gateway built incrementally to explore reliable LLM infrastructure, backend engineering, system design, and AI platform engineering.

This project is being developed as an engineering learning sprint rather than as a simple wrapper around an LLM API.

The objective is to understand what is required to move from:

```text
"Call an LLM API"
```

to:

```text
"Build a reliable backend service around LLM providers"
```

The system is intentionally being developed incrementally. Each stage introduces a new production engineering problem, followed by implementation, testing, debugging, and architectural refinement.

---

## Project Status

🚧 **Actively under development**

### Day 1 — Architecture & Engineering Foundations

**Completed**

* FastAPI application foundation
* Versioned inference API
* Pydantic request/response validation
* Logical model abstraction
* Provider abstraction
* Groq provider adapter
* Provider registry
* Provider selection
* Model routing
* API-key-style authentication
* Rate limiting
* Request ID / correlation mechanism
* Explicit timeout/deadline handling
* Basic error boundaries
* Unit testing
* Runtime API testing
* Environment-based configuration
* Dependency-chain refactoring
* Initial production-oriented project structure

Day 1 intentionally focuses on the architectural foundation rather than attempting to build the entire production platform at once.

---

# Why Build an Inference Gateway?

A direct LLM integration can be extremely simple:

```text
Application
    │
    ▼
LLM Provider
```

Real backend systems introduce additional engineering problems:

* How should clients authenticate?
* How should requests be validated?
* Which model should handle a request?
* What happens when a provider fails?
* How long should the gateway wait?
* How should clients be rate-limited?
* How can providers be changed without rewriting application logic?
* How can provider-dependent code be tested?
* How can individual requests be correlated across the system?
* What information should be exposed when something fails?

This project explores those problems through implementation rather than treating them purely as system-design theory.

---

# Day 1 Architecture

The current architecture is intentionally small.

```text
                         Client
                           │
                           ▼
                  ┌─────────────────┐
                  │   FastAPI API   │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ Authentication  │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │  Rate Limiting  │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ Request         │
                  │ Validation      │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ Model Resolution│
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ Provider Service│
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ Provider        │
                  │ Registry        │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ Groq Provider   │
                  └────────┬────────┘
                           │
                           ▼
                         Groq
                           │
                           ▼
                  Normalized Response
```

The central design decision is that the application does **not** directly depend on the Groq SDK throughout the codebase.

Instead:

```text
                    LLMProvider
                         │
             ┌───────────┼───────────┐
             ▼           ▼           ▼
        GroqProvider  FutureProvider  LocalProvider
```

The provider boundary allows the application to depend on an abstraction rather than a specific vendor implementation.

---

# Request Lifecycle

A request to:

```text
POST /v1/inference
```

passes through the following flow:

```text
Client
  │
  ▼
Request ID Middleware
  │
  ▼
Authentication
  │
  ▼
Rate Limiting
  │
  ▼
Pydantic Validation
  │
  ▼
Model Resolution
  │
  ▼
Model Constraint Validation
  │
  ▼
Provider Candidate Resolution
  │
  ▼
Provider Registry
  │
  ▼
Provider Adapter
  │
  ▼
Groq API
  │
  ▼
Response Normalization
  │
  ▼
Gateway Response
```

The implementation deliberately separates these responsibilities instead of placing the entire request lifecycle inside one FastAPI route.

---

# Logical Models vs Provider Models

One of the most important Day 1 architectural decisions is separating the model exposed to the client from the model identifier used by the provider.

The gateway exposes logical models such as:

```text
fast-model
quality-model
reasoning-model
```

while the provider layer maps those logical models to provider-specific model IDs.

For example:

```text
Client
  │
  │ fast-model
  ▼
Gateway Model Registry
  │
  ▼
Provider Routing
  │
  ▼
Groq
  │
  ▼
openai/gpt-oss-20b
```

This prevents provider-specific model identifiers from leaking throughout the application.

It also means a provider model can change without forcing clients to change their API requests.

Groq currently lists `openai/gpt-oss-20b` as a production model, with a 131,072-token context window and 65,536 maximum completion tokens. Model availability can change, so provider model identifiers remain isolated inside the routing/configuration layer.

---

# Provider Abstraction

The gateway defines a common provider interface:

```text
LLMProvider
```

The current concrete implementation is:

```text
GroqProvider
```

The application therefore follows the conceptual dependency:

```text
Application
     │
     ▼
LLMProvider
     │
     ▼
GroqProvider
     │
     ▼
Groq SDK
```

This introduces several important backend engineering concepts:

* abstraction
* interfaces
* dependency inversion
* adapter pattern
* provider portability
* testability
* separation of concerns

A future provider can be introduced without rewriting the entire inference pipeline.

---

# Provider Registry

Providers are registered through a dedicated registry.

Conceptually:

```text
ProviderRegistry

groq → GroqProvider
```

The registry is responsible for provider lookup rather than embedding provider construction throughout the application.

This creates a clean boundary between:

```text
Provider registration
        ↓
Provider lookup
        ↓
Provider implementation
```

---

# Model Routing

The routing layer maps logical gateway models to provider candidates.

Current routing is intentionally simple:

```text
fast-model
    ↓
Groq
    ↓
openai/gpt-oss-20b
```

The architecture is designed so routing can become more sophisticated later.

Potential future routing criteria include:

* latency
* model capability
* cost
* provider availability
* task type
* context requirements

Day 1 deliberately does not implement complex intelligent routing before the basic architecture is reliable.

---

# Authentication

The inference endpoint requires authentication.

The current development implementation uses an API-key-style bearer token:

```http
Authorization: Bearer gateway-dev-key
```

The architectural distinction is:

```text
Authentication
    ↓
Who is making the request?
```

versus:

```text
Authorization
    ↓
What is that requester allowed to do?
```

Day 1 establishes the authentication boundary.

More advanced capabilities such as:

* tenant identity
* key rotation
* scoped permissions
* production secret management
* advanced authorization policies

remain future work.

---

# Rate Limiting

The gateway includes rate limiting as an early protection mechanism.

Rate limiting is important because the gateway sits between clients and an external LLM dependency.

It can protect:

* provider quotas
* application resources
* downstream dependencies
* infrastructure
* availability
* cost

The current implementation is intentionally simple.

A future production architecture can evolve toward distributed rate limiting using Redis when there is an actual requirement for distributed state.

---

# Request IDs

The gateway generates or accepts a request identifier.

Conceptually:

```text
Client
  │
  │ X-Request-ID
  ▼
Gateway
  │
  ├── authentication
  ├── validation
  ├── routing
  ├── provider call
  └── response
```

The request ID is returned through the response.

This establishes the foundation for future structured logging and distributed tracing.

As the system grows, the same identifier can be used to correlate activity across:

```text
API
 ↓
Router
 ↓
Provider
 ↓
External API
```

---

# Timeout / Deadline Handling

External dependencies should not be allowed to wait indefinitely.

Day 1 introduced explicit request-deadline handling.

The underlying principle is:

> No external dependency should be allowed to consume an unlimited amount of time.

Timeouts protect:

* request workers
* connection resources
* memory
* throughput
* user latency
* overall service availability

A dedicated timeout test verifies that a deliberately slow operation is terminated when its deadline is exceeded.

---

# Request Validation

Requests are validated using Pydantic.

Example:

```json
{
  "model": "fast-model",
  "prompt": "Say hello in one sentence.",
  "temperature": 0.2,
  "max_tokens": 100
}
```

Validation includes constraints such as:

* required model
* required prompt
* temperature bounds
* positive token limits
* rejection of unexpected fields

The goal is to reject invalid input before it reaches the provider layer.

---

# Error Handling

The gateway establishes boundaries for several failure categories:

```text
Validation Failure
Authentication Failure
Rate-Limit Failure
Unknown Model
Provider Failure
Timeout
Internal Application Failure
```

Provider-specific implementation details remain inside the provider layer rather than being exposed directly through the API.

This creates a cleaner separation between:

```text
Client-facing API contract
```

and:

```text
Internal provider implementation
```

---

# Configuration & Secrets

Environment-specific configuration is kept outside application source code.

For example:

```text
GROQ_API_KEY
```

is loaded from the environment.

A local `.env` file can be used during development.

A corresponding `.env.example` documents the expected configuration without exposing real credentials.

### Never commit:

```text
GROQ_API_KEY=<real-secret>
```

to Git.

Groq's current documentation also recommends configuring the API key through an environment variable rather than embedding the key in application code.

---

# Technology Stack

| Technology | Purpose                              |
| ---------- | ------------------------------------ |
| Python     | Application language                 |
| FastAPI    | HTTP API framework                   |
| Pydantic   | Request/response validation          |
| Groq SDK   | LLM provider integration             |
| uv         | Python project/dependency management |
| pytest     | Automated testing                    |
| Uvicorn    | ASGI development server              |
| Git        | Version control                      |

FastAPI currently builds on Starlette for web functionality and Pydantic for data handling, and its current installation guidance supports `fastapi[standard]` with Uvicorn included in the standard server tooling.

The project uses `uv` with a committed `uv.lock` file. `uv` documents the lockfile as the exact resolved dependency set and recommends committing it for reproducible environments.

---

# Project Structure

The project is intentionally evolving.

The current structure separates responsibilities around:

```text
production-ai-inference-gateway/
│
├── app/
│   ├── main.py
│   │
│   ├── authorization.py
│   ├── model_selector.py
│   ├── model_service.py
│   ├── models.py
│   ├── routing.py
│   ├── provider_selector.py
│   ├── provider_service.py
│   ├── provider_execution.py
│   ├── rate_limit.py
│   ├── timeout.py
│   ├── schemas.py
│   │
│   └── providers/
│       ├── base.py
│       ├── factory.py
│       ├── registry.py
│       └── groq_provider.py
│
├── tests/
│   └── test_timeout.py
│
├── .env.example
├── .gitignore
├── .python-version
├── pyproject.toml
├── requirements.txt
├── uv.lock
└── README.md
```

The structure is expected to evolve as additional production capabilities are introduced.

---

# Running Locally

## Prerequisites

Install:

* Python
* uv
* Git
* a Groq API key

The project currently targets Python `>=3.12`.

---

## 1. Clone the repository

```bash
git clone https://github.com/Santa-Cruz1654/production-ai-inference-gateway.git
cd production-ai-inference-gateway
```

---

## 2. Configure the environment

Create a local `.env` file:

```env
GROQ_API_KEY=your_groq_api_key
```

Never commit this file.

---

## 3. Sync dependencies

```bash
uv sync
```

`uv` keeps the environment synchronized with the project's dependency configuration and lockfile.

---

## 4. Start the API

```bash
uv run uvicorn app.main:app --reload
```

The development server is available at:

```text
http://127.0.0.1:8000
```

---

# API

## Health Check

```http
GET /health
```

Example:

```bash
curl http://127.0.0.1:8000/health
```

Expected:

```json
{
  "status": "healthy"
}
```

---

## Inference

```http
POST /v1/inference
```

Example:

```bash
curl -X POST http://127.0.0.1:8000/v1/inference \
  -H "Authorization: Bearer gateway-dev-key" \
  -H "Content-Type: application/json" \
  -d "{\"model\":\"fast-model\",\"prompt\":\"Say hello in one sentence.\",\"temperature\":0.2,\"max_tokens\":100}"
```

Example response:

```json
{
  "request_id": "d611c655-3d99-4a46-9765-024b51a2156b",
  "model": "fast-model",
  "response": "Hello!"
}
```

The request ID and generated response will vary.

---

# Testing

Run the complete test suite:

```bash
uv run python -m pytest -v
```

Run the timeout test specifically:

```bash
uv run python -m pytest tests\test_timeout.py -v
```

The timeout test verifies that a slow operation is correctly terminated when its request deadline is exceeded.

---

# Day 1 Debugging Experience

Day 1 was deliberately developed through real implementation failures rather than building everything in one pass.

Several problems occurred.

## 1. Authentication dependency mismatch

The application initially attempted to import:

```text
require_user
```

from the authorization module when the expected implementation was not available.

This prevented the application from starting.

### Lesson

Refactoring a dependency chain requires validating every import and dependency boundary.

---

## 2. Circular Import

A refactoring introduced a dependency cycle:

```text
provider_selector
       ↓
providers.base
       ↓
schemas
       ↓
provider_selector
```

This produced a partially initialized module error.

### Lesson

A clean architecture is not about creating many files.

It is about creating **correct dependency direction**.

---

## 3. Missing Groq Configuration

The application initially failed because:

```text
GROQ_API_KEY
```

was not configured.

The application reported:

```text
GROQ_API_KEY is not configured
```

rather than silently constructing an unusable provider.

### Lesson

Configuration failures should be explicit and safe.

---

## 4. Logical Model vs Provider Model Confusion

An early request attempted to use:

```text
openai/gpt-oss-20b
```

as the gateway model.

The gateway returned:

```text
Unknown model: openai/gpt-oss-20b
```

The problem was architectural rather than provider-related.

The gateway expected:

```text
fast-model
```

while:

```text
openai/gpt-oss-20b
```

was the provider-level model identifier.

The routing layer performs that translation.

### Lesson

A provider gateway should distinguish:

```text
Application-facing model identity
```

from:

```text
Provider-specific model identity
```

---

## 5. Windows Shell Differences

Some commands behaved differently depending on whether they were executed through:

```text
PowerShell
```

or:

```text
Git Bash
```

### Lesson

The development shell is part of the execution environment.

Commands should be written for the shell actually being used.

---

## 6. Pytest Environment Problem

An initial test execution produced:

```text
ModuleNotFoundError: No module named 'app'
```

The problem was not the timeout implementation.

Pytest was being executed using a different Python environment.

The working command was:

```bash
uv run python -m pytest tests\test_timeout.py -v
```

which resulted in:

```text
tests/test_timeout.py::test_request_deadline_times_out_slow_operation PASSED

1 passed
```

### Lesson

When debugging Python projects, verify:

```text
Which Python?
Which pytest?
Which virtual environment?
Which dependencies?
```

before assuming the application code is broken.

---

# What Day 1 Actually Taught

The most important lesson was that building an LLM integration is not the difficult part.

Calling a provider API is relatively straightforward.

The engineering begins around that call.

Day 1 introduced practical experience with:

* API boundaries
* REST endpoint design
* Pydantic validation
* dependency injection
* provider abstraction
* adapter-style design
* model routing
* provider registries
* configuration management
* authentication
* rate limiting
* request correlation
* timeout/deadline handling
* error boundaries
* unit testing
* runtime testing
* Python dependency management
* environment isolation
* debugging
* dependency direction
* incremental architecture

The development process was:

```text
Design
  ↓
Implement
  ↓
Run
  ↓
Fail
  ↓
Inspect
  ↓
Understand
  ↓
Refactor
  ↓
Test
  ↓
Verify
```

That process is an important part of the project.

---

# Day 1 Engineering Principles

The project follows a simple rule:

> **Every component must solve a real engineering problem.**

The goal is not to add technologies merely to make the architecture look complicated.

For example:

```text
Redis
Kafka
PostgreSQL
Qdrant
Kubernetes
Celery
```

are not automatically valuable just because they are commonly used in production systems.

They should only be introduced when the system has a requirement that justifies them.

---

# What Is Not Implemented Yet

Day 1 establishes the foundation.

The following capabilities remain future work:

* bounded retry engine
* exponential backoff
* jitter
* retry budgets
* provider/model fallback
* streaming responses
* token usage tracking
* cost estimation
* structured production logging
* metrics
* distributed tracing
* OpenTelemetry integration
* persistent usage storage
* Redis-backed distributed rate limiting
* Dockerization
* CI/CD
* production secret management
* advanced authorization
* performance/load testing
* production deployment
* additional security hardening

These features will be introduced incrementally rather than all at once.

---

# Roadmap

```text
DAY 1
Architecture & Engineering Foundations
        │
        ▼
DAY 2
Reliability & Failure Handling
        │
        ▼
Retries
Timeouts
Fallbacks
Failure classification
        │
        ▼
DAY 3+
Streaming
Usage tracking
Observability
Performance
Security
Docker
CI/CD
Production hardening
```

The exact roadmap may evolve as implementation requirements become clearer.

---

# Engineering Philosophy

This project is not designed to maximize the number of technologies in the repository.

The guiding question is:

> **What engineering problem does this solve?**

The goal is to progressively transform:

```text
Simple LLM API wrapper
```

into:

```text
Reliable AI Infrastructure
```

through:

```text
Python
   +
Backend Engineering
   +
FastAPI
   +
API Design
   +
LLM Infrastructure
   +
Reliability Engineering
   +
Distributed Systems
   +
DevOps
   +
Security
   +
Observability
```

without introducing unnecessary complexity.

---

# Long-Term Goal

The final system should demonstrate more than the ability to call an LLM.

It should demonstrate the ability to reason about:

```text
Reliability
Scalability
Failure
Security
Latency
Cost
Observability
Provider portability
Testing
Deployment
```

The ultimate objective is to be able to answer:

> Why was this architecture chosen?

> What happens when a dependency fails?

> How would this scale?

> Where is the bottleneck?

> How was the failure path tested?

> What would change in production?

> Why is this abstraction necessary?

> What security risks exist?

That is the standard this project is being developed against.

---

# Current Status

🚧 **Actively under development**

### Day 1

**Architecture & Engineering Foundations — COMPLETE**

The initial gateway is running successfully with:

```text
FastAPI
   ↓
Authentication
   ↓
Rate Limiting
   ↓
Validation
   ↓
Model Resolution
   ↓
Provider Routing
   ↓
Provider Registry
   ↓
Groq Adapter
   ↓
LLM
   ↓
Normalized Response
```

The foundation is now ready for the next stage of reliability engineering.
