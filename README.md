# Production AI Inference Gateway

> An actively developed, production-oriented AI inference gateway built incrementally to explore reliable LLM infrastructure, backend engineering, system design, and AI platform engineering.

This project is being built as an engineering learning sprint rather than as a simple wrapper around an LLM API.

The goal is to understand what is required to move from:

```text
"Call an LLM API"
```

to:

```text
"Build a reliable backend service around LLM providers"
```

The system is being developed incrementally, with each stage introducing a deeper production engineering concept.

---

## Project Status

🚧 **Actively under development**

### Day 1 — Architecture & Engineering Foundations

**Completed**

* FastAPI application foundation
* Versioned inference endpoint
* Pydantic request/response validation
* Logical model abstraction
* Provider abstraction
* Groq provider adapter
* Provider registry
* Provider selection
* Model routing
* Authentication
* Rate limiting
* Request ID / correlation mechanism
* Explicit timeout/deadline handling
* Basic provider error boundaries
* Unit testing
* Runtime API testing
* Environment-based configuration
* Dependency-chain refactoring
* Initial production-oriented project structure

The project is intentionally **not considered complete**.

Future stages will build on this foundation with additional reliability, observability, deployment, and production-hardening capabilities.

---

# Why Build an Inference Gateway?

Directly integrating an application with an LLM provider is easy:

```text
Application
    ↓
LLM Provider
```

But production systems introduce additional problems:

* Which model should handle the request?
* What happens when the provider fails?
* What happens when the provider rate-limits us?
* How long should the application wait?
* How should requests be authenticated?
* How should clients be rate-limited?
* How do we switch providers without rewriting the application?
* How do we test provider-dependent code?
* How do we identify a request across different layers?
* What should be exposed to the client when something goes wrong?

This project explores those problems through implementation rather than treating them as purely theoretical system-design topics.

---

# Current Architecture

The current Day 1 architecture is intentionally small.

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
                  │ Model Service   │
                  │ / Model Select  │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ Provider        │
                  │ Service         │
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

The important architectural decision is that the application does **not** directly depend on the Groq SDK throughout the codebase.

Instead:

```text
Application
     │
     ▼
LLMProvider abstraction
     │
     ├── GroqProvider
     │
     ├── Future Provider
     │
     └── Future Local Provider
```

This keeps provider-specific implementation isolated.

---

# Request Lifecycle

A request to:

```text
POST /v1/inference
```

currently follows a controlled dependency chain.

```text
Client
  │
  ▼
Request ID middleware
  │
  ▼
Authentication
  │
  ▼
Rate limiting
  │
  ▼
Pydantic validation
  │
  ▼
Model resolution
  │
  ▼
Model constraints validation
  │
  ▼
Provider candidate resolution
  │
  ▼
Provider registry
  │
  ▼
Provider adapter
  │
  ▼
Groq API
  │
  ▼
Provider response normalization
  │
  ▼
Gateway response
```

This separation became an important part of Day 1.

Rather than putting the entire request flow inside a single FastAPI route, responsibilities were progressively separated into services and abstractions.

---

# Core Engineering Concepts

Day 1 focused on the foundations required before adding more advanced distributed-system behaviour.

## 1. API Design

The gateway exposes a versioned inference endpoint:

```text
POST /v1/inference
```

Basic service endpoints:

```text
GET /
GET /health
```

The API uses structured request and response schemas.

---

## 2. Request Validation

Requests are validated using Pydantic.

The inference request currently contains:

```json
{
  "model": "fast-model",
  "prompt": "Say hello in one sentence.",
  "temperature": 0.2,
  "max_tokens": 100
}
```

Validation covers constraints such as:

* required model
* required prompt
* temperature bounds
* positive token limits
* rejection of unexpected request fields

This prevents malformed requests from reaching the provider layer.

---

# 3. Logical Model Abstraction

The gateway exposes logical models rather than forcing clients to know provider-specific model identifiers.

For example:

```text
fast-model
quality-model
reasoning-model
```

The gateway internally maps these logical models to provider configurations.

Conceptually:

```text
Client
  │
  │ "fast-model"
  ▼
Gateway
  │
  ▼
Model Registry
  │
  ▼
Provider Routing
  │
  ▼
Groq
  │
  ▼
Provider Model
```

This creates a separation between:

```text
Application-facing model identity
```

and:

```text
Provider-specific model identity
```

---

# 4. Provider Abstraction

One of the main architectural goals of Day 1 was avoiding provider-specific code throughout the application.

The gateway defines a provider abstraction:

```text
LLMProvider
```

The Groq implementation provides the concrete adapter:

```text
GroqProvider
```

The application can therefore interact with the provider through a common interface.

Conceptually:

```text
LLMProvider
     │
     └── GroqProvider
```

Future providers can be introduced without rewriting the entire inference pipeline.

