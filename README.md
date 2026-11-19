# LoL-RandomElement-Sequence

[中文用户？点击此处查看中文介绍。](README.zh_CN.md)

This repository is mainly used to **count** random elements in special modes of League of Legends and form **human-readable** results.

## Features
1. Define a `LoLRandomElementSequence` class and standard methods of appending elements, recalling snapshots and clearing elements.
2. Support reading and exporting stat anvil sequence.
    1. Export stat anvil selection behavior <ins>sequence</ins> as timeline text.
    2. Copy stat anvil counter <ins>snapshot</ins> into clipboard, for pasting into **Adobe Premiere Pro** software subsequently.
    3. Export stat anvil counter <ins>sequence</ins> as a table.

## Environment Setup
1. Visit [Python official website](https://www.python.org) to download and install the latest Python release.
    - Refer to [Template: Python Installation and Global Environment Setup](https://zhuanlan.zhihu.com/p/2038292227298996375) for demonstration with pictures.
    - Before installation, please make sure "Add Python.exe to PATH" option is checked.
2. Input `pip install win32` in Command Prompt to install win32 library.

## Action Overview
```text
Sequence operation
├── 0: Exit the program
├── -1: Settings
│   ├── 0: Return to the last layer
│   ├── 1: Switch random element type
│   ├── 2: Export-copy strategy
│   ├── 3: Name identification strategy
│   ├── 4: Name export strategy
│   ├── 5: Tier export strategy
│   └── 6: Input language and Output language
├── 1: Add selections
│   ├── 0: Return to the last layer
│   ├── 1: Line by line
│   └── 2: From file
├── 2: Revert selections
├── 3: Export selections
│   ├── 0: Return to the last layer
│   ├── 1: Selection behavior sequence -> Timeline text
│   ├── 2: Counter snapshot -> PR clipboard
│   └── 3: Counter sequence -> Table
├── 4: Reset selections
└── 5: Output current settings
```

## User Manual
The program provides very detailed hints help users understand how to use its features. Some additional notes are listed below.
### 3/2: Counter snapshot -> PR clipboard
1. Following this example, enter stat anvil sequence data and save it into a text file or a json file.
    - Timeline text: [Stat Anvil Sequence - Malphite.txt](example/v2/StatAnvilSequence-Malphite-en_US.txt)
    - Selection data: [Stat Anvil Sequence - Malphite.json](example/v2/StatAnvilSequence-Malphite.json)
2. Before you select this option, make sure you've copied some text in a textbox of Adobe Premiere Pro application.
3. Set parameters like game mode, start index and resolution according to the hints.
4. Press Enter to copy the anvil counter one by one. Paste them into a PR textbox. Repeat this step until all counters are copied.
