# v1.0.0 · 调查工作流与完整随包版

- Tag: `v1.0.0-workflow-20261011`
- Published: 2026-10-10T20:00:00Z
- Source: https://github.com/Minglink/dsh-infinite-gen-5/releases/tag/v1.0.0-workflow-20261011

## Release notes

本版保留 Core 8 / Full 38，新增函数上下文聚合与可恢复调查工作流。

- ig5_decompile style=dossier：汇总伪代码、CFG、调用者、被调用者和栈帧，保留来源、部分结果、错误与截断。
- ig5_profile workspace：保存任务、假设、下一步和系统快照；CAS 防止覆盖并发更新，旧数据库修订或附件明确标记 stale，引用报告按 SHA-256 校验。
- 修复新版 PowerShell/.NET 下 ZIP 读取兼容问题，增加公开 CRC32 检查；Windows PowerShell 5.1 保留长度、固定 ZIP 与逐文件 SHA 校验。
- 工作台统一处理真实后端的 hits/calls/text/items/rows 返回字段与数字权限；同一样本重开后清理旧视图，调用关系读取失败明确显示。
- 视图请求携带预期快照（expected_snapshot），受理前及响应后核对 target/projectId/artifactId/sha256/engine/provider/attachmentId/dbRevision 八项来源身份，拒绝过期读取；旧附件的排队写操作不会转投新附件。
- opening 阶段来源身份不完整时等待就绪，避免提前发起无效读取。
- 调查任务来源字段损坏时明确报错并保留原文件。

完整 ZIP 面向 Windows x64，包含 Ghidra / Java / Python / x64dbg 与固定上游源码、许可证；默认 Reverse 使用随包 Ghidra provider。需已安装 DeepSeek Harness。下载 .zip 和 .sha256，完整解压后运行 plugin/install.ps1，并正常重开 DSH；完整包可离线安装，无需另跑 setup。

本包已从 ZIP 隔离离线安装，再通过两轮真实随包引擎的 38 工具夹具验收（含 12 项审批工具检查与生成 PE 的 x64dbg 执行）；新调查流程也在该安装副本通过。DSH 0.2.1-alpha.1 SDK 验证与引擎验证分别进行，不代表桌面审批界面已实测。测试范围不保证任意样本；手机离线执行及 capa/FLOSS 尚未纳入本版。

真实浏览器夹具作为发布门禁，要求在 1280px 与 390px 视口完成全部指定场景。数据来自模拟响应，不能代表真实 DSH GUI 或物理手机已经验收；实际通过数量见验收报告。

Source commit: 0129bc3ced2c6688ed72109d6e913ac4385798b6
ZIP SHA-256: 0ff08a77ebddb0c59dde080d73dd4a577ce73564f864f61d5a8654618223a1fc
逐文件归档验证数量: 52743

公开 ZIP、SHA-256 文件和验收报告已通过匿名下载核验。

## Assets

- IG5-1.0.0-Windows-x64-workflow-full-20261011.zip — not mirrored: exceeds 90 MiB per-asset guard — https://github.com/Minglink/dsh-infinite-gen-5/releases/download/v1.0.0-workflow-20261011/IG5-1.0.0-Windows-x64-workflow-full-20261011.zip
- [IG5-1.0.0-Windows-x64-workflow-full-20261011.zip.sha256](assets/IG5-1.0.0-Windows-x64-workflow-full-20261011.zip.sha256)
- [IG5-1.0.0-workflow-verification-20261011.json](assets/IG5-1.0.0-workflow-verification-20261011.json)