---

# 5. Provider Registry

Providers are registered through a provider registry.

Conceptually:

```text
ProviderRegistry

groq → GroqProvider
```

The registry separates:

* provider registration
* provider lookup
* provider implementation

This also creates a clean boundary for testing and future provider expansion.

---

# 6. Provider Selection

Provider selection is separated from the API route.

The current routing model is intentionally simple.

A logical model can map to one or more provider candidates:

```text
fast-model
    ↓
Groq
    ↓
openai/gpt-oss-20b
```

The provider-specific model identifier is therefore not scattered throughout the application.

---

# 7. Configuration

Secrets and environment-specific configuration are kept outside the application source code.

For example:

```text
GROQ_API_KEY
```

is loaded from the environment.

A real API key should never be committed to Git.

A `.env` file is used locally, while `.env.example` is intended to document the expected configuration without containing real secrets.

---

# 8. Authentication

The inference endpoint requires an authenticated request.

The current development authentication flow uses an API-key-style bearer token.

Example:

```text
Authorization: Bearer gateway-dev-key
```

The important architectural distinction is:

```text
Authentication
    =
Who are you?
```

versus:

```text
Authorization
    =
What are you allowed to do?
```

Day 1 establishes the authentication boundary.

More advanced identity, tenant management, key rotation, and authorization policies are future work.

---

# 9. Rate Limiting

The gateway includes request rate limiting as an early protection mechanism.

The purpose is not merely performance.

Rate limiting helps protect:

* provider quotas
* application resources
* infrastructure
* downstream services
* cost
* availability

This also introduced an important production concept:

> A gateway is a control point between clients and expensive downstream dependencies.

A future production implementation can evolve toward distributed rate limiting backed by Redis.

That is intentionally not required for the current minimal architecture.

---

# 10. Request IDs

The gateway generates or accepts a request identifier.

Conceptually:

```text
Client
  │
  │ X-Request-ID
  ▼
Gateway
  │
  ├── request processing
  ├── provider call
  └── response
```

The request ID is returned through the response and provides a correlation mechanism for future logging and observability.

This becomes increasingly important when the system eventually contains:

```text
API
 ↓
Router
 ↓
Provider
 ↓
External API
```

because a single request can cross multiple components.

---

# 11. Timeouts

External dependencies should not be allowed to wait indefinitely.

Day 1 introduced explicit request-deadline handling and tested the timeout behaviour independently.

The key principle is:

```text
No external dependency should be allowed
to consume an unlimited amount of time.
```

A timeout protects:

* request workers
* connection pools
* memory
* throughput
* user latency
* overall service availability

A dedicated timeout test was added to verify that a slow operation is correctly terminated when its deadline is exceeded.

---

# 12. Error Handling

The gateway distinguishes between different classes of failures rather than treating every failure as the same.

Examples include:

```text
Validation failure
Authentication failure
Rate-limit failure
Unknown model
Provider failure
Timeout
Internal application error
```

The architecture keeps provider-specific behaviour inside the provider layer instead of exposing raw SDK implementation details to the API layer.

---

# 13. Testing

Testing is part of the implementation rather than something added at the end.

Day 1 included:

* unit testing
* timeout testing
* request validation testing
* runtime endpoint testing
* provider integration testing

The project also demonstrated why the environment in which tests are executed matters.

A direct command initially produced:

```text
ModuleNotFoundError: No module named 'app'
```

when pytest was invoked using the wrong Python environment.

The corrected invocation was:

```bash
uv run python -m pytest tests\test_timeout.py -v
```

which produced:

```text
1 passed
```

This was an important debugging lesson:

> A failing test does not necessarily mean the application code is wrong.

The execution environment itself can be the problem.

---

# Development Environment

The project currently uses:

* Python
* FastAPI
* Pydantic
* Groq SDK
* pytest
* uv

Python dependencies are managed through the project configuration and lockfile.

The environment is intentionally reproducible through the project tooling rather than relying on globally installed packages.

---

# Running Locally

## 1. Clone the repository

```bash
git clone <repository-url>
cd production-ai-inference-gateway
```

## 2. Create/configure the environment

Create a local environment configuration containing:

```text
GROQ_API_KEY=<your-groq-api-key>
```

Do not commit the real `.env` file.

---

## 3. Install dependencies

Using `uv`:

```bash
uv sync
```

---

## 4. Start the API

```bash
uv run uvicorn app.main:app --reload
```

The development server runs at:

```text
http://127.0.0.1:8000
```

---

