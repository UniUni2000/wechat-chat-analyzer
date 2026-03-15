"""
微信聊天记录分析器 — 主入口
============================
一键运行: 数据加载 → 统计计算 → 图表生成 → 数据导出 → 输出 JSON 报告

使用方式:
  python wechat_analyzer.py \
    --db-dir /path/to/decrypted \
    --friend "好友备注名或wxid" \
    --output-dir ./output \
    --my-name "我" \
    --sample-size 50

所有数据处理完全在本地完成，无任何网络请求。
"""

import os
import sys
import json
import argparse
import time

# 确保能找到同级模块
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

# 首先检查依赖
print("正在检查依赖...")
dependency_checker = os.path.join(SCRIPT_DIR, 'check_dependencies.py')
if os.path.exists(dependency_checker):
    try:
        import subprocess
        result = subprocess.run([sys.executable, dependency_checker], check=False)
        if result.returncode != 0:
            print("\n⚠️ 依赖检查失败，可能会影响分析功能")
    except Exception as e:
        print(f"\n⚠️ 依赖检查时发生错误: {e}")
else:
    print("\n⚠️ 依赖检查脚本不存在")

from data_loader import load_chat_data
from stats_engine import compute_all_stats
from visualizer import generate_all_charts
from data_exporter import export_all


