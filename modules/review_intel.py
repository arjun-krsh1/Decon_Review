"""
modules/review_intel.py — MODULE: Review Intelligence (Product Team)

Deep-dive descriptive analysis of one product's Amazon reviews — a long-form
narrative report (voice of customer, themes, quotes, friction points, verdict),
not a ranked comparison. Sits right below Product Intelligence.
"""

from modules.base import Module

MODULE = Module(
    key="review_intel",
    label="Review Intelligence",
    department="Product Team",
    tagline="Deep, descriptive read of one product's Amazon reviews — voice of customer, "
            "themes, real quotes, friction points, verdict.",
    input_fields=[],
    weights={},
    candidates=[],
    score=lambda c, i: (0, {}),
    explain_prompt=lambda c, i, p: "",
    generate_prompt=lambda i, n: "",
    mock_ideas=lambda i, n: [],
    radar=[],
    recommend_noun="theme",
    generate_noun="insight",
)
