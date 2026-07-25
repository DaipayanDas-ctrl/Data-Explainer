"""
Data Explainer — backend

This is intentionally small. The PRD's heavy lifting (parsing, PII scrubbing,
profiling, anomaly detection, correlation, forecasting) all happens client-side
in the browser, deterministically, in plain JavaScript — nothing raw ever
needs to leave the machine running the frontend.

The ONE thing that genuinely needs a backend is the call to the LLM: it needs
a real API key, and a browser can't hold one without exposing it to anyone
who opens devtools. So this service does exactly one job: accept an already-
built (system_prompt, user_prompt) pair — which by construction only ever
contains computed statistics, never raw rows — and forward it to whichever
LLM provider you've configured, then hand the text response back.

Supports Anthropic (Claude) and Groq (Llama) — pick one with LLM_PROVIDER
in .env. The frontend doesn't know or care which provider is behind this;
it always just calls POST /api/claude with {system, prompt, max_tokens}.

Run:
    pip install -r requirements.txt
    cp .env.example .env      # then fill in your key(s) and pick a provider
    uvicorn main:app --reload --port 8000
"""

import os
import logging
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import json
import jwt

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Load .env for local development if available (optional in production)
if os.path.exists(".env"):
    load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("data-explainer")


def resolve_secret(key_name: str) -> str | None:
    """
    Resolves secrets cleanly across multiple environments in priority order:
    1. Direct environment variable (injected by ECS Task Definition, Lambda, App Runner, etc.)
    2. AWS Secrets Manager (if AWS_SECRET_NAME env var is set)
    3. AWS SSM Parameter Store (if AWS_SSM_PARAMETER_NAME or AWS_SSM_<KEY_NAME> is set)
    4. Local .env file fallback
    """
    val = os.getenv(key_name)
    if val and not any(val.startswith(p) for p in ("sk-ant-your", "gsk_your", "your-gemini")):
        return val

    aws_secret_name = os.getenv("AWS_SECRET_NAME")
    if aws_secret_name:
        try:
            import boto3
            region = os.getenv("AWS_REGION", "us-east-1")
            client = boto3.client("secretsmanager", region_name=region)
            resp = client.get_secret_value(SecretId=aws_secret_name)
            if "SecretString" in resp:
                secret_data = resp["SecretString"]
                try:
                    secret_dict = json.loads(secret_data)
                    if key_name in secret_dict:
                        return secret_dict[key_name]
                except Exception:
                    return secret_data
        except Exception as e:
            log.warning("Failed to fetch secret '%s' from AWS Secrets Manager: %s", aws_secret_name, e)

    ssm_param_name = os.getenv(f"AWS_SSM_{key_name}") or os.getenv("AWS_SSM_PARAMETER_NAME")
    if ssm_param_name:
        try:
            import boto3
            region = os.getenv("AWS_REGION", "us-east-1")
            client = boto3.client("ssm", region_name=region)
            resp = client.get_parameter(Name=ssm_param_name, WithDecryption=True)
            return resp.get("Parameter", {}).get("Value")
        except Exception as e:
            log.warning("Failed to fetch parameter '%s' from AWS SSM: %s", ssm_param_name, e)

    return val


LLM_PROVIDER = os.getenv("LLM_PROVIDER", "anthropic").strip().lower()  # "anthropic" | "groq"

ANTHROPIC_API_KEY = resolve_secret("ANTHROPIC_API_KEY")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5")

GROQ_API_KEY = resolve_secret("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

raw_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5500,http://127.0.0.1:5500,http://localhost:8080,http://127.0.0.1:8080",
)
ALLOWED_ORIGINS = [o.strip() for o in raw_origins.split(",") if o.strip()]

