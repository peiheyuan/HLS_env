# HLS-env

## 项目简介

HLS-env 是一个用于评估 Xilinx HLS (High-Level Synthesis) 代码性能和资源消耗的 Python 工具。该工具可以自动化 HLS 代码的综合过程，并提取关键性能指标，帮助开发者快速评估 FPGA 实现效果。

## 前提条件

- 已安装 Xilinx Vivado HLS 2018.3
- Python 3.x

## 功能特点

- 自动查找 Vivado HLS 安装路径
- 生成 HLS 项目和 TCL 脚本
- 执行 HLS 综合流程
- 解析综合报告，提取关键性能指标：
- 时序信息（Timing）
- 延迟信息（Latency）
- 资源利用率（Resource Utilization）

## 使用方法

from hls_script import hls_evaluation
