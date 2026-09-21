# Generic form filling protocol

## 1. Open and login

打开官方岗位详情页进入申请流程。需要登录时让用户处理密码、短信验证码、滑块和 CAPTCHA；可以继续读取登录后的页面，但不记录认证对象。

## 2. Resume upload

优先查找 `input[type=file]` 或可见的选择文件入口。遇到外层按钮和内层按钮同时匹配时，选择实际触发 file chooser 的内层入口。上传后等待页面状态变化并读回附件名。

简历解析覆盖前先保存本次定制文案或私有快照；表单已经完整时不重复覆盖。浏览器扩展上传受阻时，按工具文档检查文件 URL 权限，不把扩展内部 API 当作数据源。

## 3. Text fields

按标签、placeholder 或已确认的区块定位 input/textarea。重复 placeholder 必须先建立索引与区块映射，再操作。长文本使用本次材料快照中符合字数限制的版本。

## 4. Selects and custom controls

- 原生 select：选择 option 后读回选中标签；
- combobox：打开可见弹层，按选项文本选择；
- custom tag/input：确认页面是否要求真实键盘事件或用户手点；
- checkbox/radio/switch：读 `checked`、`aria-checked`、`aria-selected` 和可见标签，不只看颜色或 innerText。

## 5. Dates

先确认精度是日还是月，再使用页面支持的输入或日历操作。年/月选择器可能倒序、分组或默认落在未来年份；输入后读回实际显示值。不要把解析错误的年份、邀请日期或当前日期当作候选人的教育/工作事实。

## 6. Read-back audit

建立允许审计的业务字段清单，只读取当前页面已确认的字段，不扫描全部输入框。伪代码：

```javascript
allowedFields.map(({label, element}) => {
  if (element.matches('input[type=hidden], input[type=password]')) return {label, omitted: true};
  if (element.matches('input[type=checkbox], input[type=radio]')) return {label, checked: element.checked};
  if (element.matches('select')) return {label, selected: [...element.selectedOptions].map(o => o.text)};
  if (element.matches('input[type=file]')) return {label, files: [...element.files].map(f => f.name)};
  return {label, value: element.value ?? element.innerText};
});
```

敏感字段用页面内比较返回布尔结果；不要把原值写进终端、快照或回复。自定义下拉、日期、textarea、附件和解析残留必须纳入最终审计。

页面级读回只证明当前前端状态。若站点会把资料写入共享简历/profile、自动复用到后续申请、保存时做字段转换，或已验证存在 rehydrate/反向映射问题，则保存/提交后还要做**持久化状态审计**：优先读取官方同源 API、独立详情页或重新加载后的只读页，核对高影响结构化字段的服务器真值。共享“最新简历”与单次 application snapshot 必须区分；拿不到历史申请快照时，不得用当前共享资料反推某次历史投递当时的精确值。

## 7. Parser residue audit

简历解析常把区块标题、公司名或字段名残留到描述中，也可能把项目角色/日期/链接错位。逐个检查 textarea 与相邻字段；修正只能使用已核实材料快照的文字，不能用猜测替换。

## 8. Project-level submit gates

最终提交前除简历字段外，还要单独核对项目级门：总投递额度、同单位额度、志愿/aspiration 顺序、投后是否可改/可撤销、项目级确认项。它们可能只在第一次提交失败后才由 ATS 弹出，不能因为表单“必填=0”就假设可以直接提交。

提交时同时判断 HTTP 状态和业务响应。HTTP 200 + 非成功业务 code/msg 仍是失败。若出现“志愿不完整”“顺序缺失”“超过项目设置”等错误：

1. **先查投递记录**：确认失败请求没有实际生成申请，避免下一次重试造成重复；
2. **定位缺失门**：优先读官方项目配置、实际弹窗、账号投递列表；必要时只读分析前端调用逻辑，不凭错误文案猜字段；
3. **判断授权边界**：若唯一可选值只是完成当前已授权岗位的必要参数，且不额外消耗/重排其他稀缺志愿，可沿用当前最终提交授权；若会占用有限志愿、改变优先级、不可修改或影响其他岗位，必须再次人工确认；
4. **有界重试**：补齐已确认参数后最多做必要的有限重试，不循环提交；
5. **提交后再查记录**：要求账号/官方 API 出现稳定 application ID、岗位身份、志愿顺序和提交时间，再登记 Submitted。

## 9. Page handoff

交给用户确认时保留当前页面和 URL。只有当前浏览器工具明确支持页面保留 API 才调用该 API；否则如实提供 URL、已保存状态和未完成字段，不宣称跨回合保留。

## 10. Subsequent applications on the same site

先检查账号是否自动带入资料，再决定是否上传。重点复核岗位、城市、简历版本、志愿额度和新增问题。复用规律只按站点实际验证结果采用；不能因为第一次提交成功就推断第二个未提交岗位一定复用。

