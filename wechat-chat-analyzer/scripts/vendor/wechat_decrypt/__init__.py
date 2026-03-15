import os
import sys
import platform

def run_auto_decrypt(output_decrypted_dir: str):
    """
    执行微信自带解密流程
    由于 find_all_keys / decrypt_db 会直接去 import 甚至影响全局环境
    我们将以 subprocess 的形式来隔离执行它，避免修改 sys.path 污染当前运行时环境
    """
    system = platform.system()
    
    if system == "Darwin":  # macOS
        return False, "macOS 暂不支持自动从内存提取密钥。请使用以下步骤手动准备数据：\n1. 使用开源工具（如 wechat-decrypt）在 macOS 上提取并解密微信数据库\n2. 将解密后的 decrypted 目录复制到当前工作目录\n3. 重新运行分析命令"
    
    if system != "Windows":
        return False, "非 Windows 系统，未能执行自动破解。"

    script_dir = os.path.dirname(os.path.abspath(__file__))
    keys_file = os.path.join(output_decrypted_dir, "all_keys.json")

    # 创建独立的动态 config.json
    import json
    config_dict = {
        "db_dir": "", # 留空，让 config.py 自动去 %APPDATA% 找
        "keys_file": keys_file,
        "decrypted_dir": output_decrypted_dir,
    }
    config_path = os.path.join(script_dir, "config.json")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config_dict, f, ensure_ascii=False, indent=2)

    import subprocess
    
    # 步骤 1：寻找所有的 keys
    print("  [Vendor] 正在向 WeChat 内存中注入嗅探器寻找 aes_key...", flush=True)
    try:
        find_keys_script = os.path.join(script_dir, "find_all_keys.py")
        subprocess.run(
            [sys.executable, find_keys_script],
            cwd=script_dir,
            check=True,
            capture_output=True, # 抑制多余输出
            text=True
        )
    except subprocess.CalledProcessError as e:
        error_out = e.stderr or e.stdout
        if "Weixin.exe 未运行" in error_out:
            return False, "微信进程未运行，请先登录电脑版微信。"
        if "拒绝访问" in error_out or "Access is denied" in error_out or "OpenProcess" in error_out:
            return False, "权限不足！请以【管理员身份】运行你的终端或者 AI 客户端，否则无法读取微信内存。"
        return False, f"扫描密钥时发生错误: {error_out}"
    except Exception as e:
        return False, f"未知错误: {str(e)}"

    # 步骤 2：解密数据库
    print("  [Vendor] 正在为您脱壳数据库...", flush=True)
    try:
        decrypt_script = os.path.join(script_dir, "decrypt_db.py")
        subprocess.run(
            [sys.executable, decrypt_script],
            cwd=script_dir,
            check=True,
            capture_output=True,
            text=True
        )
    except subprocess.CalledProcessError as e:
        error_out = e.stderr or e.stdout
        return False, f"解密数据库时发生错误: {error_out}"
    except Exception as e:
        return False, f"解密时遭遇未知错误: {str(e)}"

    return True, "数据库解密成功。"
