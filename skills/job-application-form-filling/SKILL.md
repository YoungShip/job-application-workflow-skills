---
name: job-application-form-filling
description: 代填校招或社招网申表单，处理 ATS 控件、简历上传、解析纠错、字段读回审计和页面交接。用户明确要求填写、准备申请或排查已填写表单时使用。
metadata:
  short-description: ATS 网申填写与逐字段核验
---

# Job application form filling

负责“已经选定岗位后的表单准备与填写”。公司研究、岗位匹配和投递表登记由 `campus-recruitment` 负责；提交后的本地/在线进度同步由 `offernotes-sync` 负责。

## Hard boundaries

1. 除非用户明确授权本次申请直接提交，否则只填到提交前，由用户点击最终投递按钮。
2. 登录、短信验证码、滑块、CAPTCHA 和需要用户确认的敏感资料传输由用户完成或按当前工具的确认规则处理。
3. 所有个人字段只从当前本地档案读取，不凭记忆、不沿用其他候选人的资料。
4. 不把未完成的项目、AI 辅助代码、未来训练计划或 JD 要求写成既有能力。
5. 操作成功不等于字段成功；文本、下拉、日期、勾选、附件都必须读回核对。
6. 不点击“投递/提交/确认投递”等最终外部副作用按钮，除非本次已明确授权。
7. 不使用带 remote-debugging 的专用浏览器执行网申提交；该通道如被允许，只用于在线进度同步或只读诊断。

## Workflow

### 1. Prepare

读取具体岗位的完整 JD、候选人档案和已选简历版本。按 `references/application-materials.md` 选择相关且有证据的经历，建立本次私有材料快照。不得把私人材料快照写入公共 Skill 仓库。

### 2. Identify the ATS family

先读 `references/ats-families.md`，再读当前站点的 `references/site-knowledge.md`。已有站点经验只作为操作提示，仍需按当前页面读回；未知站点按 `references/fill-protocol.md` 探索并把已验证差异增量记录下来。

### 3. Open and upload

打开官方岗位投递页。若需要登录，停在登录步骤交给用户。上传指定简历，只有在确实需要解析且内容可恢复时才确认“解析并覆盖”。等待解析实际完成后再读回，不用固定等待时间冒充完成。

### 4. Fill

按档案补齐解析遗漏字段。处理自定义控件时先识别组件体系、字段标签和重复区块；多个同名输入不能凭索引猜测。完整履历要求不得因为“突出重点经历”而省略必填经历。

### 5. Audit

按已确认的业务字段清单逐项读回：

- 基本信息、城市、毕业时间；
- 教育起止、专业、学历和学习形式；
- 实习与项目名称、角色、起止日期、描述和链接；
- 语言、奖项、岗位专属问题；
- native select/custom combobox 的真实选中标签；
- checkbox/radio 实际状态；
- 上传简历文件名；
- 所有 textarea 的内容和解析残留。

身份证、手机号、邮箱等敏感字段只在页面内与档案比较，返回 `matches: true/false`，不在日志或回复中全文打印。隐藏字段、密码字段和认证对象不纳入普通审计。

### 6. Handoff or submit

未获提交授权时，保留页面并交付 URL、岗位、简历版本、关键字段核对结果和未完成项。获本次提交授权时，也必须先完成审计；提交后只有成功页、账号记录、确认邮件或用户明确确认才可登记为已提交。

### 7. Learn

将确定有效的站点控件、上传入口、日期行为、复用规律和可复现坑位增量写入 `references/site-knowledge.md`。失败只有在原因可复用时才记录；一次性坐标尝试不固化为通用规则。

## References

- ATS 家族经验：[ats-families.md](references/ats-families.md)
- 通用控件与审计：[fill-protocol.md](references/fill-protocol.md)
- 材料选择与留存：[application-materials.md](references/application-materials.md)
- 已验证站点差异：[site-knowledge.md](references/site-knowledge.md)

