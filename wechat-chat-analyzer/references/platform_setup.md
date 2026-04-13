# 平台数据准备指南

## Windows

保持电脑版微信处于登录状态即可，脚本会自动从内存提取密钥并解密数据库。

**要求**: 以管理员权限启动 agent 程序。

## macOS

由于系统安全限制（SIP），无法从内存直接提取密钥，需手动准备解密数据：

1. **定位微信数据目录**
   - Finder 中按 `Cmd+Shift+G` 输入：`~/Library/Containers/com.tencent.xinWeChat/Data/Library/Application Support/com.tencent.xinWeChat/`
   - 进入 `4.0b*/` 目录，找到 `db_storage` 文件夹

2. **使用第三方工具解密数据库**
   - 推荐 [wechat-decrypt](https://github.com/ylytdeng/wechat-decrypt) 或类似工具
   - 按工具说明提取并解密微信数据库文件

3. **复制解密数据到工作目录**
   - 将生成的 `decrypted` 目录完整复制到当前用户对话路径下
   - 确保结构为：`{用户对话路径}/decrypted/message_*.db`

## Linux

暂不支持自动密钥提取。请先在 Windows 或 macOS 上解密数据，然后将 `decrypted` 目录复制到用户对话路径下。
