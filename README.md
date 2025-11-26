# AI-Powered Recipe Chatbot

A full-stack LLM-powered cooking and recipe Q&A application built with FastAPI (backend) and Next.js (frontend). The system uses LangGraph for intelligent workflow orchestration, enabling the LLM to decide when to research recipes, validate cookware availability, and provide helpful cooking guidance.

## Features

- **Intelligent Query Classification**: Automatically categorizes queries as cooking-related or irrelevant
- **LLM-Driven Research**: The LLM decides when to use web search for recipe information
- **Cookware Validation**: Verifies if users have the required tools to prepare suggested recipes
- **Streaming Responses**: Real-time Server-Sent Events (SSE) for progressive response delivery
- **Conversation Management**: Persistent conversation history with SQLite storage
- **Modern UI**: Next.js 16 with React 19, Tailwind CSS, and dark mode support
- **Offline-First Frontend**: IndexedDB caching with Dexie for instant conversation loading

## Architecture

### System Overview

```
+------------------+         +--------------------------------------+
|   Next.js UI     |<------->|          FastAPI Backend             |
|  (Port 3000)     |  HTTP   |          (Port 8000)                 |
+------------------+         +--------------------------------------+
      |                                      |
      | IndexedDB                            |
      | (Dexie)                              v
      |                     +------------------------------------+
      |                     |        LangGraph Workflow          |
      |                     |                                    |
      |                     |  +------------------------------+  |
      |                     |  |   1. Classifier Node         |  |
      |                     |  |   (GPT-4o-mini)              |  |
      |                     |  +--------------+---------------+  |
      |                     |                 |                  |
      |                     |        +--------v--------+          |
      |                     |        |  Is Relevant?   |          |
      |                     |        +-+-------------+-+          |
      |                     |          | No          | Yes        |
      |                     |          |             |            |
      |                     |  +-------v------+    +-v---------+  |
      |                     |  |  Refusal     |    |  Decide   |  |
      |                     |  |    Node      |    |  Search   |  |
      |                     |  +--------------+    +-----+-----+  |
      |                     |                            |        |
      |                     |                  +---------v------+ |
      |                     |                  | Needs Search?  | |
      |                     |                  +--+----------+--+ |
      |                     |                     | Yes      | No |
      |                     |                +----v---+      |    |
      |                     |                | Search |      |    |
      |                     |                |  Node  |      |    |
      |                     |                |(Tavily)|      |    |
      |                     |                +----+---+      |    |
      |                     |                     |          |    |
      |                     |                +----v----------v--+ |
      |                     |                |   Cookware Check | |
      |                     |                +----------+-------+ |
      |                     |                           |         |
      |                     |                +----------v-------+ |
      |                     |                |   Response Node  | |
      |                     |                |   (GPT-4o-mini)  | |
      |                     |                +------------------+ |
      |                     +------------------------------------+
      |                                      |
      |                                      v
      +------------------>  +------------------+
                            |   SQLite DB      |
                            |   - Conversations|
                            |   - Messages     |
                            |   - Checkpoints  |
                            +------------------+
```

### LangGraph Workflow

The system uses a state-based graph with conditional routing:

1. **Classifier Node**: Analyzes the query using GPT-4o-mini to determine relevance, query type, and extract dish details
2. **Refusal Node**: Politely declines non-cooking queries
3. **Decide Search Node**: Determines if web search is needed based on query type
4. **Search Node**: Uses Tavily API to fetch relevant recipe information
5. **Cookware Verification Node**: Validates against available cookware (Spatula, Frying Pan, Little Pot, Stovetop, Whisk, Knife, Ladle, Spoon)
6. **Response Node**: Generates the final answer using GPT-4o-mini with full context

## Prerequisites

- **Python**: 3.11 or higher
- **Node.js**: 20.x or higher
- **Docker & Docker Compose**: For containerized deployment
- **API Keys**:
  - OpenAI API key (for GPT-4o-mini)
  - Tavily API key (for web search)

## Local Development Setup

### Option 1: Docker Compose (Recommended)