# Security enforcement: Reject wildcard origins to mandate exact frontend origin matching
if "*" in ALLOWED_ORIGINS:
    logging.warning("CORS Security Alert: Wildcard '*' found in ALLOWED_ORIGINS. Removing '*' to enforce exact origin matching.")
    ALLOWED_ORIGINS = [o for o in ALLOWED_ORIGINS if o != "*"]

raw_headers = os.getenv("ALLOWED_HEADERS", "Content-Type,Authorization,Accept")
ALLOWED_HEADERS = [h.strip() for h in raw_headers.split(",") if h.strip()]

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("data-explainer")

app = FastAPI(title="Data Explainer API", version="1.1.0")

RATE_LIMIT_PER_MINUTE = os.getenv("RATE_LIMIT_PER_MINUTE", "15/minute")
limiter = Limiter(key_func=get_remote_address, default_limits=[RATE_LIMIT_PER_MINUTE])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

REQUIRE_CLIENT_AUTH = os.getenv("REQUIRE_CLIENT_AUTH", "false").strip().lower() in ("true", "1", "yes")
CLIENT_API_KEY = resolve_secret("CLIENT_API_KEY")
JWT_SECRET = resolve_secret("JWT_SECRET")

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_auth(request: Request, api_key: str = Security(api_key_header)):
    if REQUIRE_CLIENT_AUTH or CLIENT_API_KEY or JWT_SECRET:
        auth_header = request.headers.get("Authorization")
        bearer_token = None
        if auth_header and auth_header.startswith("Bearer "):
            bearer_token = auth_header.split(" ", 1)[1].strip()

        if CLIENT_API_KEY and (api_key == CLIENT_API_KEY or bearer_token == CLIENT_API_KEY):
            return True

        if JWT_SECRET and bearer_token:
            try:
                algorithm = os.getenv("JWT_ALGORITHM", "HS256")
                payload = jwt.decode(bearer_token, JWT_SECRET, algorithms=[algorithm])
                request.state.user = payload
                return True
            except Exception as e:
                raise HTTPException(status_code=401, detail=f"Invalid JWT authentication token: {e}")

        raise HTTPException(
            status_code=401,
            detail="Unauthorized: Valid X-API-Key or Authorization Bearer token is required.",
        )
    return True


app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,  # Kept False unless real session auth is added
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=ALLOWED_HEADERS,
)

# AWS ALB / CloudFront / API Gateway HTTPS Proxy Header Support
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")
app.add_middleware(GZipMiddleware, minimum_size=500)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# In-memory TTL Response Cache for LLM calls
import hashlib
import time

_llm_cache: dict[str, tuple[float, str]] = {}
CACHE_TTL_SECONDS = 600

def _get_cached_response(key_str: str) -> str | None:
    h = hashlib.sha256(key_str.encode("utf-8")).hexdigest()
    if h in _llm_cache:
        ts, val = _llm_cache[h]
        if time.time() - ts < CACHE_TTL_SECONDS:
            log.info("Serving LLM response from in-memory TTL cache (hash=%s)", h[:8])
            return val
        del _llm_cache[h]
    return None

def _set_cached_response(key_str: str, response_text: str):
    h = hashlib.sha256(key_str.encode("utf-8")).hexdigest()
    _llm_cache[h] = (time.time(), response_text)

# --- provider clients, only the selected one actually needs to import/init cleanly ---

_anthropic_client = None
_groq_client = None

if LLM_PROVIDER == "anthropic":
    import anthropic
    _anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None
elif LLM_PROVIDER == "groq":
    import groq
    _groq_client = groq.Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
else:
    raise RuntimeError(f"Unknown LLM_PROVIDER '{LLM_PROVIDER}' — use 'anthropic' or 'groq'")

