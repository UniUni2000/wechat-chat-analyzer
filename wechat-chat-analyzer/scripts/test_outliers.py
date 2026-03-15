#!/usr/bin/env python3
"""
测试极端数据剔除功能
"""

import sys
import os

# 确保能找到同级模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from stats_engine import _remove_outliers

# 测试数据
normal_data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
outlier_data = [1, 2, 3, 4, 5, 100, 7, 8, 9, 10]  # 包含极端值 100
empty_data = []
single_data = [5]
identical_data = [5, 5, 5, 5, 5]  # 标准差为0

print("=== 测试极端数据剔除功能 ===")

# 测试正常数据
print("\n1. 测试正常数据:")
print(f"原始数据: {normal_data}")
filtered = _remove_outliers(normal_data)
print(f"过滤后: {filtered}")
print(f"是否相同: {normal_data == filtered}")

# 测试包含极端值的数据
print("\n2. 测试包含极端值的数据:")
print(f"原始数据: {outlier_data}")
filtered = _remove_outliers(outlier_data)  # 使用默认的IQR方法
print(f"过滤后: {filtered}")
print(f"是否移除了极端值: {100 not in filtered}")

# 测试使用sigma方法
print("\n6. 测试使用sigma方法:")
print(f"原始数据: {outlier_data}")
filtered_sigma = _remove_outliers(outlier_data, method='sigma', factor=3)
print(f"过滤后: {filtered_sigma}")
print(f"是否移除了极端值: {100 not in filtered_sigma}")

# 测试空数据
print("\n3. 测试空数据:")
print(f"原始数据: {empty_data}")
filtered = _remove_outliers(empty_data)
print(f"过滤后: {filtered}")
print(f"是否为空: {filtered == []}")

# 测试单元素数据
print("\n4. 测试单元素数据:")
print(f"原始数据: {single_data}")
filtered = _remove_outliers(single_data)
print(f"过滤后: {filtered}")
print(f"是否相同: {single_data == filtered}")

# 测试标准差为0的数据
print("\n5. 测试标准差为0的数据:")
print(f"原始数据: {identical_data}")
filtered = _remove_outliers(identical_data)
print(f"过滤后: {filtered}")
print(f"是否相同: {identical_data == filtered}")

print("\n=== 测试完成 ===")
