from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apis.fastapi.agents import AgentAPIRouter
from apis.fastapi.apikeys import APIKeyAPIRouter
from apis.fastapi.audit import AuditAPIRouter
from apis.fastapi.auth import UsersAuthAPIRouter
from apis.fastapi.escalations import EscalationAPIRouter
from apis.fastapi.gateway import ExecutionGatewayAPIRouter
from apis.fastapi.policy import PolicyAPIRouter
from apis.fastapi.reports import ReportsAPIRouter
from apis.fastapi.tenants import TenantAPIRouter
from core.agents.service import AgentService
from core.api_keys.service import APIKeyService
from core.audit_events.service import AuditEventService
from core.escalations.manager import EscalationManager
from core.escalations.service import EscalationService
from core.policy.engine import PolicyEngine
from core.policy.service import PolicyService
from core.reports.service import ComplianceReportService
from core.tenants.service import TenantService
from core.users.auth import AuthService
from core.users.service import UserService
from dbs.postgres.agents.dao import AgentDAO
from dbs.postgres.api_keys.dao import APIKeyDAO
from dbs.postgres.audit_events.dao import AuditEventDAO
from dbs.postgres.engine import cleanup_connections, test_connection
from dbs.postgres.escalations.dao import EscalationDAO
from dbs.postgres.policy.dao import PolicyDAO
from dbs.postgres.tenant_policies.dao import TenantPolicyDAO
from dbs.postgres.tenants.dao import TenantDAO
from dbs.postgres.users.dao import UserDAO


@asynccontextmanager
async def lifespan(app: FastAPI):
    await test_connection()
    yield
    await cleanup_connections()


app = FastAPI(
    title="Provenance API",
    description="API for Provenance, the Agentic Audit & Compliance Layer for AI agent deployments.",
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

# Initialize DAOs
audit_event_dao = AuditEventDAO()
escalation_dao = EscalationDAO()
user_dao = UserDAO()
tenant_dao = TenantDAO()
agent_dao = AgentDAO()
policy_dao = PolicyDAO()
tenant_policy_dao = TenantPolicyDAO()
api_key_dao = APIKeyDAO()

# Initialize services
user_service = UserService(dao=user_dao)
auth_service = AuthService(user_service=user_service)
policy_service = PolicyService(
    dao=policy_dao,
    tenant_policy_dao=tenant_policy_dao,
)
policy_engine = PolicyEngine(service=policy_service)
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
tenant_service = TenantService(tenant_dao=tenant_dao)
agent_service = AgentService(agent_dao=agent_dao)
api_key_service = APIKeyService(api_key_dao=api_key_dao)

# Initialize routers
execution_gateway_router = ExecutionGatewayAPIRouter(
    policy_engine=policy_engine,
    tenant_service=tenant_service,
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
api_key_router = APIKeyAPIRouter(
    apikey_service=api_key_service,
)
policy_router = PolicyAPIRouter(policy_service=policy_service)
reports_router = ReportsAPIRouter(
    report_service=report_service,
)
users_auth_router = UsersAuthAPIRouter(auth_service=auth_service)
tenant_router = TenantAPIRouter(
    tenant_service=tenant_service,
)
agent_router = AgentAPIRouter(
    agent_service=agent_service,
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
    tenant_router.router,
    tags=["Tenants"],
    prefix="/tenants",
)
api_v1_router.include_router(
    agent_router.router,
    tags=["Agents"],
    prefix="/agents",
)
api_v1_router.include_router(
    api_key_router.router,
    tags=["API Keys"],
    prefix="/api_keys",
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
