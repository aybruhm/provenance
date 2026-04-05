from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apis.fastapi.audit import AuditAPIRouter
from apis.fastapi.auth import UsersAuthAPIRouter
from apis.fastapi.escalations import EscalationAPIRouter
from apis.fastapi.gateway import ExecutionGatewayAPIRouter
from apis.fastapi.policy import PolicyAPIRouter
from apis.fastapi.reports import ReportsAPIRouter
from core.audit_events.service import AuditEventService
from core.escalations.manager import EscalationManager
from core.escalations.service import EscalationService
from core.policy.service import PolicyEngine
from core.reports.service import ComplianceReportService
from core.users.auth import AuthService
from core.users.service import UserService
from dbs.postgres.audit_events.dao import AuditEventDAO
from dbs.postgres.engine import cleanup_connections, test_connection
from dbs.postgres.escalations.dao import EscalationDAO
from dbs.postgres.users.dao import UserDAO
from middlewares.jwt_bearer import JWTCookie


@asynccontextmanager
async def lifespan(app: FastAPI):
    await test_connection()
    yield
    await cleanup_connections()


app = FastAPI(
    title="Sentinel API",
    description="API for Sentinel, the Agentic Audit & Compliance Layer for AI agent deployments.",
    version="0.1.0",
    lifespan=lifespan,
    root_path="/api",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# Initialize v1 router
api_v1_router = APIRouter(prefix="/v1")

# Initialize custom middlewares
jwt_cookie = JWTCookie()

# Initialize DAOs
audit_event_dao = AuditEventDAO()
escalation_dao = EscalationDAO()
user_dao = UserDAO()

# Initialize services
user_service = UserService(dao=user_dao)
auth_service = AuthService(user_service=user_service)
policy_engine = PolicyEngine()
audit_service = AuditEventService(
    audit_event_dao=audit_event_dao,
    escalation_dao=escalation_dao,
)
escalation_service = EscalationService(
    escalation_dao=escalation_dao,
)
escalation_manager = EscalationManager(
    service=escalation_service,
)
report_service = ComplianceReportService(
    escalation_service=escalation_service,
    audit_event_service=audit_service,
)

# Initialize routers
execution_gateway_router = ExecutionGatewayAPIRouter(
    policy_engine=policy_engine,
    audit_service=audit_service,
    escalation_manager=escalation_manager,
    escalation_service=escalation_service,
)
audit_router = AuditAPIRouter(
    audit_service=audit_service,
)
escalation_router = EscalationAPIRouter(
    escalation_service=escalation_service,
    escalation_manager=escalation_manager,
)
policy_router = PolicyAPIRouter()
reports_router = ReportsAPIRouter(
    report_service=report_service,
)
users_auth_router = UsersAuthAPIRouter(
    jwt_cookie=jwt_cookie,
    auth_service=auth_service,
)

# Register routers
api_v1_router.include_router(
    execution_gateway_router.router,
    tags=["Execution Gateway"],
    prefix="/gateway",
)
api_v1_router.include_router(
    audit_router.router,
    tags=["Audit"],
    prefix="/audit",
)
api_v1_router.include_router(
    escalation_router.router,
    tags=["Escalations"],
    prefix="/escalations",
)
api_v1_router.include_router(
    policy_router.router,
    tags=["Policy"],
    prefix="/policies",
)
api_v1_router.include_router(
    reports_router.router,
    tags=["Reports"],
    prefix="/reports",
)
api_v1_router.include_router(
    users_auth_router.router,
    tags=["Auth"],
    prefix="/auth",
)

# Mount api_v1_router
app.include_router(api_v1_router)


@app.get("/health")
async def health_check():
    """Health check endpoint to verify that the API is running."""
    return {"status": "ok"}