class AuditLogManager:
    """
    Production Audit Logger:
    1. Emits structured JSON logs for AWS CloudWatch Logs & CloudWatch Insights querying.
    2. Persists & retrieves entries via AWS DynamoDB if AUDIT_LOG_TABLE_NAME is configured.
    3. Maintains in-memory fallback for local dev when DynamoDB is unconfigured.
    """
    def __init__(self):
        self._local_log: list[dict] = []
        self.table_name = os.getenv("AUDIT_LOG_TABLE_NAME") or os.getenv("AWS_DYNAMODB_TABLE")
        self._dynamodb_table = None
        if self.table_name:
            try:
                import boto3
                region = os.getenv("AWS_REGION", "us-east-1")
                dynamodb = boto3.resource("dynamodb", region_name=region)
                self._dynamodb_table = dynamodb.Table(self.table_name)
            except Exception as e:
                log.warning("Failed to initialize DynamoDB table '%s': %s", self.table_name, e)

    def record(self, entry: dict):
        # Always emit structured JSON for CloudWatch Logs & CloudWatch Insights
        log.info("[AUDIT_LOG] %s", json.dumps(entry))
        self._local_log.append(entry)

        if self._dynamodb_table:
            try:
                import uuid
                item = {**entry, "id": str(uuid.uuid4())}
                self._dynamodb_table.put_item(Item=item)
            except Exception as e:
                log.error("Failed to write audit entry to DynamoDB: %s", e)

    def get_entries(self, limit: int = 200) -> list[dict]:
        if self._dynamodb_table:
            try:
                resp = self._dynamodb_table.scan(Limit=limit)
                items = resp.get("Items", [])
                items.sort(key=lambda x: x.get("time", ""), reverse=True)
                return items
            except Exception as e:
                log.error("Failed to fetch audit log from DynamoDB: %s", e)
        return self._local_log[-limit:]

audit_logger = AuditLogManager()


class ClaudeRequest(BaseModel):
    system: str = Field(..., max_length=50000, description="System prompt — built entirely from computed stats, max 50KB")
    prompt: str = Field(..., max_length=50000, description="User prompt — max 50KB")
    max_tokens: int = Field(default=1000, ge=1, le=4096)


# Type aliases for provider-neutral and Groq-specific naming
GroqRequest = ClaudeRequest
LLMRequest = ClaudeRequest


class ClaudeResponse(BaseModel):
    text: str


GroqResponse = ClaudeResponse
LLMResponse = ClaudeResponse


class PIIField(BaseModel):
    name: str
    reason: str
    confidence: str = Field(..., pattern="^(high|medium|low)$")


class PIIReport(BaseModel):
    dropped_columns: list[str]
    retained_columns: list[str]
    flags: list[PIIField]


def _call_anthropic(system: str, prompt: str, max_tokens: int) -> str:
    if not _anthropic_client:
        raise HTTPException(
            status_code=500,
            detail="ANTHROPIC_API_KEY is not configured on the server. Set it in .env.",
        )
    cache_key = f"anthropic:{CLAUDE_MODEL}:{max_tokens}:{system}:{prompt}"
    cached = _get_cached_response(cache_key)
    if cached:
        return cached

    import anthropic
    try:
        response = _anthropic_client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
    except anthropic.APIStatusError as e:
        log.error("Anthropic API error: %s", e)
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        log.error("Unexpected error calling Claude: %s", e)
        raise HTTPException(status_code=502, detail=f"Upstream call failed: {e}")

    text = "".join(block.text for block in response.content if getattr(block, "type", None) == "text")
    _set_cached_response(cache_key, text)
    return text


