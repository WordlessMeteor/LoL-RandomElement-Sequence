# LoL-RandomElement-Sequence

[Speak English? Click here to view the English introduction.](README.md)

本存储库主要负责对英雄联盟特殊模式中的随机元素进行**统计**，并形成**可供人类阅读的**结果。

***随机元素序列脚本目前仍处于开发阶段。这意味着，用户需要具备一定编程能力，能够根据自身需求修改代码，从而实现自己的目的。***

## 特性
1. 定义了一个属性锻造器时间序列类，并提供了追加元素、撤回快照和清空元素等标准方法。
2. 支持将在特定时刻的属性锻造器选取情况汇总复制到剪贴板中，以便粘贴到**Adobe Premiere Pro**软件中。

## 环境配置
1. 前往[Python官网](https://www.python.org)，下载和安装最新版本的Python。
    - 图文示范可参考[模块：Python安装与全局环境配置](https://zhuanlan.zhihu.com/p/2038292227298996375)一文。
    - 安装前请确保“Add Python.exe to PATH”选项已勾选。
2. 在命令提示符中输入`pip install win32`以安装win32库。

## 使用方法
1. 仿照下面两个示例录入属性锻造器时间序列数据，保存到一个json文件中。
    - [属性锻造器时间序列-剑圣.json](example/v1/StatAnvilSequence-MasterYi.json)
    - [属性锻造器时间序列-赵信.json](example/v1/StatAnvilSequence-XinZhao.json)
2. 在运行程序之前，请先在Adobe Premiere Pro程序中复制一个文本框中的一段文字。
3. 修改`StatAnvilSequence.export`方法主体，控制属性锻造器快照的输出形式。
4. 修改`copy_stat_anvil_sequence_PR`函数主体，控制文本和段落格式。
    - 该函数主体通过注释来划分层次。
    - 为了方便理解各个层次，发行版中提供了一个Jupyter笔记本，解析了复制PR文本框中的文本时系统剪贴板中的八种格式。
    - 用户可以先在PR软件中撰写一段符合目标格式的文本，然后复制到剪贴板，再运行Jupyter笔记本的“导出PR剪贴板信息”代码块将剪贴板信息导出为Json文件，将该文件与函数主体进行比对，修改对应值。

## 视频示范
[属性锻造器位阶概率测试系列视频制作过程](https://youtu.be/pDSbs6z8oeQ)
