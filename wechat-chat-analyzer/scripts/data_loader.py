"""
微信聊天记录数据加载器
=======================
功能: 从 wechat-decrypt 解密后的 SQLite 数据库中提取指定好友的1对1单聊记录。
隐私: 所有数据处理完全在本地完成。

数据库结构:
  - contact/contact.db: 联系人表 (username, nick_name, remark)
  - message/message_N.db: 消息表 Msg_<md5(wxid)>, 字段包括:
      local_type(1=文本,3=图片,34=语音,47=表情...),
      create_time(unix时间戳), message_content, status(2=自己发送)
"""

import os
import sys
import sqlite3
import hashlib
import json
import re
from datetime import datetime, timezone, timedelta

# 中国时区 UTC+8
CN_TZ = timezone(timedelta(hours=8))


def find_decrypted_dir(search_path: str) -> str:
    """自动搜索解密后的数据库目录。

    支持以下情况:
    1. 直接传入 decrypted 目录 (包含 message/, contact/ 子目录)
    2. 传入 wechat-decrypt 项目根目录 (自动找到 decrypted/)
    """
    # 检查是否直接是解密目录
    if os.path.isdir(os.path.join(search_path, "message")) and os.path.isdir(
        os.path.join(search_path, "contact")
    ):
        return search_path

    # 检查子目录 decrypted/
    decrypted = os.path.join(search_path, "decrypted")
    if os.path.isdir(decrypted) and os.path.isdir(os.path.join(decrypted, "message")):
        return decrypted

    raise FileNotFoundError(
        f"无法在 '{search_path}' 中找到解密后的数据库目录。\n"
        f"请确保目录下包含 message/ 和 contact/ 子目录。\n"
        f"如尚未解密，请先运行 wechat-decrypt 项目的 decrypt_db.py。"
    )


def load_contacts(db_dir: str) -> dict:
    """加载联系人映射: {wxid: {nick_name, remark, display_name}}"""
    contact_db = os.path.join(db_dir, "contact", "contact.db")
    if not os.path.exists(contact_db):
        print(f"[WARN] 联系人数据库不存在: {contact_db}")
        return {}

    contacts = {}
    conn = sqlite3.connect(contact_db)
    try:
        # 尝试查询所有字段，看看是否有存储微信号的字段
        cursor = conn.execute("PRAGMA table_info(contact)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"[INFO] 联系人表字段: {columns}")

        # 尝试查询包含微信号的字段
        if "alias" in columns:
            rows = conn.execute(
                "SELECT username, nick_name, remark, alias FROM contact"
            ).fetchall()
            for username, nick_name, remark, alias in rows:
                display = remark if remark else nick_name if nick_name else username
                contacts[username] = {
                    "nick_name": nick_name or "",
                    "remark": remark or "",
                    "alias": alias or "",  # 微信号
                    "display_name": display,
                }
        elif "wechat_id" in columns:
            rows = conn.execute(
                "SELECT username, nick_name, remark, wechat_id FROM contact"
            ).fetchall()
            for username, nick_name, remark, wechat_id in rows:
                display = remark if remark else nick_name if nick_name else username
                contacts[username] = {
                    "nick_name": nick_name or "",
                    "remark": remark or "",
                    "wechat_id": wechat_id or "",  # 微信号
                    "display_name": display,
                }
        else:
            # 回退到原始查询
            rows = conn.execute(
                "SELECT username, nick_name, remark FROM contact"
            ).fetchall()
            for username, nick_name, remark in rows:
                display = remark if remark else nick_name if nick_name else username
                contacts[username] = {
                    "nick_name": nick_name or "",
                    "remark": remark or "",
                    "display_name": display,
                }
    except Exception as e:
        print(f"[WARN] 读取联系人数据库失败: {e}")
    finally:
        conn.close()

    return contacts


def resolve_friend(contacts: dict, friend_input: str) -> str:
    """将用户输入的好友名解析为 wxid。

    支持: wxid 直接匹配、备注名匹配、昵称匹配、WeChat ID匹配、模糊匹配。
    """
    # 去除好友名称中的多余引号
    friend_input = friend_input.strip("\"'")

    # 直接是 wxid
    if friend_input in contacts:
        return friend_input

    # 处理 Weixin ID 格式 (wxid_ 开头)
    if friend_input.startswith("wxid_"):
        # 尝试在 contacts 中查找精确匹配
        for wxid in contacts:
            if wxid == friend_input:
                return wxid
        # 如果找不到精确匹配，仍然返回输入的 wxid（可能是新好友）
        return friend_input

    lower_input = friend_input.lower()

    # 精确匹配备注名、昵称或微信号（不区分大小写）
    exact_matches = []
    for wxid, info in contacts.items():
        if lower_input == info["remark"].lower():
            exact_matches.append((wxid, "备注名"))
        elif lower_input == info["nick_name"].lower():
            exact_matches.append((wxid, "昵称"))
        elif "alias" in info and lower_input == info["alias"].lower():
            exact_matches.append((wxid, "微信号"))
        elif "wechat_id" in info and lower_input == info["wechat_id"].lower():
            exact_matches.append((wxid, "微信号"))

    # 如果有精确匹配，返回第一个
    if exact_matches:
        wxid, match_type = exact_matches[0]
        print(f"[INFO] 找到精确匹配: {wxid} ({match_type}: {friend_input})")
        return wxid

    # 模糊匹配 (包含关系)
    candidates = []
    for wxid, info in contacts.items():
        if lower_input in info["remark"].lower():
            candidates.append((wxid, f"备注名包含 '{friend_input}'"))
        elif lower_input in info["nick_name"].lower():
            candidates.append((wxid, f"昵称包含 '{friend_input}'"))
        elif "alias" in info and lower_input in info["alias"].lower():
            candidates.append((wxid, f"微信号包含 '{friend_input}'"))
        elif "wechat_id" in info and lower_input in info["wechat_id"].lower():
            candidates.append((wxid, f"微信号包含 '{friend_input}'"))
        elif lower_input in wxid.lower():
            candidates.append((wxid, f"wxid 包含 '{friend_input}'"))

    if len(candidates) == 1:
        wxid, reason = candidates[0]
        print(f"[INFO] 找到模糊匹配: {wxid} ({reason})")
        return wxid
    elif len(candidates) > 1:
        print(f"[INFO] 找到多个匹配:")
        for wxid, reason in candidates[:10]:
            info = contacts[wxid]
            print(
                f"  - {wxid} ({reason}, 昵称: {info['nick_name']}, 备注: {info['remark']})"
            )
        print(f"请使用更精确的名称或 wxid 重试。")
        return None

    # 尝试使用原始输入作为 wxid
    print(f"[INFO] 未找到匹配的好友，尝试将 '{friend_input}' 作为 wxid 使用")
    return friend_input


def _find_message_table(db_dir: str, wxid: str) -> list:
    """在所有 message_N.db 中查找目标用户的消息表。

    返回: [(db_path, table_name), ...]
    """
    table_hash = hashlib.md5(wxid.encode("utf-8")).hexdigest()
    table_name = f"Msg_{table_hash}"

    message_dir = os.path.join(db_dir, "message")
    if not os.path.isdir(message_dir):
        return []

    results = []
    for filename in sorted(os.listdir(message_dir)):
        if (
            filename.startswith("message_")
            and filename.endswith(".db")
            and "fts" not in filename
            and "resource" not in filename
        ):
            db_path = os.path.join(message_dir, filename)
            try:
                conn = sqlite3.connect(db_path)
                exists = conn.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                    (table_name,),
                ).fetchone()
                conn.close()
                if exists:
                    results.append((db_path, table_name))
            except Exception:
                pass

    return results