def _call_groq(system: str, prompt: str, max_tokens: int) -> str:
    if not _groq_client:
        raise HTTPException(
            status_code=500,
            detail="GROQ_API_KEY is not configured on the server. Set it in .env.",
        )
    cache_key = f"groq:{GROQ_MODEL}:{max_tokens}:{system}:{prompt}"
    cached = _get_cached_response(cache_key)
    if cached:
        return cached

    import time
    last_err = None
    for attempt in range(3):
        try:
            response = _groq_client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
            )
            text = response.choices[0].message.content
            if text is None:
                raise HTTPException(
                    status_code=502,
                    detail="Groq returned no text.",
                )
            _set_cached_response(cache_key, text)
            return text
        except HTTPException:
            raise
        except Exception as e:
            last_err = e
            err_str = str(e)
            # 429 rate-limit: back off and retry with longer waits
            if "429" in err_str or "rate_limit" in err_str.lower():
                wait = [5, 10, 20][attempt]
                log.warning("Groq 429 rate-limit hit, waiting %ss before retry %s/3", wait, attempt + 1)
                time.sleep(wait)
                continue
            log.error("Unexpected error calling Groq: %s", e)
            raise HTTPException(status_code=502, detail=f"Upstream call failed: {e}")

    log.error("Groq rate-limit retries exhausted: %s", last_err)
    raise HTTPException(
        status_code=429,
        detail="Groq API rate limit exceeded. Wait a moment and try again.",
    )



EXPOSE_HEALTH_DETAILS = os.getenv("EXPOSE_HEALTH_DETAILS", "false").strip().lower() in ("true", "1", "yes")


@app.get("/api/health")
def health(details: bool = False):
    # Public health check returns minimal status to prevent infrastructure fingerprinting
    if not (details and EXPOSE_HEALTH_DETAILS):
        return {"status": "ok"}
    if LLM_PROVIDER == "anthropic":
        return {"status": "ok", "provider": "anthropic", "model": CLAUDE_MODEL, "key_configured": bool(ANTHROPIC_API_KEY)}
    return {"status": "ok", "provider": "groq", "model": GROQ_MODEL, "key_configured": bool(GROQ_API_KEY)}


@app.get("/api/audit-log")
def get_audit_log():
    return {"entries": audit_logger.get_entries(limit=200)}


class StructuredInsightRequest(BaseModel):
    system: str = Field(..., max_length=50000, description="System prompt — max 50KB")
    prompt: str = Field(..., max_length=50000, description="User prompt — max 50KB")
    max_tokens: int = Field(default=1000, ge=1, le=4096)
    schema_json: str = Field(..., max_length=10000, description="JSON Schema for the expected response shape")
    failure_schema: str | None = Field(default=None, max_length=10000, description="Fallback shape when invalid JSON is returned")
    max_retries: int = Field(default=1, ge=0, le=3)


class StructuredInsightResponse(BaseModel):
    text: str


def _build_system_with_output_contract(system: str, schema_json: str, failure_schema: str | None) -> str:
    contract = (
        "You MUST respond with ONLY a valid JSON object that matches this exact JSON Schema:\n"
        f"{schema_json}\n"
    )
    if failure_schema:
        contract += (
            "If you cannot produce a valid JSON object matching the schema, respond with ONLY this fallback JSON:\n"
            f"{failure_schema}\n"
        )
    contract += "Do not include markdown fences, preamble, or commentary outside the JSON object."
    return f"{system}\n\n{contract}"


