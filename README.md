# WeChat Chat Analyzer Skill

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform: Windows|macOS](https://img.shields.io/badge/platform-Windows%20%7C%20macOS-lightgrey.svg)]()

一个 AI Agent Skill，用于深度分析微信聊天记录，生成互动习惯报告、情感走势、性格画像，并支持追问细节。

本项目数据库解密功能参考自 [wechat-decrypt](https://github.com/ylytdeng/wechat-decrypt) 项目。

## 功能特性

- 📊 **互动习惯分析**：主动性 PK、秒回率报告、聊天生物钟
- ☁️ **词云可视化**：双方高频词汇对比
- 📈 **情感走势**：月度聊天趋势、好感度变化
- 🎯 **性格画像**：基于聊天特征的性格分析
- 💡 **行动建议**：根据关系类型给出可执行建议
- 📁 **数据导出**：支持 TXT、CSV、HTML 格式导出

## 系统要求

- **操作系统**: Windows 10/11 (推荐), macOS (需手动准备数据)
- **Python**: 3.8 或更高版本
- **权限**: Windows 用户需要管理员权限
- **微信**: 电脑版微信 4.0+

## 安装教程

将 `wechat-chat-analyzer` 目录复制到你的 AI Agent 软件的 skills 目录下即可。

例如：

- Qwen CLI: `~/.qwen/skills/`

### 安装步骤

```bash
# 1. 克隆仓库
git clone https://github.com/UniUni2000/wechat-chat-analyzer.git

# 2. 复制到 skills 目录（以 Trae 为例）
cp -r wechat-chat-analyzer/wechat-chat-analyzer ~/.qwen/skills/

# 3. 安装依赖
pip install -r wechat-chat-analyzer/requirements.txt
```

## 使用方法

安装完成后，直接对你的 AI Agent 说（注意，一定要以管理员方式启动 agent 进程）：

> "分析我和 [好友名字] 的微信聊天记录"

AI 会自动完成：提取微信数据 → 运行分析 → 生成报告 → 与你讨论结果

## 输出文件

分析完成后，会在输出目录生成以下文件：

- `analysis_report.json` - 完整的分析报告（JSON 格式）
- `chat_export.txt` - 纯文本聊天记录
- `chat_export.csv` - 结构化 CSV 文件
- `chat_export.html` - 微信气泡对话风格（可截图分享）
- `wordcloud_*.png` - 词云图片
- `trend.png` - 消息量趋势图
- `monthly_bar.png` - 月度消息量对比柱状图
- `heatmap.png` - 聊天频率热力图
- `reply_speed.png` - 回复速度分析图

## 故障排查

| 问题            | 解决方案                                                     |
| ------------- | -------------------------------------------------------- |
| 权限不足          | Windows 用户请以管理员身份运行 AI Agent                             |
| 微信进程未找到       | 确保微信已登录并保持运行                                             |
| 数据库解密失败       | 重启微信和 AI Agent 后重试                                       |
| 未找到聊天记录       | 确认好友名称正确，或尝试使用 wxid                                      |
| macOS 数据目录找不到 | 手动检查 `~/Library/Containers/com.tencent.xinWeChat/...` 路径 |

更多故障排查信息请参考 [wechat-chat-analyzer/references/troubleshooting.md](wechat-chat-analyzer/references/troubleshooting.md)

## 隐私声明

- 所有数据处理完全在本地完成，**绝不上传云端**
- 不会收集任何用户数据
- 分析完成后，解密的数据文件保留在用户本地
- AI 只读取本地生成的分析结果，不会上传原始聊天记录

## 免责声明

本工具仅供学习研究使用，请遵守相关法律法规：

- 仅分析您自己的聊天记录
- 尊重他人隐私，未经同意不得分析他人数据
- 禁止用于任何非法用途

## 许可证

[MIT License](LICENSE) © 2026 UniUni2000

## 致谢

- 数据库解密基于 [wechat-decrypt](https://github.com/ylytdeng/wechat-decrypt)
- 感谢所有开源贡献者