def extract_messages(
    db_dir: str, wxid: str, my_name: str = "我", friend_display: str = None
) -> list:
    """提取指定好友的所有1对1文本聊天记录。

    参数:
      db_dir: 解密后数据库目录
      wxid: 好友 wxid
      my_name: 自己的显示名
      friend_display: 好友显示名

    返回: 按时间排序的消息列表
      [{time: str, timestamp: int, sender: str, content: str, is_me: bool}, ...]
    """
    # 排除群聊
    if "@chatroom" in wxid:
        raise ValueError(f"'{wxid}' 是群聊，本工具仅支持1对1单聊分析。")

    friend_name = friend_display or wxid
    tables = _find_message_table(db_dir, wxid)

    if not tables:
        raise FileNotFoundError(
            f"未找到与 '{wxid}' 的聊天记录。\n"
            f"可能原因: wxid不正确、消息在未解密的数据库中、或确实无聊天记录。"
        )

    messages = []
    for db_path, table_name in tables:
        conn = sqlite3.connect(db_path)
        try:
            # 尝试获取real_sender_id字段，如果不存在则回退到status
            try:
                # 优先使用real_sender_id (微信4.X版本)
                rows = conn.execute(
                    f"""
                    SELECT create_time, local_type, message_content, status, real_sender_id
                    FROM [{table_name}]
                    ORDER BY create_time ASC
                """
                ).fetchall()

                for create_time, local_type, content, status, real_sender_id in rows:
                    # 跳过非文本消息 (但保留类型信息用于统计)
                    # real_sender_id=3 为自己发送 (微信4.X版本)
                    # 回退到 status==2 (旧版本)
                    is_me = (real_sender_id == 3) or (status == 2)
                    sender = my_name if is_me else friend_name

                    # 处理消息内容
                    if isinstance(content, bytes):
                        try:
                            content = content.decode("utf-8", errors="replace")
                        except Exception:
                            content = "(二进制内容)"

                    if content is None:
                        content = ""

                    # 文本消息标记
                    msg_type_label = {
                        1: "text",
                        3: "image",
                        34: "voice",
                        42: "card",
                        43: "video",
                        47: "emoji",
                        48: "location",
                        49: "link",
                        50: "call",
                        10000: "system",
                        10002: "recall",
                    }.get(local_type, f"type_{local_type}")

                    dt = datetime.fromtimestamp(create_time, tz=CN_TZ)

                    messages.append(
                        {
                            "time": dt.strftime("%Y-%m-%d %H:%M:%S"),
                            "timestamp": create_time,
                            "sender": sender,
                            "is_me": is_me,
                            "content": content,
                            "msg_type": msg_type_label,
                            "weekday": dt.weekday(),  # 0=周一
                            "hour": dt.hour,
                        }
                    )
            except Exception:
                # 如果real_sender_id字段不存在，回退到旧逻辑
                rows = conn.execute(
                    f"""
                    SELECT create_time, local_type, message_content, status
                    FROM [{table_name}]
                    ORDER BY create_time ASC
                """
                ).fetchall()

                for create_time, local_type, content, status in rows:
                    # 跳过非文本消息 (但保留类型信息用于统计)
                    is_me = status == 2
                    sender = my_name if is_me else friend_name

                    # 处理消息内容
                    if isinstance(content, bytes):
                        try:
                            content = content.decode("utf-8", errors="replace")
                        except Exception:
                            content = "(二进制内容)"

                    if content is None:
                        content = ""

                    # 文本消息标记
                    msg_type_label = {
                        1: "text",
                        3: "image",
                        34: "voice",
                        42: "card",
                        43: "video",
                        47: "emoji",
                        48: "location",
                        49: "link",
                        50: "call",
                        10000: "system",
                        10002: "recall",
                    }.get(local_type, f"type_{local_type}")

                    dt = datetime.fromtimestamp(create_time, tz=CN_TZ)

                    messages.append(
                        {
                            "time": dt.strftime("%Y-%m-%d %H:%M:%S"),
                            "timestamp": create_time,
                            "sender": sender,
                            "is_me": is_me,
                            "content": content,
                            "msg_type": msg_type_label,
                            "weekday": dt.weekday(),  # 0=周一
                            "hour": dt.hour,
                        }
                    )
        except Exception as e:
            print(f"[WARN] 查询 {db_path} 失败: {e}")
        finally:
            conn.close()

    # 按时间排序
    messages.sort(key=lambda m: m["timestamp"])
    return messages


