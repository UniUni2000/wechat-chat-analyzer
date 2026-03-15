"""
微信聊天可视化引擎
===================
功能: 基于统计数据生成美观的图表 (PNG格式)。
依赖: matplotlib, wordcloud

所有数据处理完全在本地完成，无任何网络请求。
"""

import os
import sys
import platform

# 尝试导入可视化依赖
try:
    import matplotlib
    matplotlib.use("Agg")  # 非交互式后端，适用于无GUI环境
    import matplotlib.pyplot as plt
    import matplotlib.ticker as ticker
    import numpy as np
    MPL_AVAILABLE = True
except ImportError:
    MPL_AVAILABLE = False

try:
    from wordcloud import WordCloud
    WC_AVAILABLE = True
except ImportError:
    WC_AVAILABLE = False


# ===================== 中文字体配置 =====================

def _find_chinese_font() -> str:
    """跨平台自动查找中文字体路径。"""
    system = platform.system()
    
    candidates = []
    if system == "Darwin":  # macOS
        candidates = [
            "/System/Library/Fonts/STHeiti Medium.ttc",
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/Hiragino Sans GB.ttc",
            "/Library/Fonts/Arial Unicode MS.ttf",
            "/System/Library/Fonts/STHeiti Light.ttc",
            "/System/Library/Fonts/Supplemental/Songti.ttc",
            "/System/Library/Fonts/Supplemental/STFangsong.ttf",
        ]
    elif system == "Windows":
        windir = os.environ.get("WINDIR", r"C:\Windows")
        fonts_dir = os.path.join(windir, "Fonts")
        candidates = [
            os.path.join(fonts_dir, "msyh.ttc"),      # 微软雅黑
            os.path.join(fonts_dir, "msyhbd.ttc"),     # 微软雅黑粗体
            os.path.join(fonts_dir, "simhei.ttf"),     # 黑体
            os.path.join(fonts_dir, "simsun.ttc"),     # 宋体
            os.path.join(fonts_dir, "simfang.ttf"),    # 仿宋
        ]
    else:  # Linux
        candidates = [
            "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        ]
    
    for path in candidates:
        if os.path.exists(path):
            return path
    
    return None


def _setup_matplotlib_chinese():
    """配置 matplotlib 中文显示。"""
    if not MPL_AVAILABLE:
        return
    
    font_path = _find_chinese_font()
    if font_path:
        from matplotlib import font_manager
        font_prop = font_manager.FontProperties(fname=font_path)
        plt.rcParams["font.family"] = font_prop.get_name()
        # 注册字体
        font_manager.fontManager.addfont(font_path)
        plt.rcParams["font.sans-serif"] = [font_prop.get_name()] + plt.rcParams.get("font.sans-serif", [])
    else:
        # 回退方案
        plt.rcParams["font.sans-serif"] = ["SimHei", "Heiti TC", "WenQuanYi Micro Hei", "sans-serif"]
    
    plt.rcParams["axes.unicode_minus"] = False


# ===================== 配色方案 =====================

# 温暖、现代的配色
COLORS = {
    "primary": "#FF6B6B",       # 珊瑚红
    "secondary": "#4ECDC4",     # 薄荷绿
    "accent": "#FFE66D",        # 暖黄
    "bg": "#2C3E50",            # 深蓝灰
    "text": "#ECF0F1",          # 浅灰白
    "my_color": "#4ECDC4",      # 我的颜色 (薄荷绿)
    "friend_color": "#FF6B6B",  # 对方颜色 (珊瑚红)
    "grid": "#34495E",          # 网格线
}

# 饼图/回复速度用的渐变色
SPEED_COLORS = ["#2ECC71", "#3498DB", "#F1C40F", "#E67E22", "#E74C3C"]


# ===================== 图表生成 =====================

def generate_all_charts(stats: dict, output_dir: str,
                        my_name: str, friend_name: str) -> dict:
    """生成所有图表，返回文件路径字典。"""
    if not MPL_AVAILABLE:
        return {"error": "matplotlib 未安装。请运行: pip install matplotlib"}
    
    _setup_matplotlib_chinese()
    os.makedirs(output_dir, exist_ok=True)
    
    results = {}
    
    # 1. 热力图
    try:
        path = _generate_heatmap(stats["time_distribution"], output_dir)
        results["heatmap"] = path
    except Exception as e:
        results["heatmap_error"] = str(e)
    
    # 2. 月度柱状图
    try:
        path = _generate_monthly_bar(stats["monthly_trend"], output_dir, my_name, friend_name)
        results["monthly_bar"] = path
    except Exception as e:
        results["monthly_bar_error"] = str(e)
    
    # 3. 回复时差饼图
    try:
        path = _generate_reply_pie(stats["reply_speed"], output_dir, my_name, friend_name)
        results["reply_pie"] = path
    except Exception as e:
        results["reply_pie_error"] = str(e)
    
    # 4. 词云
    try:
        paths = _generate_wordclouds(stats["top_words"], output_dir, my_name, friend_name)
        results.update(paths)
    except Exception as e:
        results["wordcloud_error"] = str(e)
    
    # 5. 每日消息趋势
    try:
        path = _generate_daily_trend(stats["monthly_trend"], output_dir, my_name, friend_name)
        results["daily_trend"] = path
    except Exception as e:
        results["daily_trend_error"] = str(e)
    
    return results


def _generate_heatmap(time_dist: dict, output_dir: str) -> str:
    """生成 7×24 聊天频率热力图。"""
    data = time_dist["heatmap"]  # 7x24 matrix
    weekday_names = time_dist["weekday_names"]
    
    fig, ax = plt.subplots(figsize=(14, 5))
    fig.patch.set_facecolor(COLORS["bg"])
    ax.set_facecolor(COLORS["bg"])
    
    arr = list(reversed(data))  # 周日在上
    names_reversed = list(reversed(weekday_names))
    
    im = ax.imshow(arr, cmap="YlOrRd", aspect="auto", interpolation="nearest")
    
    ax.set_xticks(range(24))
    ax.set_xticklabels([f"{h:02d}" for h in range(24)], fontsize=8, color=COLORS["text"])
    ax.set_yticks(range(7))
    ax.set_yticklabels(names_reversed, fontsize=10, color=COLORS["text"])
    
    ax.set_xlabel("时间 (小时)", fontsize=11, color=COLORS["text"])
    ax.set_title("聊天频率热力图", fontsize=14, color=COLORS["text"], pad=15, fontweight="bold")
    
    # 在每个格子中显示数字
    for i in range(7):
        for j in range(24):
            val = arr[i][j]
            if val > 0:
                text_color = "white" if val > max(max(row) for row in arr) * 0.5 else "black"
                ax.text(j, i, str(val), ha="center", va="center", fontsize=6, color=text_color)
    
    cbar = plt.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("消息数", color=COLORS["text"], fontsize=10)
    cbar.ax.yaxis.set_tick_params(color=COLORS["text"])
    plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color=COLORS["text"])
    
    plt.tight_layout()
    path = os.path.join(output_dir, "heatmap.png")
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=COLORS["bg"])
    plt.close()
    return path


