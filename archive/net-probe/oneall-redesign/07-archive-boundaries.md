# 归档边界

## 1. 当前主线

当前重构主线只包括：

- `oneall-redesign`：设计手册、领域边界、技术架构、任务清单。
- `oneall-antd-prototype`：React + Ant Design 原型和可执行契约测试。

## 2. 旧 Vue 前端

相邻旧项目中的 `OneAll/frontend` 是现有 Vue + Element Plus 前端，只作为旧实现参考。

使用边界：

- 可以参考旧交互、旧 API 和旧业务细节。
- 不作为下一版设计基准。
- 不继续在旧 Vue 技术栈上扩展下一版原型。
- 不删除旧项目，避免影响存量代码和历史参考。

## 3. 误做的 Vue + Element Plus 独立原型

`oneall-frontend-prototype` 属于早期误做的 Vue + Element Plus 独立原型。

当前工作区未发现该目录；如果后续从备份或其他分支恢复出来，应按归档处理：

- 不参与新原型预览。
- 不作为任务清单交付物。
- 不进入主线 README 的预览入口。
- 只允许作为历史参考移动到 archive 或删除。

## 4. 防回退规则

新增页面、契约或测试时，必须以 React + Ant Design 原型为主线。

如果需要参考旧项目，只能抽取业务规则、API 形态或交互经验，不能恢复旧一级导航、固定资产模型或重工具库。