def _extract_json(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
    first = cleaned.find("{")
    last = cleaned.rfind("}")
    if first >= 0 and last > first:
        cleaned = cleaned[first : last + 1]
    return cleaned


def _validate_against_schema(payload: str, schema_json: str) -> str | None:
    try:
        import json
        obj = json.loads(payload)
        # Lightweight structural validation: require top-level keys present in schema fields when obvious.
        try:
            schema = json.loads(schema_json)
            required = schema.get("required") if isinstance(schema, dict) else None
            if required:
                missing = [k for k in required if k not in obj or obj[k] is None]
                if missing:
                    return f"missing required fields: {missing}"
        except Exception:
            pass
        return None
    except Exception as e:
        return f"invalid json: {e}"


@app.post("/api/groq", response_model=ClaudeResponse)
@app.post("/api/llm", response_model=ClaudeResponse)
@app.post("/api/claude", response_model=ClaudeResponse)
@limiter.limit(RATE_LIMIT_PER_MINUTE)
def call_llm(req: ClaudeRequest, request: Request, auth=Security(verify_auth)):
    if LLM_PROVIDER == "anthropic":
        text = _call_anthropic(req.system, req.prompt, req.max_tokens)
        model_used = CLAUDE_MODEL
    else:
        text = _call_groq(req.system, req.prompt, req.max_tokens)
        model_used = GROQ_MODEL

    audit_logger.record({
        "time": datetime.now(timezone.utc).isoformat(),
        "provider": LLM_PROVIDER,
        "model": model_used,
        "prompt_chars": len(req.prompt),
        "system_chars": len(req.system),
        "response_chars": len(text),
    })

    return ClaudeResponse(text=text)


@app.post("/api/groq/structured", response_model=StructuredInsightResponse)
@app.post("/api/llm/structured", response_model=StructuredInsightResponse)
@app.post("/api/claude/structured", response_model=StructuredInsightResponse)
@limiter.limit(RATE_LIMIT_PER_MINUTE)
def call_llm_structured(req: StructuredInsightRequest, request: Request, auth=Security(verify_auth)):
    system_prompt = _build_system_with_output_contract(req.system, req.schema_json, req.failure_schema)
    last_err = None
    for attempt in range(1 + max(req.max_retries, 0)):
        try:
            if LLM_PROVIDER == "anthropic":
                text = _call_anthropic(system_prompt, req.prompt, req.max_tokens)
                model_used = CLAUDE_MODEL
            else:
                text = _call_groq(system_prompt, req.prompt, req.max_tokens)
                model_used = GROQ_MODEL

            payload = _extract_json(text)
            validation_err = _validate_against_schema(payload, req.schema_json)
            if validation_err:
                last_err = validation_err
                req = ClaudeRequest(system=system_prompt, prompt=f"{req.prompt}\n\nPrevious response failed because: {last_err}. Return corrected JSON now.", max_tokens=req.max_tokens)
                continue

            audit_logger.record({
                "time": datetime.now(timezone.utc).isoformat(),
                "provider": LLM_PROVIDER,
                "model": model_used,
                "endpoint": "/api/claude/structured",
                "prompt_chars": len(req.prompt),
                "system_chars": len(system_prompt),
                "response_chars": len(payload),
                "attempt": attempt + 1,
            })
            return StructuredInsightResponse(text=payload)
        except HTTPException:
            raise
        except Exception as e:
            last_err = str(e)

    raise HTTPException(status_code=502, detail=f"LLM structured call failed after retries: {last_err}")


# --- PII guardrails ---
_PII_HEADER_HINTS = [
    "email","e-mail","mail","ssn","social","phone","mobile","credit","card","password","address","dob","birth","aadhaar","pan","passport","license"
]

from typing import Any

class PIIMetadata(BaseModel):
    columns: list[str]
    types: dict[str, Any]
    sample_rows: list[dict[str, Any]] = Field(default_factory=list)

@app.post("/api/pii/detect", response_model=PIIReport)
def detect_pii(meta: PIIMetadata):
    dropped: list[str] = []
    retained: list[str] = []
    flags: list[PIIField] = []

    for name in meta.columns:
        low = name.lower().strip()
        hit = next((h for h in _PII_HEADER_HINTS if h in low), None)
        if hit:
            dropped.append(name)
            flags.append(PIIField(name=name, reason=f"Header hints at PII: '{hit}'", confidence="high"))
        else:
            retained.append(name)

    if not dropped:
        flags.append(PIIField(name="(none)", reason="No columns matched PII header heuristics.", confidence="low"))

    return PIIReport(dropped_columns=dropped, retained_columns=retained, flags=flags)


# AWS Lambda Serverless Handler (via Mangum)
try:
    from mangum import Mangum
    handler = Mangum(app)
except Exception as e:
    log.warning("Mangum handler not initialized: %s", e)



