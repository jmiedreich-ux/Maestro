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
    RuntimeIdentityCore,
    RuntimeIdentityProtocolError,
    RuntimeIdentityServer,
    SupervisorIdentityReporter,
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
    "RuntimeIdentityCore",
    "RuntimeIdentityProtocolError",
    "RuntimeIdentityServer",
    "SupervisorIdentityReporter",
    "ToolModelSelection",
    "ToolRoute",
    "verify_running_identity",
]
