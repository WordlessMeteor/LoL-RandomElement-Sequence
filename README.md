# LoL-RandomElement-Sequence

[中文用户？点击此处查看中文介绍。](README.zh_CN.md)

This repository is mainly used to **count** random elements in special modes of League of Legends and form **human-readable** results.

## Features
1. Define a `LoLRandomElementSequence` class and standard methods of appending elements, recalling snapshots and clearing elements.
2. Support reading and exporting stat anvil sequence.
    1. (Currently disabled) Export stat anvil selection behavior <ins>sequence</ins> as timeline text.
    2. Copy stat anvil counter <ins>snapshot</ins> into clipboard, for pasting into **Adobe Premiere Pro** software subsequently.
    3. (Currently disabled) Export stat anvil counter <ins>sequence</ins> as a table.

## Environment Setup
1. Visit [Python official website](https://www.python.org) to download and install the latest Python release.
    - Refer to [Template: Python Installation and Global Environment Setup](https://zhuanlan.zhihu.com/p/2038292227298996375) for demonstration with pictures.
    - Before installation, please make sure "Add Python.exe to PATH" option is checked.
2. Input `pip install win32` in Command Prompt to install win32 library.

## User Manual
1. Following this example, enter stat anvil sequence data and save it into a text file or a json file.
    - Timeline text: [Stat Anvil Sequence - Malphite.txt](example/v2/StatAnvilSequence-Malphite-en_US.txt)
    - Selection data: [Stat Anvil Sequence - Malphite.json](example/v2/StatAnvilSequence-Malphite.json)
2. Before running the program, make sure you've copied some text in a text box of Adobe Premiere Pro application.
3. Set parameters like sequence file path, game mode, start index and resolution according to the hints.
4. Press Enter to copy the anvil counter one by one. Paste them into a PR textbox. Repeat this step until all counters are copied.
