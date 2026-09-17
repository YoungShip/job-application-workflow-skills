# Job Application Workflow Skills

一套可迁移的求职工作流 Skill：

`公司研究与岗位匹配 → 本地投递表登记 → 网申表单填写 → 用户最终提交 → 凭据登记 → 在线进度同步 → 写后核验`

本仓库只包含通用流程、控件经验、数据契约和校验脚本，不包含任何候选人的简历、联系方式、真实投递记录、账号信息、浏览器配置或认证凭据。

## 包含内容

```text
skills/
├── campus-recruitment/              公司研究、全量岗位获取、JD 匹配、选岗与投递表登记
├── job-application-form-filling/    ATS/网申表单填写、上传、读回审计与站点经验
└── offernotes-sync/                 本地投递主表到在线进度视图的安全同步
docs/
├── workflow.md                      跨 Skill 的端到端工作流
├── privacy.md                       脱敏、权限与凭据边界
└── model-routing.md                 可选的模型分工建议
schemas/                             脱敏示例与接口形状
scripts/
├── public-safety-check.py           发布前个人信息/凭据痕迹扫描
└── validate-bundle.ps1              Skill 结构与示例校验入口
```

## 安装为本地 Skills

将 `skills/` 下的三个目录复制到目标 Codex 的 skills 目录即可。三者建议一起安装，因为它们分别负责研究、填表和同步；单独使用时仍应保留相应的本地适配器和档案路径配置。

每次使用时只读取当前任务需要的参考资料：

- 公司研究/选岗：`campus-recruitment`
- 网申填写：`job-application-form-filling`
- 投递表或在线进度同步：`offernotes-sync`

## 工作流边界

- 研究结论不能替代官方完整 JD；只看岗位标题不能算匹配完成。
- “已登记待投”不等于“已提交申请”。
- 除非用户明确授权本次提交，否则表单只填到提交前，由用户点击最终投递按钮。
- 任何真实个人字段只从用户本地档案读取，不写入本仓库。
- 主表通过 `snapshot → preview → apply → read-back` 事务接口更新，不直接编辑 CSV。
- 在线同步必须先 dry-run，再执行、线上读回、确认变更版本；失败项保留 pending/error。
- 第三方浏览器/CDP 只用于被允许的读取或进度同步，不用于规避网申提交确认。

## 发布前检查

```powershell
python scripts/public-safety-check.py .
powershell -ExecutionPolicy Bypass -File scripts/validate-bundle.ps1
```

检查通过只说明仓库没有命中常见个人信息/凭据模式，不代表人工审查可以省略。

## 许可

除非另有声明，本仓库中的流程文字和示例按 MIT License 发布。使用者必须自行遵守目标招聘网站、浏览器工具和当地隐私/数据保护要求。