def get_text_messages(messages: list) -> list:
    """从全部消息中筛选纯文本消息。"""
    return [m for m in messages if m["msg_type"] == "text"]


def load_chat_data(db_dir: str, friend: str, my_name: str = "我") -> dict:
    """一键加载聊天数据的便捷接口。

    返回完整的数据包:
    {
        "wxid": str,
        "friend_name": str,
        "my_name": str,
        "contacts": dict,
        "all_messages": list,      # 所有类型消息
        "text_messages": list,     # 纯文本消息
        "total_count": int,
        "text_count": int,
    }
    """
    try:
        db_dir = find_decrypted_dir(db_dir)
        print(f"[INFO] 使用数据库目录: {db_dir}")

        contacts = load_contacts(db_dir)
        print(f"[INFO] 加载了 {len(contacts)} 个联系人")

        if not contacts:
            print("[WARN] 未加载到任何联系人，可能是联系人数据库不存在或损坏")

        wxid = resolve_friend(contacts, friend)
        if not wxid:
            raise ValueError(f"无法匹配好友: '{friend}'")

        friend_info = contacts.get(wxid, {})
        friend_name = friend_info.get("display_name", wxid)

        print(f"[+] 目标好友: {friend_name} ({wxid})")

        all_messages = extract_messages(db_dir, wxid, my_name, friend_name)
        text_messages = get_text_messages(all_messages)

        print(
            f"[+] 共提取 {len(all_messages)} 条消息 (其中文本 {len(text_messages)} 条)"
        )

        if not all_messages:
            print("[WARN] 未提取到任何消息，可能是该好友没有聊天记录")

        return {
            "db_dir": db_dir,
            "wxid": wxid,
            "friend_name": friend_name,
            "my_name": my_name,
            "contacts": contacts,
            "all_messages": all_messages,
            "text_messages": text_messages,
            "total_count": len(all_messages),
            "text_count": len(text_messages),
        }
    except Exception as e:
        print(f"[ERROR] 加载聊天数据失败: {e}")
        raise


if __name__ == "__main__":
    # 独立测试用
    import argparse

    parser = argparse.ArgumentParser(description="微信聊天数据加载器")
    parser.add_argument("--db-dir", required=True, help="解密后数据库目录")
    parser.add_argument("--friend", required=True, help="好友备注名/昵称/wxid")
    parser.add_argument("--my-name", default="我", help="自己的显示名")
    args = parser.parse_args()

    data = load_chat_data(args.db_dir, args.friend, args.my_name)
    print(f"\n=== 数据加载完成 ===")
    print(f"好友: {data['friend_name']} ({data['wxid']})")
    print(f"总消息数: {data['total_count']}")
    print(f"文本消息: {data['text_count']}")
    if data["text_messages"]:
        first = data["text_messages"][0]
        last = data["text_messages"][-1]
        print(f"首条: [{first['time']}] {first['sender']}: {first['content'][:50]}")
        print(f"末条: [{last['time']}] {last['sender']}: {last['content'][:50]}")
