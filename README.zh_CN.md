# LoL-RandomElement-Sequence

[Speak English? Click here to view the English introduction.](README.md)

本存储库主要负责对英雄联盟特殊模式中的随机元素进行**统计**，并形成**可供人类阅读的**结果。

## 特性
1. 定义了一个随机元素时间序列类，并提供了追加元素、撤回快照和清空元素等标准方法。
2. 支持读取和导出属性锻造器时间序列。
    1. （目前尚未启用）将属性锻造器选择行为<ins>序列</ins>导出为时间轴文本。
    2. 将属性锻造器计数器<ins>快照</ins>汇总复制到剪贴板中，以便后续粘贴到**Adobe Premiere Pro**软件中。
    3. （目前尚未启用）将属性锻造器计数器<ins>序列</ins>导出为一张表格。

## 环境配置
1. 前往[Python官网](https://www.python.org)，下载和安装最新版本的Python。
    - 图文示范可参考[模块：Python安装与全局环境配置](https://zhuanlan.zhihu.com/p/2038292227298996375)一文。
    - 安装前请确保“Add Python.exe to PATH”选项已勾选。
2. 在命令提示符中输入`pip install win32`以安装win32库。

## 使用方法
1. 仿照下面的示例录入属性锻造器时间序列数据，保存到一个文本文档或json文件中。
    - 时间轴文本：[属性锻造器时间序列-墨菲特.txt](example/v2/StatAnvilSequence-Malphite-zh_CN.txt)
    - 选择数据：[属性锻造器时间序列-墨菲特.json](example/v2/StatAnvilSequence-Malphite.json)
2. 在运行程序之前，请先在Adobe Premiere Pro程序中复制一个文本框中的一段文字。
3. 根据程序提示设置时间序列文件路径、游戏模式、起始序号和分辨率等参数。
4. 按下回车键以逐个复制计数器快照。将它们粘贴到一个PR文本框中，然后重复这个操作，直到复制完成所有的计数器。