def _generate_monthly_bar(monthly: list, output_dir: str,
                           my_name: str, friend_name: str) -> str:
    """生成月度消息量对比柱状图。"""
    if not monthly:
        return None
    
    months = [m["month"] for m in monthly]
    my_counts = [m["my_count"] for m in monthly]
    friend_counts = [m["friend_count"] for m in monthly]
    
    fig, ax = plt.subplots(figsize=(max(10, len(months) * 0.6), 6))
    fig.patch.set_facecolor(COLORS["bg"])
    ax.set_facecolor(COLORS["bg"])
    
    x = range(len(months))
    width = 0.35
    
    bars1 = ax.bar([i - width/2 for i in x], my_counts, width,
                   label=my_name, color=COLORS["my_color"], alpha=0.85, edgecolor="none")
    bars2 = ax.bar([i + width/2 for i in x], friend_counts, width,
                   label=friend_name, color=COLORS["friend_color"], alpha=0.85, edgecolor="none")
    
    ax.set_xticks(list(x))
    ax.set_xticklabels(months, rotation=45, ha="right", fontsize=8, color=COLORS["text"])
    ax.set_ylabel("消息数", fontsize=11, color=COLORS["text"])
    ax.set_title("月度消息量对比", fontsize=14, color=COLORS["text"], pad=15, fontweight="bold")
    ax.tick_params(colors=COLORS["text"])
    ax.spines["bottom"].set_color(COLORS["grid"])
    ax.spines["left"].set_color(COLORS["grid"])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    
    legend = ax.legend(fontsize=10, facecolor=COLORS["bg"], edgecolor=COLORS["grid"])
    for text in legend.get_texts():
        text.set_color(COLORS["text"])
    
    plt.tight_layout()
    path = os.path.join(output_dir, "monthly_bar.png")
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=COLORS["bg"])
    plt.close()
    return path


