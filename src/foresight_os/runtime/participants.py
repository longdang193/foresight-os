from dataclasses import dataclass, field
from typing import Any, Mapping

from foresight_os.runtime.capabilities import CapabilityUnavailableError, ForesightFunctionMiddleware, instrument_tool


@dataclass(frozen=True)
class ParticipantConfig:
    id: str
    role: str
    purpose: str
    profile: str = "normal"
    capability_ids: tuple[str, ...] = ()
    skill_ids: tuple[str, ...] = ()
    handoff_targets: tuple[str, ...] = ()
    data_scope: tuple[str, ...] = ()
    provider: str = "local"
    model: str = "unspecified"
    reasoning_controls: dict[str, str | int | float | bool] = field(default_factory=dict)
    limits: dict[str, int | str] = field(default_factory=dict)
    structured_output: bool | dict[str, Any] = False

    @classmethod
    def from_mapping(cls, value: "ParticipantConfig | Mapping[str, Any]", default_id: str = "participant") -> "ParticipantConfig":
        if isinstance(value, cls):
            return value
        return cls(
            id=str(value.get("id", default_id)),
            role=str(value.get("role", value.get("purpose", "participant"))),
            purpose=str(value.get("purpose", "participate")),
            profile=str(value.get("profile", "normal")),
            capability_ids=tuple(str(item) for item in value.get("capability_ids", value.get("capabilities", ()))),
            skill_ids=tuple(str(item) for item in value.get("skill_ids", ())),
            handoff_targets=tuple(str(item) for item in value.get("handoff_targets", ())),
            data_scope=tuple(str(item) for item in value.get("data_scope", ())),
            provider=str(value.get("provider", "local")),
            model=str(value.get("model", "unspecified")),
            reasoning_controls=dict(value.get("reasoning_controls", {})),
            limits=dict(value.get("limits", {})),
            structured_output=value.get("structured_output", False),
        )


@dataclass
class AgentFactory:
    client: Any

    def create(self, participant_config: ParticipantConfig | Mapping[str, Any], run_context: Mapping[str, Any] | None = None) -> Any:
        config = ParticipantConfig.from_mapping(participant_config)
        if config.provider not in {"", "local"}:
            raise RuntimeError(f"participant {config.id} provider '{config.provider}' is not configured")
        context = dict(run_context or {})
        skill_registry = context.get("skill_registry")
        selected_by_participant = context.get("selected_skills_by_participant", {})
        if config.id in selected_by_participant:
            selected_skills = tuple(selected_by_participant[config.id])
        else:
            selected_skills = tuple(context.get("selected_skills", ()))
        if config.skill_ids and skill_registry is None:
            raise RuntimeError(f"participant {config.id} requires a skill registry")
        if skill_registry is not None and config.skill_ids and not selected_skills:
            selected_skills = skill_registry.resolve(config.skill_ids)
        required_skill_capabilities = skill_registry.required_capabilities(selected_skills) if skill_registry is not None else ()
        required_capabilities = tuple(dict.fromkeys((*config.capability_ids, *required_skill_capabilities)))
        kwargs: dict[str, Any] = {
            "id": config.id,
            "name": config.id,
            "instructions": f"Act as the {config.role} responsible for {config.purpose} and return a structured result."
            + (f"\n\n{skill_registry.instructions(selected_skills)}" if selected_skills and skill_registry is not None else ""),
        }
        if context.get("handoff"):
            kwargs["require_per_service_call_history_persistence"] = True
        profile_options = context.get("profile_options", {})
        if config.profile in profile_options:
            kwargs["default_options"] = dict(profile_options[config.profile])
        if config.model != "unspecified":
            kwargs.setdefault("default_options", {})["model"] = config.model
        if config.reasoning_controls:
            kwargs.setdefault("default_options", {}).update(config.reasoning_controls)
        if config.structured_output and isinstance(config.structured_output, dict):
            kwargs.setdefault("default_options", {})["response_format"] = config.structured_output
        tools = context.get("tools_by_participant", {}).get(config.id)
        middleware = []
        if tools is None and required_capabilities and context.get("capability_resolver") is not None:
            participant_context = dict(context)
            participant_context["participant_data_scope"] = config.data_scope
            resolutions = context["capability_resolver"].resolve(required_capabilities, participant_context)
            denied = [item.reason for item in resolutions.values() if not item.available]
            if denied:
                raise CapabilityUnavailableError(f"participant {config.id} capabilities unavailable: {'; '.join(denied)}")
            resolved_tools = []
            native_mcp_definitions = {}
            for item in resolutions.values():
                if item.tool is None:
                    continue
                if item.tool.__class__.__module__.startswith("agent_framework") and hasattr(item.tool, "functions"):
                    resolved_tools.append(item.tool)
                    for function in getattr(item.tool, "functions", ()):
                        native_mcp_definitions[getattr(function, "name", "")] = item.definition
                else:
                    resolved_tools.append(instrument_tool(item.tool, item.definition, participant_context))
            tools = resolved_tools
            if native_mcp_definitions:
                middleware.append(ForesightFunctionMiddleware(native_mcp_definitions, participant_context))
        elif tools is None and required_capabilities:
            raise CapabilityUnavailableError(f"participant {config.id} capabilities require a configured resolver")
        elif tools:
            native_mcp_definitions = {}
            for item in tools:
                for function in getattr(item, "functions", ()):
                    native_mcp_definitions[getattr(function, "name", "")] = context.get("capability_definitions", {}).get(getattr(item, "capability_id", ""))
            native_mcp_definitions = {name: definition for name, definition in native_mcp_definitions.items() if definition is not None}
            if native_mcp_definitions:
                middleware.append(ForesightFunctionMiddleware(native_mcp_definitions, context))
        if tools is not None:
            kwargs["tools"] = tools
        if middleware:
            kwargs["middleware"] = middleware
        context_providers = context.get("context_providers_by_participant", {}).get(config.id)
        if context_providers is not None:
            kwargs["context_providers"] = context_providers
        agent = self.client.as_agent(**kwargs)
        scope = context.get("scope")
        if scope is not None:
            scope.register_agent(agent)
        cleanup = context.get("cleanup")
        if cleanup is not None and scope is None:
            cleanup.append(agent)
        return agent
