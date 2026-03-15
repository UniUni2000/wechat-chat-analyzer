"""
微信聊天统计引擎
=================
功能: 基于聊天记录计算所有精准统计指标。
输出 JSON 格式的结构化数据，供 LLM 深度解读 & 图表生成。

所有计算完全在本地完成，无任何网络请求。
"""

import re
import random
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta

# 尝试导入 jieba，缺失时给出提示
try:
    import jieba
    JIEBA_AVAILABLE = True
except ImportError:
    JIEBA_AVAILABLE = False

CN_TZ = timezone(timedelta(hours=8))


def _remove_outliers(data, method='iqr', factor=1.5):
    """剔除极端数据。
    
    参数:
      data: 数值列表
      method: 方法，'iqr'（四分位距）或 'sigma'（标准差）
      factor: 倍数，默认1.5（IQR方法）或3（sigma方法）
    
    返回:
      剔除极端数据后的列表
    """
    if not data:
        return []
    
    if method == 'sigma':
        # 使用3σ方法
        mean = sum(data) / len(data)
        variance = sum((x - mean) ** 2 for x in data) / len(data)
        std_dev = math.sqrt(variance)
        
        if std_dev == 0:
            return data
        
        lower_bound = mean - factor * std_dev
        upper_bound = mean + factor * std_dev
    else:
        # 使用IQR方法（默认）
        sorted_data = sorted(data)
        n = len(sorted_data)
        q1 = sorted_data[n//4]
        q3 = sorted_data[3*n//4]
        iqr = q3 - q1
        
        lower_bound = q1 - factor * iqr
        upper_bound = q3 + factor * iqr
    
    filtered_data = [x for x in data if lower_bound <= x <= upper_bound]
    # 如果过滤后的数据为空，返回原始数据
    return filtered_data if filtered_data else data

# ===================== 停用词 =====================
# 内置基础停用词列表，涵盖中文常见虚词、标点
STOP_WORDS = set("""
的 了 在 是 我 有 和 就 不 人 都 一 一个 上 也 很 到 说 要 去 你 会 着
可以 这 那 他 她 它 们 吗 呢 吧 啊 哦 嗯 哈 呀 哎 哇 喔 唉 嘿 嗨
好 好的 嗯嗯 哈哈 哈哈哈 嘻嘻 呵呵 对 是的 没 没有 不是 什么 怎么
这个 那个 还是 但是 因为 所以 如果 虽然 可是 而且 或者 以及
只是 而已 就是 已经 正在 曾经 将要 可能 应该 必须 需要
我们 他们 自己 大家 什么 为什么 哪里 多少 怎样 何时
把 被 让 给 从 向 往 比 跟 像 对于 关于 通过 之后 之前
其实 当然 然后 接着 最后 首先 另外 而且 不过 只要 除了
这样 那样 怎样 如何 为何 此外 总之 因此 于是 所以
图片 表情 语音 视频 链接
the a an is are was were be been being have has had do does did
will would shall should may might can could of to in for on with
at by from as into through during before after above below between
and but or nor not no so yet both either neither each every all any
i me my we us our you your he him his she her it its they them their
this that these those here there where when how what which who whom
am is are was were be been being have has had do does did will would
""".split())


def compute_all_stats(all_messages: list, text_messages: list,
                      my_name: str, friend_name: str,
                      sample_size: int = 50) -> dict:
    """计算全部统计指标，返回完整 JSON 报告。
    
    参数:
      all_messages: 所有类型消息列表
      text_messages: 纯文本消息列表
      my_name: 自己的显示名
      friend_name: 好友的显示名
      sample_size: 采样对话条数
    """
    stats = {}
    
    # 基础统计
    stats["basic"] = _basic_stats(all_messages, text_messages, my_name, friend_name)
    
    # 里程碑时刻
    stats["milestones"] = _milestones(all_messages)
    
    # 主动性分析
    stats["initiative"] = _initiative_analysis(all_messages, my_name)
    
    # 回复时差分析
    stats["reply_speed"] = _reply_speed_analysis(text_messages, my_name, friend_name)
    
    # 时间分布
    stats["time_distribution"] = _time_distribution(all_messages, my_name, friend_name)
    
    # 高频词统计
    stats["top_words"] = _top_words(text_messages, my_name, friend_name)
    
    # 月度趋势
    stats["monthly_trend"] = _monthly_trend(all_messages, my_name, friend_name)
    
    # 采样代表性对话 (供 LLM 深度分析)
    stats["sampled_conversations"] = _sample_conversations(text_messages, sample_size)
    
    # 消息类型分布
    stats["msg_type_dist"] = _msg_type_distribution(all_messages)
    
    return stats


# ===================== 基础统计 =====================

def _basic_stats(all_msgs, text_msgs, my_name, friend_name) -> dict:
    """基础计数与占比。"""
    total = len(all_msgs)
    text_total = len(text_msgs)
    
    my_all = sum(1 for m in all_msgs if m["is_me"])
    friend_all = total - my_all
    my_text = sum(1 for m in text_msgs if m["is_me"])
    friend_text = text_total - my_text
    
    # 聊天天数
    if all_msgs:
        first_ts = all_msgs[0]["timestamp"]
        last_ts = all_msgs[-1]["timestamp"]
        days_span = max(1, (last_ts - first_ts) // 86400 + 1)
        active_days = len(set(
            datetime.fromtimestamp(m["timestamp"], tz=CN_TZ).strftime("%Y-%m-%d")
            for m in all_msgs
        ))
    else:
        days_span = 0
        active_days = 0
    
    # 平均消息长度 (文本)
    my_texts = [m["content"] for m in text_msgs if m["is_me"] and m["content"]]
    friend_texts = [m["content"] for m in text_msgs if not m["is_me"] and m["content"]]
    
    # 计算消息长度并剔除极端数据
    my_lengths = [len(t) for t in my_texts]
    friend_lengths = [len(t) for t in friend_texts]
    
    filtered_my_lengths = _remove_outliers(my_lengths, method='iqr', factor=1.5)  # 使用IQR方法
    filtered_friend_lengths = _remove_outliers(friend_lengths, method='iqr', factor=1.5)  # 使用IQR方法
    
    my_avg_len = round(sum(filtered_my_lengths) / max(1, len(filtered_my_lengths)), 1) if filtered_my_lengths else 0
    friend_avg_len = round(sum(filtered_friend_lengths) / max(1, len(filtered_friend_lengths)), 1) if filtered_friend_lengths else 0
    
    return {
        "total_messages": total,
        "text_messages": text_total,
        "my_messages": my_all,
        "friend_messages": friend_all,
        "my_text_messages": my_text,
        "friend_text_messages": friend_text,
        "my_percentage": round(my_all / max(1, total) * 100, 1),
        "friend_percentage": round(friend_all / max(1, total) * 100, 1),
        "days_span": days_span,
        "active_days": active_days,
        "active_rate": round(active_days / max(1, days_span) * 100, 1),
        "avg_msgs_per_active_day": round(total / max(1, active_days), 1),
        "my_avg_text_length": my_avg_len,
        "friend_avg_text_length": friend_avg_len,
    }


# ===================== 里程碑时刻 =====================

def _milestones(all_msgs) -> dict:
    """关键时刻记录。"""
    if not all_msgs:
        return {}
    
    first = all_msgs[0]
    last = all_msgs[-1]
    
    # 最晚聊天 (一天中最晚的消息)
    latest_msg = max(all_msgs, key=lambda m: m["hour"] * 60 + 
                     datetime.fromtimestamp(m["timestamp"], tz=CN_TZ).minute)
    
    # 最早聊天 (排除凌晨 0-5 点的夜猫子消息)
    morning_msgs = [m for m in all_msgs if 5 <= m["hour"] <= 12]
    earliest_msg = min(morning_msgs, key=lambda m: m["hour"] * 60 + 
                       datetime.fromtimestamp(m["timestamp"], tz=CN_TZ).minute) if morning_msgs else None
    
    # 单日最多消息
    day_counts = Counter(
        datetime.fromtimestamp(m["timestamp"], tz=CN_TZ).strftime("%Y-%m-%d")
        for m in all_msgs
    )
    busiest_day, busiest_count = day_counts.most_common(1)[0] if day_counts else ("", 0)
    
    result = {
        "first_chat_time": first["time"],
        "first_chat_sender": first["sender"],
        "first_chat_content": first["content"][:100] if first["msg_type"] == "text" else f"[{first['msg_type']}]",
        "last_chat_time": last["time"],
        "latest_night_time": datetime.fromtimestamp(latest_msg["timestamp"], tz=CN_TZ).strftime("%H:%M"),
        "latest_night_date": datetime.fromtimestamp(latest_msg["timestamp"], tz=CN_TZ).strftime("%Y-%m-%d"),
        "busiest_day": busiest_day,
        "busiest_day_count": busiest_count,
    }
    
    if earliest_msg:
        result["earliest_morning_time"] = datetime.fromtimestamp(
            earliest_msg["timestamp"], tz=CN_TZ
        ).strftime("%H:%M")
        result["earliest_morning_date"] = datetime.fromtimestamp(
            earliest_msg["timestamp"], tz=CN_TZ
        ).strftime("%Y-%m-%d")
    
    return result


# ===================== 主动性分析 =====================

def _initiative_analysis(all_msgs, my_name, gap_threshold=300) -> dict:
    """分析谁更主动发起聊天。
    
    规则: 若与前一条消息时间间隔 > gap_threshold(默认5分钟/300秒),
    则该消息视为"发起聊天"。
    """
    if len(all_msgs) < 2:
        return {"my_initiations": 0, "friend_initiations": 0}
    
    my_init = 0
    friend_init = 0
    
    # 第一条消息算发起
    if all_msgs[0]["is_me"]:
        my_init += 1
    else:
        friend_init += 1
    
    for i in range(1, len(all_msgs)):
        gap = all_msgs[i]["timestamp"] - all_msgs[i-1]["timestamp"]
        if gap >= gap_threshold:
            if all_msgs[i]["is_me"]:
                my_init += 1
            else:
                friend_init += 1
    
    total_init = my_init + friend_init
    return {
        "my_initiations": my_init,
        "friend_initiations": friend_init,
        "total_conversations": total_init,
        "my_initiative_rate": round(my_init / max(1, total_init) * 100, 1),
        "friend_initiative_rate": round(friend_init / max(1, total_init) * 100, 1),
    }


# ===================== 回复时差分析 =====================

def _reply_speed_analysis(text_msgs, my_name, friend_name) -> dict:
    """计算双方回复速度分布。"""
    # 分类阈值 (秒)
    TIERS = [
        ("instant_reply", "秒回 (≤30s)", 30),
        ("quick_reply", "快速回复 (≤5min)", 300),
        ("normal_reply", "正常回复 (≤30min)", 1800),
        ("slow_reply", "佛系回复 (≤2h)", 7200),
        ("very_slow_reply", "意念回复 (>2h)", float("inf")),
    ]
    
    my_reply_times = []
    friend_reply_times = []
    
    for i in range(1, len(text_msgs)):
        curr = text_msgs[i]
        prev = text_msgs[i-1]
        
        # 只统计不同发送方之间的回复时差
        if curr["is_me"] != prev["is_me"]:
            gap = curr["timestamp"] - prev["timestamp"]
            if gap > 0 and gap < 86400:  # 排除超过24小时的(不算回复)
                if curr["is_me"]:
                    my_reply_times.append(gap)
                else:
                    friend_reply_times.append(gap)
    
    def _classify(times):
        dist = {key: 0 for key, _, _ in TIERS}
        for t in times:
            for key, _, threshold in TIERS:
                if t <= threshold:
                    dist[key] += 1
                    break
        total = len(times)
        result = {}
        for key, label, _ in TIERS:
            count = dist[key]
            result[key] = {
                "label": label,
                "count": count,
                "percentage": round(count / max(1, total) * 100, 1),
            }
        # 剔除极端数据后计算平均回复时长
        filtered_times = _remove_outliers(times, method='iqr', factor=1.5)  # 使用IQR方法
        result["avg_seconds"] = round(sum(filtered_times) / max(1, len(filtered_times)), 1) if filtered_times else 0
        result["median_seconds"] = round(sorted(times)[len(times)//2], 1) if times else 0
        result["total_replies"] = total
        result["filtered_replies"] = len(filtered_times)
        return result
    
    return {
        "my_reply": _classify(my_reply_times),
        "friend_reply": _classify(friend_reply_times),
    }


# ===================== 时间分布 =====================

def _time_distribution(all_msgs, my_name, friend_name) -> dict:
    """按小时和星期统计消息分布。"""
    # 7x24 热力矩阵 (weekday x hour)
    heatmap = [[0]*24 for _ in range(7)]
    hourly = [0]*24
    weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    
    for m in all_msgs:
        heatmap[m["weekday"]][m["hour"]] += 1
        hourly[m["hour"]] += 1
    
    # 找到最活跃时段
    peak_hour = max(range(24), key=lambda h: hourly[h])
    peak_weekday = max(range(7), key=lambda w: sum(heatmap[w]))
    
    return {
        "heatmap": heatmap,
        "weekday_names": weekday_names,
        "hourly_total": hourly,
        "peak_hour": peak_hour,
        "peak_hour_count": hourly[peak_hour],
        "peak_weekday": weekday_names[peak_weekday],
        "peak_weekday_count": sum(heatmap[peak_weekday]),
    }


# ===================== 高频词统计 =====================

def _top_words(text_msgs, my_name, friend_name, top_n=50) -> dict:
    """分别统计双方高频词。"""
    if not JIEBA_AVAILABLE:
        return {
            "my_words": [],
            "friend_words": [],
            "error": "jieba 未安装，无法进行分词。请运行: pip install jieba",
        }
    
    my_texts = " ".join(m["content"] for m in text_msgs if m["is_me"] and m["content"])
    friend_texts = " ".join(m["content"] for m in text_msgs if not m["is_me"] and m["content"])
    
    def _count_words(text):
        words = jieba.lcut(text)
        # 过滤: 长度>=2, 非纯数字, 非停用词
        filtered = [
            w for w in words
            if len(w) >= 2 and not w.isdigit() and w.lower() not in STOP_WORDS
            and not re.match(r'^[\s\d\W]+$', w)
        ]
        return Counter(filtered).most_common(top_n)
    
    return {
        "my_words": [{"word": w, "count": c} for w, c in _count_words(my_texts)],
        "friend_words": [{"word": w, "count": c} for w, c in _count_words(friend_texts)],
    }


# ===================== 月度趋势 =====================

def _monthly_trend(all_msgs, my_name, friend_name) -> list:
    """按月统计双方消息量。"""
    monthly = defaultdict(lambda: {"my": 0, "friend": 0, "total": 0})
    
    for m in all_msgs:
        month_key = m["time"][:7]  # "YYYY-MM"
        monthly[month_key]["total"] += 1
        if m["is_me"]:
            monthly[month_key]["my"] += 1
        else:
            monthly[month_key]["friend"] += 1
    
    return [
        {"month": k, "my_count": v["my"], "friend_count": v["friend"], "total": v["total"]}
        for k, v in sorted(monthly.items())
    ]


# ===================== 采样对话 =====================

def _sample_conversations(text_msgs, sample_size=50) -> list:
    """智能采样代表性对话片段，供 LLM 做深度分析。
    
    策略: 从不同时间段均匀采样 + 选取高互动密度的对话片段。
    """
    if not text_msgs:
        return []
    
    if len(text_msgs) <= sample_size:
        return [{"time": m["time"], "sender": m["sender"], "content": m["content"]}
                for m in text_msgs]
    
    # 策略1: 均匀时间采样 (60%)
    uniform_count = int(sample_size * 0.6)
    step = len(text_msgs) // uniform_count
    uniform_samples = [text_msgs[i * step] for i in range(uniform_count)]
    
    # 策略2: 高密度互动片段 (40%) — 选取连续快速回复的对话
    remaining = sample_size - uniform_count
    dense_segments = []
    for i in range(1, len(text_msgs)):
        gap = text_msgs[i]["timestamp"] - text_msgs[i-1]["timestamp"]
        if gap < 120 and text_msgs[i]["is_me"] != text_msgs[i-1]["is_me"]:  # 2分钟内一来一回
            dense_segments.append(i)
    
    # 从高密度位置附近抽取
    if dense_segments:
        selected_indices = random.sample(dense_segments, min(remaining, len(dense_segments)))
        # 每个点取前后各1条，形成小片段
        dense_samples = []
        for idx in selected_indices:
            for offset in range(-1, 2):
                ni = idx + offset
                if 0 <= ni < len(text_msgs):
                    dense_samples.append(text_msgs[ni])
        # 去重
        seen_ts = {m["timestamp"] for m in uniform_samples}
        dense_samples = [m for m in dense_samples if m["timestamp"] not in seen_ts]
        dense_samples = dense_samples[:remaining]
    else:
        dense_samples = random.sample(text_msgs, min(remaining, len(text_msgs)))
    
    all_samples = uniform_samples + dense_samples
    all_samples.sort(key=lambda m: m["timestamp"])
    
    return [{"time": m["time"], "sender": m["sender"], "content": m["content"]}
            for m in all_samples]


# ===================== 消息类型分布 =====================

def _msg_type_distribution(all_msgs) -> dict:
    """统计各消息类型的数量分布。"""
    type_labels = {
        "text": "文本", "image": "图片", "voice": "语音", "emoji": "表情",
        "video": "视频", "link": "链接/文件", "call": "通话",
        "location": "位置", "card": "名片", "system": "系统消息",
        "recall": "撤回",
    }
    
    counter = Counter(m["msg_type"] for m in all_msgs)
    return {
        msg_type: {
            "label": type_labels.get(msg_type, msg_type),
            "count": count,
        }
        for msg_type, count in counter.most_common()
    }


if __name__ == "__main__":
    # 测试: 需配合 data_loader 使用
    print("请通过 wechat_analyzer.py 主入口运行，或通过 data_loader.py 加载数据后调用 compute_all_stats()")
