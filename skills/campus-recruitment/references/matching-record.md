# Matching record contract

`matching.json` 是“全量目录 → 范围筛选 → 完整 JD 阅读 → 经历匹配”的对账文件。比较报告只能从它生成或与它逐项对照。

## Required invariants

1. `catalog_index` 一岗一条，包含官方范围内的完整目录；
2. `in_scope=false` 必须有 `exclusion`；
3. `positions` 覆盖每一个 `in_scope=true` 的岗位；
4. 每个 `positions` 条目至少有两条不同、非空的 JD 原文引文；
5. 未排除岗位还要有 `grade`、`coverage_estimate`、`resume_version`、`match_reasons`、`gaps`；
6. `positions[].id` 必须存在于 `catalog_index`；
7. `raw_catalog.file` 必须存在，`total_positions` 必须等于目录条数；
8. `catalog_index` 不允许重复 ID，`positions` 不允许重复 ID。

## Shape

```json
{
  "company": "Example Company",
  "date": "YYYY-MM-DD",
  "scope": "Target cohort and geography",
  "raw_catalog": {
    "file": "catalog.json",
    "total_positions": 1
  },
  "catalog_index": [
    {
      "id": "example-role-1",
      "title": "Example QA Engineer",
      "city": "Example City",
      "in_scope": true
    }
  ],
  "positions": [
    {
      "id": "example-role-1",
      "title": "Example QA Engineer",
      "city": "Example City",
      "url": "https://example.invalid/jobs/example-role-1",
      "jd_evidence": [
        "Design and maintain automated tests.",
        "Investigate failures and report root causes."
      ],
      "grade": "A",
      "coverage_estimate": "60% (fixture only)",
      "resume_version": "candidate-selected-version",
      "match_reasons": "Fixture match reason; replace with evidence-backed reasoning.",
      "gaps": "Fixture gap; replace with verified gaps.",
      "excluded": false
    }
  ]
}
```

The example is fictional and is not a recommendation for a real candidate.

## Interpretation rules

- `grade` is a prioritization level, not a hiring probability.
- `coverage_estimate` describes evidence coverage of the JD, not skill mastery beyond the evidence.
- A tool, library or project appearing in source code is not by itself proof of personal ownership or production experience.
- “Future training may cover this” belongs in a separate note and does not satisfy a current hard requirement.

## Validation

```powershell
python skills/campus-recruitment/scripts/verify-matching.py path/to/matching.json
```

The verifier writes a sibling `*-verification.json` report. It checks structure and file/count consistency; human review is still required for source authenticity and decision quality.