def main():
    parser = argparse.ArgumentParser(
        description="💬 微信聊天记录深度分析器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python wechat_analyzer.py --friend "小明"
  python wechat_analyzer.py --friend "wxid_xxx" --my-name "我"
  python wechat_analyzer.py --interactive  # 交互式输入联系人信息
        """,
    )

    parser.add_argument("--friend", help="好友的备注名、昵称或 wxid")
    parser.add_argument(
        "--db-dir", default=None, help="解密后数据库目录 (默认: 自动搜索)"
    )
    parser.add_argument(
        "--output-dir",
        default="./wechat_analysis_output",
        help="输出目录 (默认: ./wechat_analysis_output，位于用户对话路径下)",
    )
    parser.add_argument("--my-name", default="我", help="自己的显示名 (默认: 我)")
    parser.add_argument(
        "--sample-size",
        type=int,
        default=50,
        help="采样对话条数，供 LLM 深度分析 (默认: 50)",
    )
    parser.add_argument(
        "--modules",
        default="all",
        help="要运行的模块，逗号分隔: all/stats/charts/export (默认: all)",
    )
    parser.add_argument(
        "--interactive", action="store_true", help="交互式输入联系人信息"
    )

    args = parser.parse_args()
    
    # 处理联系人信息输入
    if args.interactive or not args.friend:
        guidance_script = os.path.join(SCRIPT_DIR, 'user_guidance.py')
        if os.path.exists(guidance_script):
            try:
                import subprocess
                result = subprocess.run(
                    [sys.executable, guidance_script],
                    capture_output=True,
                    text=True,
                    check=False
                )
                if result.returncode == 0:
                    # 从输出中提取联系人标识
                    for line in result.stdout.split('\n'):
                        if '📋 联系人标识:' in line:
                            args.friend = line.split(':', 1)[1].strip()
                            break
                else:
                    print(f"\n⚠️ 交互式输入失败: {result.stderr}")
            except Exception as e:
                print(f"\n⚠️ 运行用户引导脚本时发生错误: {e}")
        
    if not args.friend:
        print("\n❌ 未提供联系人信息，无法继续")
        sys.exit(1)

    start_time = time.time()

    print("=" * 60)
    print("  💬 微信聊天记录深度分析器")
    print("  🔒 所有数据在本地处理，绝不上传云端")
    print("=" * 60)

    # 解析模块
    modules = set(args.modules.split(","))
    run_all = "all" in modules

    import platform

    is_windows = platform.system() == "Windows"

    # Step 0: 全自动解密
    if is_windows:
        print("\n🔑 [0/4] 正在尝试自动提取微信密钥并解密数据库...")
    else:
        print("\n🔑 [0/4] 检测到 macOS 系统，将使用已解密数据或引导手动准备...")

    # 确定数据库目录
    db_dir = args.db_dir

    # 如果用户未指定，使用当前工作目录（用户对话路径）
    if not db_dir:
        # 当前工作目录即为用户对话路径
        user_conversation_dir = os.getcwd()
        db_dir = os.path.join(user_conversation_dir, "decrypted")
        print(f"  📁 使用用户对话路径作为数据库目录: {db_dir}")
        # 创建目录（如果不存在）
        os.makedirs(db_dir, exist_ok=True)
    else:
        print(f"  📁 使用用户指定的数据库目录: {db_dir}")

    if is_windows:
        try:
            from vendor.wechat_decrypt import run_auto_decrypt

            success, msg = run_auto_decrypt(db_dir)
            if success:
                print(f"  🔑 {msg}")
            else:
                print(f"\n⚠️ 自动解密遇到问题: {msg}")
                print(f"将尝试直接使用已有解密数据。")
        except ImportError as e:
            print(f"  ⚠️ 未找到内置自动化解密模块 ({e})，跳过自动抓取。")
    else:
        print(
            "  ⚠️ 操作系统非 Windows（Mac/Linux），开源解密引擎可能无法自动抓取内存密钥。"
        )
        print("  将尝试直接使用该目录下已解密好的缓存文件。")

    # 检查数据库目录是否存在
    if not os.path.exists(db_dir):
        print(f"\n❌ 数据库目录不存在: {db_dir}")
        print("\n💡 解决方案：")
        print("👉 请确保微信已登录，并且你有管理员权限运行此脚本。")
        print("👉 或者使用 --db-dir 参数指定已解密的数据库目录。")
        sys.exit(1)

    if not os.path.isdir(os.path.join(db_dir, "message")) or not os.path.isdir(
        os.path.join(db_dir, "contact")
    ):
        print(f"\n❌ 数据库目录结构不正确！")
        print(f"📁 当前数据库路径: {db_dir}")
        print("需要包含 message/ 和 contact/ 子目录。")
        print("\n💡 解决方案：")
        if is_windows:
            print(
                "👉 如果你是 Windows 用户：请以管理员身份运行脚本，让系统自动提取密钥并解密。"
            )
        else:
            print(
                "👉 macOS 用户：请使用第三方工具（如 wechat-decrypt）提取并解密微信数据库，然后将 decrypted 目录复制到当前路径。"
            )
        print(
            "👉 如果你已有解密数据：请确保数据结构正确，或使用 --db-dir 参数指定正确的目录。"
        )
        sys.exit(1)

    # Step 1: 数据加载
    print("\n📂 [1/4] 加载聊天数据...")
    try:
        chat_data = load_chat_data(db_dir, args.friend, args.my_name)
    except Exception as e:
        print(f"\n❌ 数据加载失败: {e}")
        sys.exit(1)

    if not chat_data["all_messages"]:
        print("❌ 未找到任何消息记录。")
        sys.exit(1)

    my_name = chat_data["my_name"]
    friend_name = chat_data["friend_name"]

    os.makedirs(args.output_dir, exist_ok=True)

    # 完整输出报告
    report = {
        "meta": {
            "wxid": chat_data["wxid"],
            "friend_name": friend_name,
            "my_name": my_name,
            "total_messages": chat_data["total_count"],
            "text_messages": chat_data["text_count"],
            "analysis_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        },
        "stats": None,
        "charts": None,
        "exports": None,
    }

    # Step 2: 统计分析
    if run_all or "stats" in modules:
        print("\n📊 [2/4] 计算统计指标...")
        stats = compute_all_stats(
            chat_data["all_messages"],
            chat_data["text_messages"],
            my_name,
            friend_name,
            sample_size=args.sample_size,
        )
        report["stats"] = stats

        # 打印关键指标
        basic = stats["basic"]
        init = stats["initiative"]
        print(
            f"  ✅ 总消息 {basic['total_messages']} 条 "
            f"({my_name} {basic['my_percentage']}% / {friend_name} {basic['friend_percentage']}%)"
        )
        print(
            f"  ✅ 聊天跨度 {basic['days_span']} 天，活跃 {basic['active_days']} 天 "
            f"(活跃率 {basic['active_rate']}%)"
        )
        print(
            f"  ✅ 主动发起: {my_name} {init['my_initiations']}次 / "
            f"{friend_name} {init['friend_initiations']}次"
        )

    # Step 3: 生成图表
    if run_all or "charts" in modules:
        print("\n🎨 [3/4] 生成可视化图表...")
        if report["stats"]:
            charts = generate_all_charts(
                report["stats"], args.output_dir, my_name, friend_name
            )
            report["charts"] = charts
            for name, path in charts.items():
                if not name.endswith("_error"):
                    print(f"  ✅ {name}: {path}")
                else:
                    print(f"  ⚠️  {name}: {path}")
        else:
            print("  ⚠️  跳过 (需要先运行 stats 模块)")

    # Step 4: 导出数据
    if run_all or "export" in modules:
        print("\n💾 [4/4] 导出聊天记录...")
        exports = export_all(
            chat_data["all_messages"], args.output_dir, my_name, friend_name
        )
        report["exports"] = exports
        for name, path in exports.items():
            if not name.endswith("_error"):
                print(f"  ✅ {name}: {path}")
            else:
                print(f"  ⚠️  {name}: {path}")

    # 保存完整 JSON 报告 (供 LLM 读取分析)
    report_path = os.path.join(args.output_dir, "analysis_report.json")

    # 序列化时需要处理不可序列化的对象
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)

    elapsed = time.time() - start_time

    print(f"\n{'=' * 60}")
    print(f"  ✅ 分析完成! 耗时 {elapsed:.1f} 秒")
    print(f"  📁 输出目录: {os.path.abspath(args.output_dir)}")
    print(f"  📋 完整报告: {report_path}")
    print(f"{'=' * 60}")

    # 输出给 LLM 的摘要 (打印到 stdout)
    print("\n\n===== LLM_ANALYSIS_DATA_START =====")
    # 只输出关键数据给 LLM (不含采样消息的完整内容以节省 token)
    llm_data = {
        "meta": report["meta"],
    }
    if report["stats"]:
        llm_data["basic_stats"] = report["stats"]["basic"]
        llm_data["milestones"] = report["stats"]["milestones"]
        llm_data["initiative"] = report["stats"]["initiative"]
        llm_data["reply_speed_summary"] = {
            "my_avg_reply_seconds": report["stats"]["reply_speed"]["my_reply"][
                "avg_seconds"
            ],
            "friend_avg_reply_seconds": report["stats"]["reply_speed"]["friend_reply"][
                "avg_seconds"
            ],
            "my_instant_rate": report["stats"]["reply_speed"]["my_reply"][
                "instant_reply"
            ]["percentage"],
            "friend_instant_rate": report["stats"]["reply_speed"]["friend_reply"][
                "instant_reply"
            ]["percentage"],
        }
        llm_data["time_highlights"] = {
            "peak_hour": report["stats"]["time_distribution"]["peak_hour"],
            "peak_weekday": report["stats"]["time_distribution"]["peak_weekday"],
        }
        llm_data["top_words_preview"] = {
            "my_top10": [
                w["word"] for w in report["stats"]["top_words"].get("my_words", [])[:10]
            ],
            "friend_top10": [
                w["word"]
                for w in report["stats"]["top_words"].get("friend_words", [])[:10]
            ],
        }
        llm_data["monthly_trend_summary"] = {
            "total_months": len(report["stats"]["monthly_trend"]),
            "peak_month": (
                max(report["stats"]["monthly_trend"], key=lambda m: m["total"])["month"]
                if report["stats"]["monthly_trend"]
                else None
            ),
        }
        llm_data["msg_type_dist"] = report["stats"].get("msg_type_dist", {})
        llm_data["sampled_conversations"] = report["stats"].get(
            "sampled_conversations", []
        )

    if report["charts"]:
        llm_data["chart_files"] = {
            k: v for k, v in report["charts"].items() if not k.endswith("_error")
        }
    if report["exports"]:
        llm_data["export_files"] = {
            k: v for k, v in report["exports"].items() if not k.endswith("_error")
        }

    print(json.dumps(llm_data, ensure_ascii=False, indent=2, default=str))
    print("===== LLM_ANALYSIS_DATA_END =====")


if __name__ == "__main__":
    main()