def _generate_reply_pie(reply_speed: dict, output_dir: str,
                         my_name: str, friend_name: str) -> str:
    """生成回复时差分布双饼图。"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    fig.patch.set_facecolor(COLORS["bg"])
    
    tier_keys = ["instant_reply", "quick_reply", "normal_reply", "slow_reply", "very_slow_reply"]
    labels = ["秒回\n≤30s", "快速\n≤5min", "正常\n≤30min", "佛系\n≤2h", "意念\n>2h"]
    
    for ax, data_key, title in [
        (ax1, "my_reply", f"{my_name}的回复速度"),
        (ax2, "friend_reply", f"{friend_name}的回复速度"),
    ]:
        ax.set_facecolor(COLORS["bg"])
        data = reply_speed[data_key]
        values = [data[k]["count"] for k in tier_keys]
        
        if sum(values) == 0:
            ax.text(0.5, 0.5, "暂无数据", ha="center", va="center",
                    fontsize=14, color=COLORS["text"], transform=ax.transAxes)
            ax.set_title(title, fontsize=13, color=COLORS["text"], fontweight="bold")
            continue
        
        # 过滤掉0值
        filtered = [(l, v, c) for l, v, c in zip(labels, values, SPEED_COLORS) if v > 0]
        f_labels, f_values, f_colors = zip(*filtered) if filtered else ([], [], [])
        
        wedges, texts, autotexts = ax.pie(
            f_values, labels=f_labels, colors=f_colors,
            autopct="%1.1f%%", startangle=90, pctdistance=0.75,
            textprops={"fontsize": 9, "color": COLORS["text"]},
        )
        for t in autotexts:
            t.set_fontsize(8)
            t.set_color("white")
            t.set_fontweight("bold")
        
        avg_s = data["avg_seconds"]
        if avg_s < 60:
            avg_text = f"平均: {avg_s:.0f}秒"
        elif avg_s < 3600:
            avg_text = f"平均: {avg_s/60:.1f}分钟"
        else:
            avg_text = f"平均: {avg_s/3600:.1f}小时"
        
        ax.set_title(f"{title}\n{avg_text}", fontsize=12, color=COLORS["text"], fontweight="bold")
    
    plt.tight_layout()
    path = os.path.join(output_dir, "reply_speed.png")
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=COLORS["bg"])
    plt.close()
    return path


def _generate_wordclouds(top_words: dict, output_dir: str,
                          my_name: str, friend_name: str) -> dict:
    """生成双方词云图。"""
    if not WC_AVAILABLE:
        return {"wordcloud_error": "wordcloud 未安装。请运行: pip install wordcloud"}
    
    font_path = _find_chinese_font()
    results = {}
    
    for key, name, color_map in [
        ("my_words", my_name, "winter"),
        ("friend_words", friend_name, "autumn"),
    ]:
        words = top_words.get(key, [])
        if not words:
            continue
        
        freq = {item["word"]: item["count"] for item in words}
        
        wc = WordCloud(
            font_path=font_path,
            width=800,
            height=400,
            background_color=COLORS["bg"],
            colormap=color_map,
            max_words=80,
            max_font_size=120,
            min_font_size=10,
            prefer_horizontal=0.7,
            margin=10,
        )
        wc.generate_from_frequencies(freq)
        
        filename = f"wordcloud_{key.replace('_words', '')}.png"
        path = os.path.join(output_dir, filename)
        wc.to_file(path)
        results[f"wordcloud_{key.replace('_words', '')}"] = path
    
    return results


def _generate_daily_trend(monthly: list, output_dir: str,
                           my_name: str, friend_name: str) -> str:
    """月度消息量趋势折线图。"""
    if not monthly:
        return None
    
    months = [m["month"] for m in monthly]
    totals = [m["total"] for m in monthly]
    
    fig, ax = plt.subplots(figsize=(max(10, len(months) * 0.5), 5))
    fig.patch.set_facecolor(COLORS["bg"])
    ax.set_facecolor(COLORS["bg"])
    
    ax.fill_between(range(len(months)), totals, alpha=0.3, color=COLORS["primary"])
    ax.plot(range(len(months)), totals, color=COLORS["primary"], linewidth=2, marker="o", markersize=4)
    
    ax.set_xticks(range(len(months)))
    ax.set_xticklabels(months, rotation=45, ha="right", fontsize=8, color=COLORS["text"])
    ax.set_ylabel("消息数", fontsize=11, color=COLORS["text"])
    ax.set_title("消息量趋势", fontsize=14, color=COLORS["text"], pad=15, fontweight="bold")
    ax.tick_params(colors=COLORS["text"])
    ax.spines["bottom"].set_color(COLORS["grid"])
    ax.spines["left"].set_color(COLORS["grid"])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color=COLORS["grid"], alpha=0.3)
    
    plt.tight_layout()
    path = os.path.join(output_dir, "trend.png")
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=COLORS["bg"])
    plt.close()
    return path


if __name__ == "__main__":
    print("请通过 wechat_analyzer.py 主入口运行。")
