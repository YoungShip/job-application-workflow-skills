---
name: job-application-form-filling
description: 代填校招或社招网申表单，处理 ATS 控件、简历上传、解析纠错、字段读回审计和页面交接。用户明确要求填写、准备申请或排查已填写表单时使用。
metadata:
  short-description: ATS 网申填写与逐字段核验
---

# Job application form filling

负责“已经选定岗位后的表单准备与填写”。公司研究、岗位匹配和投递表登记由 `campus-recruitment` 负责；提交后的本地/在线进度同步由 `offernotes-sync` 负责。

## Hard boundaries

1. 除非用户已对本次具体岗位/批次明确授权最终提交，否则默认只填到提交前。预授权必须可定位到岗位或明确的批次/筛选范围，不能从“想自动化”推断。
2. 登录、注册、短信验证码、微信扫码、滑块、CAPTCHA、Cloudflare 和需要用户确认的敏感认证步骤由用户完成或按当前工具确认规则处理。
3. 所有个人字段只从当前本地档案读取，不凭记忆、不沿用其他候选人的资料。
4. 不把未完成的项目、AI 辅助代码、未来训练计划或 JD 要求写成既有能力。
5. 操作成功不等于字段成功；文本、下拉、日期、勾选、附件都必须读回核对。页面显示过也不等于已服务端保存。对于会把字段写入共享 profile/resume、存在自动复用/二次映射，或有可靠同源读取接口的 ATS，保存/提交后还必须做持久化状态读回；不能只凭当前 UI 判定服务器真值。
6. 最终外部副作用遵循 review / preauthorized / autonomous 授权模式；无明确模式时使用 review。提交后必须取得真实提交证据才能登记 Submitted。
7. **Playwright 专用持久化 profile 可用于网申填写；Raw CDP 不作为普通 ATS 填表首选。** Playwright 允许打开申请页、上传、解析纠错、填写、保存和读回；Raw CDP 只保留在线进度同步/只读诊断及用户明确的特殊例外。两者都不得 remote-debug 用户真实默认 Chrome profile。
8. 自动化交互失败时最多采用三层有界策略，不无限重试、不随机坐标点击。验证码、未知高影响问题、额度/志愿冲突和不可逆弹窗立即交给用户。
9. **最终提交还要检查项目级隐藏门**：志愿/顺序、项目总额度、同单位额度、项目确认项等可能不在简历表单中。提交接口即使 HTTP 200，也必须检查业务 code/msg；若返回“志愿不完整/顺序缺失/额度冲突”等业务错误，不得登记 Submitted。先查账号投递记录防止其实已生成记录，再解析当前项目配置、官方弹窗或前端行为定位缺失门，确认后才允许有界重试；重试后再次读回投递记录。若志愿选择会占用稀缺额度、不可修改或影响其他岗位，仍属于人工确认门。

## Browser channel and remote takeover

通道优先级按当前运行时能力选择：①内置浏览器 → ②已授权日常 Chrome 插件 → ③A Playwright 专用持久化 profile → ③B Raw CDP 专用通道。前一级能可靠完成且可读回时不升级。

- **③A Playwright**：适合 ATS UI。优先 data-cy、label、role、可见文本和真实 option；利用 actionability/auto-wait 拒绝被遮挡或不可交互的元素。必要的组件级 JavaScript 只针对已经精确定位的目标，并在操作后读回。
- **③B Raw CDP**：适合 OfferNotes/API 级精确同步和诊断。不得因为能执行 Runtime.evaluate 就把它当成普通网申默认方案。
- **远程登录接管**：遇首次注册、短信/扫码/2FA/CAPTCHA 时暂停在当前专用浏览器页面，用户可在本机或已授权远程桌面完成；之后从当前页续跑。不要要求用户把验证码、密码、Cookie 或 token 发进聊天。
- **失败接管**：同一字段依次尝试语义 locator/真实选项、组件特定方法/键盘、一次可恢复的安全重入；仍失败返回 needs-human。刷新前确认未保存状态是否会丢失。
- **提交模式**：
  - review：默认。全量审计后停在最终提交前，等待用户批准。
  - preauthorized：用户预先明确批准指定岗位或一批岗位；在审计无错误、岗位身份/简历/额度/高影响答案均核实后可直接提交。
  - autonomous：仅在用户另外明确规定自动提交范围、筛选规则与例外处理后启用；登录/验证码、未知高影响问题、额度冲突和不可逆不确定项仍触发人工接管。

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

未获提交授权时，保留页面并交付 URL、岗位、简历版本、关键字段核对结果和未完成项。获本次提交授权时，也必须先完成审计；提交前还要核项目级志愿/顺序/额度等隐藏门。执行提交后检查 HTTP 状态、业务 code/msg 和账号投递记录：业务失败时先确认没有生成记录，再定位并补齐允许自动处理的项目级门，最多做必要的有界重试；只有成功页、账号记录、确认邮件或用户明确确认才可登记为已提交。

### 7. Learn

将确定有效的站点控件、上传入口、日期行为、复用规律和可复现坑位增量写入 `references/site-knowledge.md`。失败只有在原因可复用时才记录；一次性坐标尝试不固化为通用规则。

## References

- ATS 家族经验：[ats-families.md](references/ats-families.md)
- 通用控件与审计：[fill-protocol.md](references/fill-protocol.md)
- 材料选择与留存：[application-materials.md](references/application-materials.md)
- 已验证站点差异：[site-knowledge.md](references/site-knowledge.md)