1. **Set up environment variables**:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
OPENAI_API_KEY=sk-proj-your_openai_api_key_here
TAVILY_API_KEY=tvly-your_tavily_api_key_here
```

2. **Start the application**:

```bash
docker-compose up --build
```

3. **Access the application**:

   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

4. **Stop the application**:

```bash
docker-compose down
```

### Option 2: Local Development (Without Docker)

#### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

export OPENAI_API_KEY=sk-proj-your_key_here
export TAVILY_API_KEY=tvly-your_key_here
export DATABASE_URL=sqlite:///./data/conversations.db

uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup

```bash
cd frontend
npm install  # or bun install

echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

npm run dev  # or bun dev
```

Access: http://localhost:3000

## API Documentation

### Key Endpoints

**Health Check:**

```bash
GET /health
```

**Send Cooking Query (Non-Streaming):**

```bash
curl -X POST http://localhost:8000/api/cooking \
  -H "Content-Type: application/json" \
  -d '{"query": "How do I make pasta carbonara?"}'
```

**Send Cooking Query (Streaming):**

```bash
curl -N -X POST http://localhost:8000/api/cooking/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "What can I cook with eggs and cheese?", "thread_id": "test-123"}'
```

**Get All Conversations:**

```bash
curl http://localhost:8000/api/conversations
```

**Get Conversation by ID:**

```bash
curl http://localhost:8000/api/conversations/test-123
```

**Delete Conversation:**

```bash
curl -X DELETE http://localhost:8000/api/conversations/test-123
```

Full API documentation available at http://localhost:8000/docs when running the backend.

## Usage Examples

### Example 1: Recipe Request

**Query:** "How do I make pizza?"

**Flow:** Classifier -> Search (Tavily) -> Cookware Check -> Response

**Response:** Detailed pizza recipe with dough instructions, noting that you have all required tools.

### Example 2: Ingredient Query

**Query:** "What can I cook with eggs, milk, and flour?"

**Flow:** Classifier -> Search -> Cookware Check -> Response

**Response:** Suggests pancakes, crepes, French toast - all feasible with available cookware.

### Example 3: General Cooking Question

**Query:** "What's the difference between boiling and simmering?"

**Flow:** Classifier -> No Search -> Response (uses LLM knowledge)

**Response:** Explains temperature differences without web search.

### Example 4: Irrelevant Query

**Query:** "What's the weather today?"

**Flow:** Classifier -> Refusal

**Response:** Polite decline, explaining it's a cooking assistant.

## AWS Deployment Plan

### Architecture

- **Compute**: ECS Fargate (auto-scaling containers)
- **Database**: RDS PostgreSQL (Multi-AZ, replacing SQLite)
- **Secrets**: AWS Secrets Manager (API keys, DB credentials)
- **Load Balancing**: Application Load Balancer (ALB) with HTTPS
- **Observability**: CloudWatch Logs + X-Ray tracing
- **Networking**: VPC with public/private subnets
- **CI/CD**: CodePipeline -> ECR -> ECS rolling updates

### Key Components

**ECS Fargate:**

- Backend: 2-10 tasks (auto-scale on CPU > 70%)
- Frontend: 2-6 tasks
- Health checks on `/health` endpoint

**RDS PostgreSQL:**

- Instance: db.t4g.medium (Multi-AZ)
- Automated backups (7-day retention)
- Read replicas for conversation queries

**Secrets Manager:**

- Automatic rotation (90 days)
- Fine-grained IAM per ECS task

**Monitoring:**

- Structured JSON logging
- Custom metrics (query types, search rate, latency)
- SNS alerts for 5xx errors, high latency

## Security & Authentication Plan

### Planned Implementation

**Authentication:**

- JWT tokens with httpOnly cookies
- 24-hour access tokens, 7-day refresh tokens
- FastAPI dependency injection for protected routes

**Authorization:**

- Row-level security (conversations filtered by user_id)
- API Gateway rate limiting (50 req/s per key)
- Backend rate limiting (20 req/min per IP)

**Input Validation:**

- Pydantic models with strict validation
- Prompt injection detection (regex patterns)
- OpenAI content moderation API
- HTML sanitization on frontend

**CORS:**

- Environment-specific origins (localhost for dev, production domain for prod)
- Credentials allowed, max age 1 hour

**Secrets:**

- AWS Secrets Manager in production
- Automatic rotation every 90 days
- ECS task IAM roles (no hardcoded keys)

**HTTPS:**

- TLS 1.3 only via ALB
- ACM certificates (auto-renewal)
- HTTP -> HTTPS redirect

## ELT Integration Plan

### Data Pipeline

**Extract:**

- AWS DMS for CDC from RDS PostgreSQL
- Real-time replication to S3 data lake
- Tables: conversations, messages, recipe_events

**Load:**

- S3 raw layer (Parquet format, partitioned by date)
- AWS Glue Data Catalog for schema discovery

**Transform:**

- AWS Glue ETL jobs (PySpark)
- Aggregate to curated layer:
  - Recipe popularity (daily views, unique users)
  - Cookware usage patterns (most limiting tools)
  - Search effectiveness (trigger rate by query type)
  - User engagement (avg messages, duration)

**Analytics:**

- Amazon Athena for ad-hoc queries
- Redshift data warehouse for BI
- QuickSight dashboards:
  - Recipe Insights (top recipes, trends)
  - Cookware Analysis (usage frequency, availability)
  - User Engagement (KPIs, funnels)
  - Search Effectiveness (correlation analysis)

**Metrics Tracked:**

- Recipe popularity (dish name frequency)
- Cookware usage patterns (which tools are most needed)
- Search vs no-search decisions (by query type)
- User engagement (messages per conversation, duration)
- Time-series trends (daily/weekly/monthly)

## Design Decisions

### Why LangGraph?

- Conditional routing based on query classification
- State persistence for conversation history
- Visible decision flow for debugging
- Easy to add new nodes (substitutions, nutrition)

### Why Tavily?

- LLM-optimized content (not just snippets)
- Designed for RAG use cases
- Cost-effective ($1/1000 searches)
- Better recipe-specific results than generic search

### Why SQLite (dev) -> PostgreSQL (prod)?

- SQLite: Zero config, single file, perfect for local dev
- PostgreSQL: Concurrent writes, JSON indexing, full-text search
- SQLAlchemy makes migration trivial (change one line)

## Edge Cases & Limitations

1.
2. **Ambiguous ingredient names**: LLM interprets contextually but might guess wrong (e.g., "tomato sauce" variations)
3. **Non-English queries**: GPT-4o-mini handles multilingual input, but Tavily might return English results
4. **Context window limits**: Only last 6 messages used; longer conversations lose early context
5. **SERP rate limits**: Tavily free tier limits; no retry logic or circuit breaker yet
6. **Metric/imperial conversions**: Not automatically converted
7. **Dietary restrictions & allergens**: No user profile system to track restrictions
8. **Recipe difficulty**: Doesn't assess complexity or warn beginners
9. **Ingredient quantity scaling**: Doesn't adjust for serving size
10. **Cooking time filtering**: No structured time extraction or filtering

### Implemented (Core Functionality)

- LangGraph workflow with 5 nodes + conditional routing
- Query classification and cookware validation
- Tavily web search integration
- Conversation persistence with SQLite
- Streaming responses via SSE
- Full-stack integration (backend + frontend)
- Docker containerization

### Next Steps (If More Time)

1. Better prompts
2. Error handling (retries, circuit breakers)
3. Monitoring (structured logging, metrics, tracing)
4. Improve User Experience
5. UI polish (animations, mobile responsive)
6. Database migrations (Alembic)
7. Testing suite (pytest + E2E)

## AI Tooling Used

- **Claude (Anthropic)**: Architecture design and documentation

All core logic, design decisions, and architecture choices were made by the developer. AI tools accelerated implementation but did not drive technical decisions.

## Troubleshooting

**Backend won't start**: Check API keys in `.env`, ensure port 8000 is free
**Frontend won't start**: Run `npm install` or `bun install`
**Database locked**: SQLite doesn't handle concurrent writes well; use PostgreSQL for production
**Streaming not working**: Check CORS allows `text/event-stream`, fallback to non-streaming endpoint
**Rate limiting**: Tavily free tier is 10 req/s; add caching or upgrade

## License

This project was created as an assessment for an AI Engineering role.

---

**Stack:** FastAPI • LangGraph • LangChain • Next.js • React • Tailwind CSS • SQLite • Docker
