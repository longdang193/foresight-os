from .models import Evidence, EvidenceCandidate, SourceLocator
from .validation import ValidationError, validate_evidence_candidate


def normalize_evidence_candidate(candidate: EvidenceCandidate | dict) -> Evidence:
    value = validate_evidence_candidate(candidate)
    if value.acquisition_kind in {"web_search", "page_retrieval", "web_crawl"}:
        proof = value.retrieval_proof
        if proof is None or not getattr(proof, "is_valid", lambda: False)():
            raise ValidationError("external evidence candidates require adapter-issued retrieval proof")
    provenance = value.provenance
    return Evidence(
        id=value.candidate_id,
        source_locator=SourceLocator(
            provenance.get("file_version", provenance.get("source_version", "unknown")),
            provenance.get("sheet", value.source),
            provenance.get("range", "unknown"),
            provenance.get("units", "unknown"),
            provenance.get("transformation", "none"),
            provenance.get("calculation", value.query or "none"),
        ),
        version=provenance.get("version", provenance.get("source_version", "unknown")),
        date=provenance.get("date", value.retrieved_at or "unknown"),
        excerpt=value.excerpt,
        limitations=list(value.limitations),
    )
