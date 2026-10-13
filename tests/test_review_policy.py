from foresight_os.controller.policy import ReviewPolicyResolver
from foresight_os.domain.models import ResearchNeed, ResearchNeedKind, WorkBrief


def brief(*, consequence_level="standard", needs=()):
    return WorkBrief("policy", "question", [], ["answer"], [], [], "direction", "next", stages=[] , consequence_level=consequence_level)


def test_review_policy_precedence_and_required_skills():
    resolver = ReviewPolicyResolver()
    assert resolver.resolve(brief()).required_skill_ids == ("source-appraisal", "red-team-claim")
    assert resolver.resolve(target_kind=ResearchNeedKind.QUANTITATIVE_ANALYSIS.value).required_skill_ids == ("quantitative-sanity-check", "red-team-claim")
    assert resolver.resolve(brief(consequence_level="high"), target_kind=ResearchNeedKind.QUANTITATIVE_ANALYSIS.value).required_skill_ids == ("key-assumptions-check", "red-team-claim", "abstain-or-escalate")


def test_missing_or_unknown_classification_falls_back_and_records_issue():
    resolver = ReviewPolicyResolver()
    missing = resolver.resolve()
    unknown = resolver.resolve(target_kind="not-a-target")
    assert missing.policy_id == "review-policy-standard-v1"
    assert missing.unresolved_classification_issue
    assert unknown.policy_id == "review-policy-standard-v1"
    assert unknown.unresolved_classification_issue
