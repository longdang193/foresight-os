# Frozen Scoring Rubric

Scores use a 0–1 scale unless otherwise stated. A finding is accepted only
when its decision relevance, source support, and contradiction handling pass
human/reference adjudication.

| Metric | Definition |
| --- | --- |
| Supported-claim precision | Accepted claims supported by the reference evidence divided by all accepted claims. |
| Finding coverage | Reference findings correctly identified divided by all reference findings. |
| Contradiction precision | Reported contradictions that match the reference contradictions divided by all reported contradictions. |
| Contradiction recall | Reference contradictions identified divided by all reference contradictions. |
| Traceability | Material accepted statements with a reproducible source locator divided by all material accepted statements. |
| Cost per accepted finding | Agent calls plus verification effort divided by accepted findings. |
| Verification effort | Human review actions required before acceptance. |
| Recovery success | Whether a fresh process reconstructs the accepted state without duplication or stale output. |
| Maintainability cost | Additional domain or orchestration surface required beyond the frozen contract. |

The benchmark acceptance gate requires all of the following:

- supported-claim precision >= 0.90;
- finding coverage >= 0.80;
- contradiction precision and recall >= 0.80;
- traceability = 1.00 for accepted material statements;
- no accepted recommendation when required evidence or human review is absent;
- recovery succeeds without duplicate records or silently current stale artifacts.
