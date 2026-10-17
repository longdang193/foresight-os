from dataclasses import dataclass, field
from typing import Any, Mapping

from foresight_os.domain.relationships import RELATIONSHIP_RULES
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
        instructions = f"Act as the {config.role} responsible for {config.purpose} and return a structured result."
        if "spreadsheet_read" in required_capabilities:
            instructions += (
                " For spreadsheet_read, pass source as a string and use the selected sheet or range "
                "to bound the read. Omit limits unless a concrete measured safety bound is required; "
                "do not invent low max_rows or max_cells values that could truncate the selected sheet. "
                "Keep source set to the approved workbook path; never use workbook_sha256, a hash, or "
                "a provenance digest as the source path."
            )
        if "data_analysis" in required_capabilities:
            instructions += (
                " For data_analysis, operation kind must be one of aggregate, sum, mean, scenario, "
                "sensitivity, compare, join, nulls, missing, or duplicates; summary is unsupported. "
                "Use value_column for aggregate, sum, mean, scenario, and sensitivity; use columns "
                "for compare, and pass exactly two column names in that list; use key_columns for duplicates."
            )
        if "document_read" in required_capabilities:
            instructions += (
                " For document_read, pass a relative path from an approved local source root and an "
                "optional max_chars bound; do not request arbitrary filesystem paths."
            )
        if "artifact_generation" in required_capabilities:
            instructions += (
                " For artifact_generation, pass a relative artifact name, complete content, and one "
                "of text, markdown, or json; generated files are provisional local outputs and do not "
                "constitute external delivery."
            )
        if "domain_validation" in required_capabilities:
            instructions += (
                " For domain_validation, pass either a complete analysis payload or an evidence candidate "
                "with only candidate_id, capability_id, source, request, excerpt, provenance, limitations, "
                "acquisition_kind, retrieved_at, query, context, raw_result, and retrieval_proof; do not "
                "pass scorecard weights, claims, recommendations, stage results, stage_id, objective, "
                "decision_question, horizon, research_needs, relevant_constraints, dependency_outputs, "
                "or other stage metadata as candidate fields. Canonical stage-result validation is automatic; "
                "never call domain_validation with an analysis-stage-result payload."
            )
        if "calculation" in required_capabilities:
            instructions += (
                " For calculation, use only spreadsheet measurements returned by spreadsheet_read or "
                "verified calculation records; never pass domain Evidence, prose excerpts, coordinates, "
                "or fabricated measurement mappings as calculation inputs."
            )
        if context.get("require_structured_output") and context.get("stage_id"):
            instructions += (
                f" The output field stage_id must be exactly {context['stage_id']!r}; "
                "do not invent or substitute a generic stage identifier. Return only one JSON "
                "object matching analysis-stage-result/v1 after tool use; do not return prose, "
                "markdown fences, or commentary."
            )
            relationship_guidance = "; ".join(
                f"{relation}: {'/'.join(sorted(kind.value for kind in rule.sources))} -> "
                f"{'/'.join(sorted(kind.value for kind in rule.targets))}"
                for relation, rule in sorted(RELATIONSHIP_RULES.items())
            )
            instructions += (
                " Relationship edges must follow the canonical endpoint rules: "
                f"{relationship_guidance}. Only emit an edge when both endpoint kinds match; "
                "never emit same-kind claim-to-claim or implication-to-implication edges; "
                "if uncertain, omit the edge rather than inventing a relationship, and remove its "
                "ID from relationship_ids. "
                "Use informs for claim/evidence/implication -> implication/recommendation; "
                "use produces only from claim/implication/recommendation to artifact."
            )
            instructions += (
                " The stage result must preserve canonical dependency references: an existing "
                "dependency ID may be referenced without copying its record when the dependency "
                "is authorized and current. Validate the dependency hash, invalidation state, "
                "closure, and participant authorization before using it; materialize a record only "
                "when the current contract requires it, and copy every field verbatim when you do. "
                "Every relationship_ids entry must refer to a declared current relationship or an "
                "authorized existing canonical relationship. Before returning, audit every "
                "evidence_ids, relationship_ids, input_ids, from_id, and to_id value against a "
                "declared or authorized canonical ID; remove any reference that cannot be proven."
            )
            instructions += (
                " When re-declaring an existing dependency record, copy every field verbatim; do not "
                "rewrite evidence, claims, implications, recommendations, or relationships under an "
                "existing ID. use a new record ID for a revised interpretation."
            )
            instructions += (
                " Every calculations[].input_ids value must match an id declared in the current "
                "evidence or calculations collection; never use a spreadsheet coordinate, source "
                "locator, or tool-result label as an input id. Do not emit duplicate relationship "
                "edges with the same endpoints and relation type."
            )
            if "spreadsheet_read" in required_capabilities:
                instructions += (
                    " For spreadsheet_read selection, encode ranges as a list of "
                    "[sheet_name, cell_range] pairs, for example [[\"Channel Dynamic\", \"A1:H20\"]]. "
                    "When ranges or tables are used, also provide sheet_names for every selected "
                    "sheet and keep each range within the sheet's used area; do not request a "
                    "blanket workbook read or padded rows and columns. Request the smallest bounded "
                    "set of sheets and ranges needed for one analytical step; combine compatible ranges "
                    "in one call when this keeps the selection bounded and avoids repeated extraction."
                )
        kwargs: dict[str, Any] = {
            "id": config.id,
            "name": config.id,
            "instructions": instructions
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
        elif context.get("require_structured_output") and context.get("structured_output_schema"):
            kwargs.setdefault("default_options", {})["response_format"] = context["structured_output_schema"]
        tools = context.get("tools_by_participant", {}).get(config.id)
        middleware = []
        provider_middleware = context.get("provider_call_middleware")
        if provider_middleware is not None:
            middleware.append(provider_middleware)
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
