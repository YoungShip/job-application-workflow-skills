# Verification plan

## What runs offline

- Skill frontmatter and local reference links;
- public-data/credential pattern scan;
- `matching.json` completeness, evidence and raw-catalog accounting;
- cross-skill handoff contract: matching → tracker plan → sensitive-field audit → sync payload → revision ack;
- negative cases for duplicate IDs, raw sensitive values, invalid statuses and stale acknowledgements.

当前本地回归共 30 个用例，另有 PowerShell 7 入口会串行执行安全扫描、结构检查和同一组 Python 测试。

匹配校验回归还覆盖：同集合重复目录 ID、CSV 编码/格式错误不崩溃、非字符串证据引用不被强制转换、范围内岗位结构必填字段、布尔/coverage 类型不被强制转换，以及损坏 JSON 仍输出完整检查维度。

## What is intentionally not run in CI

- Real recruitment websites or accounts;
- CAPTCHA, SMS, browser login or file uploads;
- actual application submission;
- real tracker CSVs or online progress records;
- any operation that could change a candidate’s application state.

Those steps require a user-authorized runtime, current site knowledge and a live read-back audit. The public repository provides the contracts and safety gates; it does not contain credentials or a live connector.
