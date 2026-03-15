# 异常说明与排查建议

当技能运行失败时，可能是以下原因导致的，请按照对应建议进行排查：

## 常见失败原因及排查建议

1. **权限不足**
   - **症状**: 无法从微信内存中提取密钥，提示 "拒绝访问" 或 "权限不足"
   - **建议**: Windows 用户请以管理员权限启动支持 skills 的 agent 程序

2. **微信版本问题**
   - **症状**: 提示 "无法找到微信进程" 或 "密钥提取失败"
   - **建议**: 确保使用最新版本的微信 PC 客户端，旧版本可能不支持密钥提取

3. **Python 环境问题**
   - **症状**: 提示 "ModuleNotFoundError" 或 "Python 未找到"
   - **建议**: 确保激活了正确的 Python 环境，并已安装所有依赖库

4. **Node.js 版本问题** (仅适用于 CLI 类 agent)
   - **症状**: 提示 "Node.js 版本过低" 或相关依赖错误
   - **建议**: 升级 Node.js 到最新版本，确保兼容性

5. **微信未登录**
   - **症状**: 提示 "未找到微信进程" 或 "微信未登录"
   - **建议**: 确保微信 PC 客户端已登录并保持运行状态

6. **数据库解密失败**
   - **症状**: 提示 "解密失败" 或 "无法找到数据库"
   - **建议**: 尝试重启微信和 agent 程序，或手动使用其他工具解密微信数据库

7. **好友名称不匹配**
   - **症状**: 提示 "未找到与 'xxx' 的聊天记录"
   - **建议**: 确认好友的正确备注名或 Weixin ID，避免使用昵称的变体

8. **macOS 数据目录找不到**
   - **症状**: 提示 "未能自动检测微信数据目录"
   - **建议**: 手动检查 `~/Library/Containers/com.tencent.xinWeChat/Data/Library/Application Support/com.tencent.xinWeChat/` 目录是否存在 `4.0b*` 文件夹

9. **macOS 解密数据未找到**
   - **症状**: 提示 "数据库目录不存在" 或 "数据库目录结构不正确"
   - **建议**: 确保已使用第三方工具解密数据，并将 `decrypted` 目录复制到当前工作目录

## 手动准备解密数据

如果自动解密失败，可以按照以下步骤手动准备数据：

### Windows 系统

1. 在 Windows 上使用开源工具 [wechat-decrypt](https://github.com/ylytdeng/wechat-decrypt) 提取并解密微信数据库
2. 将解密后的 `decrypted` 目录复制到用户对话路径下
3. 重新运行分析脚本

### macOS 系统

**数据目录位置说明：**

macOS 版微信的数据存储在以下路径：
```
~/Library/Containers/com.tencent.xinWeChat/Data/Library/Application Support/com.tencent.xinWeChat/
```

其中包含以版本号命名的文件夹（如 `4.0b4.0.9`），聊天记录数据库位于该文件夹下的相应目录中。

**推荐使用的开源工具：**

- [wechat-decrypt](https://github.com/ylytdeng/wechat-decrypt) - 支持 macOS 版本
- [wechat-dump-rs](https://github.com/0xlane/wechat-dump-rs) - 跨平台支持

**数据准备的具体步骤：**

1. **找到微信数据目录**
   - 打开 Finder，按 `Cmd+Shift+G` 输入路径：`~/Library/Containers/com.tencent.xinWeChat/Data/Library/Application Support/com.tencent.xinWeChat/`
   - 确认存在以 `4.0b` 开头的版本文件夹

2. **使用解密工具提取数据**
   - 下载并运行支持 macOS 的微信解密工具
   - 根据工具说明，指定微信数据目录进行解密
   - 解密完成后会生成 `decrypted` 目录，包含解密后的数据库文件

3. **复制解密数据到工作目录**
   - 将解密工具生成的 `decrypted` 目录复制到当前技能的工作目录
   - 确保目录结构完整，包含 `message_*.db` 等数据库文件

4. **重新运行分析脚本**
   - 返回技能界面，重新执行分析操作