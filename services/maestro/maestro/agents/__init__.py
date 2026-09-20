"""Public contracts for installed agent routing and preflight."""

from .preflight import (
    AdapterInspector,
    AdapterObservation,
    AgentRoutePreflight,
    InstalledAdapter,
    ResolvedAgentRoute,
    ResolvedRoleRoutes,
    RunningToolIdentity,
    verify_running_identity,
)
from .routes import (
    AgentRouteError,
    ConfiguredAgentRouteProvider,
    AgentRouteRegistry,
    PermittedDestination,
    RoleSelections,
    RouteRequirements,
    ToolModelSelection,
    ToolRoute,
)
from .runtime_identity import (
    ConfirmedRuntimeIdentity,
    PlanningIdentityConsumer,
    RuntimeIdentityProtocolError,
    SupervisorIdentityReporter,
    compose_runtime_identity_endpoints,
)

__all__ = [
    "AdapterInspector",
    "AdapterObservation",
    "AgentRouteError",
    "ConfiguredAgentRouteProvider",
    "ConfirmedRuntimeIdentity",
    "AgentRoutePreflight",
    "AgentRouteRegistry",
    "InstalledAdapter",
    "PermittedDestination",
    "PlanningIdentityConsumer",
    "ResolvedAgentRoute",
    "ResolvedRoleRoutes",
    "RoleSelections",
    "RouteRequirements",
    "RunningToolIdentity",
    "RuntimeIdentityProtocolError",
    "SupervisorIdentityReporter",
    "ToolModelSelection",
    "ToolRoute",
    "compose_runtime_identity_endpoints",
    "verify_running_identity",
]
