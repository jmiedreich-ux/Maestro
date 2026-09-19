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
    AgentRouteRegistry,
    PermittedDestination,
    RoleSelections,
    RouteRequirements,
    ToolModelSelection,
    ToolRoute,
)

__all__ = [
    "AdapterInspector",
    "AdapterObservation",
    "AgentRouteError",
    "AgentRoutePreflight",
    "AgentRouteRegistry",
    "InstalledAdapter",
    "PermittedDestination",
    "ResolvedAgentRoute",
    "ResolvedRoleRoutes",
    "RoleSelections",
    "RouteRequirements",
    "RunningToolIdentity",
    "ToolModelSelection",
    "ToolRoute",
    "verify_running_identity",
]