# Health Check

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{
  "status": "healthy"
}
```

---

# Inference Request

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

The exact request ID and model response will naturally vary.

---

# Testing

Run the test suite with:

```bash
uv run python -m pytest -v
```

For the timeout test specifically:

```bash
uv run python -m pytest tests\test_timeout.py -v
```

---

# Important Day 1 Debugging Lessons

Day 1 was not a straight-line implementation.

Several real implementation problems occurred during development.

## Authentication dependency mismatch

The application initially attempted to import:

```text
require_user
```

from the authorization module even though the expected implementation was not available.

This caused the application to fail during startup.

### Lesson

Application dependency chains need to be validated after refactoring.

---

## Circular import

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

This resulted in:

```text
ImportError:
cannot import name 'ProviderSelector'
from partially initialized module
```

The solution was to separate the schema layer from the provider-selection layer.

### Lesson

Dependency direction matters.

A clean architecture is not only about having many files; it is about ensuring that dependencies flow in a sensible direction.

---

## Missing provider configuration

The application also failed when:

```text
GROQ_API_KEY
```

was not configured.

The application correctly surfaced:

```text
GROQ_API_KEY is not configured
```

rather than silently creating an unusable provider.

### Lesson

Configuration failures should be explicit and fail safely.

---

## Logical model vs provider model

An early runtime request used:

```text
openai/gpt-oss-20b
```

as the gateway model.

The gateway rejected it with:

```text
Unknown model: openai/gpt-oss-20b
```

The reason was that:

```text
openai/gpt-oss-20b
```

is the provider-level model identifier, while the gateway expects logical models such as:

```text
fast-model
quality-model
reasoning-model
```

The routing layer then maps the logical model to the provider model.

### Lesson

A gateway should distinguish between:

```text
logical application model
```

and:

```text
provider-specific model identifier
```

---

## PowerShell / Git Bash command differences

Some debugging commands were also affected by the difference between Windows shells.

A command written for one shell could fail when copied directly into another.

### Lesson

The command environment is part of the development environment.

---

## Test environment mismatch

Running:

```bash
uv run pytest
```

initially resulted in pytest using a different Python installation and failing to import the application package.

Running:

```bash
uv run python -m pytest
```

correctly used the project's environment.

### Lesson

Always verify:

```text
Which Python?
Which pytest?
Which environment?
Which dependency installation?
```

before assuming a code failure.

---

# What Day 1 Taught Me

The main lesson from Day 1 was that production engineering starts **around** the core functionality.

Calling an LLM is relatively simple.

Building the boundaries around that call is where the engineering becomes interesting.

The project introduced practical experience with:

* API boundaries
* dependency injection
* abstraction
* provider adapters
* model routing
* configuration
* authentication
* rate limiting
* timeouts
* request correlation
* error handling
* testing
* debugging
* dependency management
* environment isolation

Most importantly, the project was deliberately developed through:

```text
Design
   ↓
Implementation
   ↓
Runtime failure
   ↓
Diagnosis
   ↓
Refactoring
   ↓
Testing
   ↓
Working system
```

rather than attempting to produce a large codebase in one pass.

---

# Current Limitations

This is **not yet a complete production gateway**.

The following areas remain future work:

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
* load/performance testing
* production deployment
* security hardening

These will be introduced only when there is an engineering reason for them.

---

# Development Roadmap

## Day 1 — Architecture & Engineering Foundations

✅ FastAPI gateway
✅ Request validation
✅ Model abstraction
✅ Provider abstraction
✅ Provider registry
✅ Provider routing
✅ Groq integration
✅ Authentication
✅ Rate limiting
✅ Request IDs
✅ Timeout handling
✅ Initial error handling
✅ Unit/runtime testing
✅ Environment configuration



# Repository Structure

The project is intentionally evolving.

The current structure separates responsibilities around:

```text
app/
├── authorization
├── model selection / resolution
├── provider selection
├── provider service
├── provider execution
├── routing
├── rate limiting
├── timeout handling
├── schemas
├── models
├── providers/
│   ├── base
│   ├── registry
│   ├── factory
│   └── Groq provider
└── main application
```

The structure will continue to evolve as the system becomes more capable.

---

# Design Philosophy

This project is not being built to maximize the number of technologies in the stack.

The guiding question for every new component is:

> **What engineering problem does this solve?**

The goal is to progressively transform a simple LLM API wrapper into a system that demonstrates:

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
Distributed Systems Concepts
    +
DevOps
    +
Security
    +
Observability
```

without introducing unnecessary complexity.

---

# Learning Objective

By the end of the project, I want to be able to explain not only:

> "How does this code work?"

but also:

> "Why is it designed this way?"

> "What happens when this dependency fails?"

> "How would this scale?"

> "Where is the bottleneck?"

> "What would I change for production?"

> "Why did I choose this abstraction?"

> "How did I test the failure path?"

> "What security risks exist?"

That is the standard this project is being developed against.

---

# Status

🚧 **Active development**

Day 1 establishes the architectural foundation.

The system will continue evolving incrementally as new reliability, observability, deployment, and security requirements are introduced.
