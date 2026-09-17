---
name: campus-recruitment
description: 研究校招公司、获取官方岗位目录、逐岗匹配 JD、比较志愿并按事务协议登记投递主表。用户提到秋招、校招、公司调研、岗位比较、选岗、志愿或投递表时使用。
metadata:
  short-description: 公司研究、岗位匹配与投递主表登记
---

# Campus recruitment workflow

负责“研究与选择”和“本地投递记录维护”，不负责代填网申页面；表单填写由 `job-application-form-filling` 负责，在线进度视图同步由 `offernotes-sync` 负责。

## Hard boundaries

1. 个人事实只从当前候选人本地档案读取；不要凭记忆补全姓名、教育、经历、联系方式或偏好。
2. 推荐必须基于官方完整 JD。第三方页面只用于定位官方入口，不能作为职责、门槛、额度或日期的唯一依据。
3. “已选定/已登记待投”不等于“已提交”。只有真实提交证据才能写 `Submitted`。
4. 不能因为岗位标题、关键词命中或源码存在就推断能力覆盖；未证实能力必须在对应 `requirements[].judgment` 中保留为缺口/待确认。
5. 有限志愿、投后不可修改、截止日、面试形式和跨项目额度必须显著说明；规则冲突保持待核实。
6. 主表只能通过适配器的 `snapshot → preview → apply → read-back` 流程更新，禁止直接编辑 CSV 或按行号定位。
7. 新研究岗位须经用户选定，并且 `matching.json` 验证通过后，才登记为待投。

## Choose an entry point

- **A：新公司全量研究**：没有可靠现行报告，或用户要求当前全量筛选。
- **B：已有公司增量复核**：只核对开放状态、额度、截止日、志愿或新增岗位；改变推荐时补读受影响 JD。
- **C：已选岗位补档**：补齐历史 JD、来源或材料，不重新推荐、不改变已投事实。
- **D：进度维护**：依据邮件、账号页或用户凭据更新提交/测评/面试/结果；不顺带重做调研。

开始前读取最新候选人规则、现有研究索引和投递主表快照。只读查询不产生写入；任何写入都要记录证据并检查同步队列。

## A. Full research

1. **查重与范围**：核对公司主体、招聘批次、城市、届别、校招/社招/实习、历史投递和公司级额度。
2. **定位官方入口**：对多品牌集团或多个招聘主体分别核实入口、额度和流转关系，不能套用另一个主体的规则。
3. **获取全量目录**：按 `references/data-acquisition.md` 选择 API、页面或浏览器路径，保存原始快照，翻到最后一页并记录总数。
4. **强制核查门**：逐岗判断届别、招聘性质、城市、硬门槛、额度、投后修改/撤回、截止日和面试形式。未知就标未知，不猜。
5. **逐岗读 JD**：对所有范围内岗位完整阅读职责和要求；在共享 `jd_source` 中保存岗位 ID、来源 URL、读取时间、本地正文快照和可定位原文引文。
6. **映射候选人证据**：每条要求写入 `requirements[]`，明确 `hard_qualification`/`core_capability`/`plus`/`ambiguous` 类别、JD 引文 ID、候选人档案版本与证据 ID、`direct_support`/`transferable`/`no_evidence`/`conflict` 支持关系，以及 `satisfied`/`not_satisfied`/`pending` 结论。无证据不能写成满足；语义不明确不能升级为硬门槛。
7. **由逐项结果汇总**：计算 `requirement_summary`，再生成 `decision`；不要先写 S/A/B/C 或自由百分比再补理由。S/A/B/C 仅是可选辅助标签，规则见 `references/matching-record.md`。
8. **验证再报告**：按 schema v2 边读边写 `matching.json`，运行 `scripts/verify-matching.py`。它会分别报告结构、目录身份、证据引用、决策一致性、覆盖声明和下一步状态；非零报告仍可包含已核实单岗，不能直接宣称全量完成。
9. **输出可决策结论**：优先展示核心要求总数、直接支持、可迁移、待确认和明确不满足数量；给出首选、替代、排除清单、影响选择的规则、未核事实和需要用户确认的岗位。

关键词搜索可以定位岗位，但不能证明全量覆盖；如果不得不使用关键词，`coverage.capture_status` 使用 `partial` 或 `unknown`，明确写“非全量，可能遗漏”。原始目录 ID 提取必须在 `raw_catalog` 中显式声明，无法提取时保持覆盖待核验，不得按标题猜身份。

## B/C/D shortcuts

- B 只验证本次变化；推荐顺序变化时，重新读取受影响岗位的完整 JD，并保留原报告和快照。
- C 以稳定 `job_id`、官方编号、批次和部门确认身份；缺失的 JD 留缺口，不用相邻岗位或新版 JD 填充。
- D 只处理当前事实所需材料；邀请不等于完成，某轮通过不等于 Offer，拒绝/放弃要确认实际到达环节。

## Register the local tracker

读取 `references/tracker-contract.md`。只有 `matching` 报告的 `readiness.can_register_selected_position=true` 且用户已选定岗位时，才进入主表登记。典型流程：

```text
snapshot → build plan with expected_revision → preview → apply → snapshot/read-back → validate
```

新岗位用稳定新 `job_id` 登记 `Pending` 或等价待投状态，保留未修改字段。由未投转 `Submitted` 时，同一计划必须追加含真实证据的申请日志和实际日期。不得把计划日期、页面打开或预览结果写成提交事实。旧 schema 记录可读取展示，但没有完成迁移和新校验前不得当作新标准通过。

本地写入成功后检查 `sync_queue`，交由 `offernotes-sync` 完成在线视图同步。在线同步失败时保留 `pending/error`，不能把本地保存说成线上完成。

## References

- 全量目录获取与失败切换：[data-acquisition.md](references/data-acquisition.md)
- 匹配记录契约：[matching-record.md](references/matching-record.md)
- 边界案例：[edge-cases.md](references/edge-cases.md)
- 主表适配器接口：[tracker-contract.md](references/tracker-contract.md)
- 主表最小入口：[tracker-update.md](references/tracker-update.md)
- 结构化校验：`scripts/verify-matching.py`
