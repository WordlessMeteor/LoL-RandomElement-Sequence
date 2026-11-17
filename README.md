# LoL-RandomElement-Sequence

[中文用户？点击此处查看中文介绍。](README.zh_CN.md)

This repository is mainly used to **count** random elements in special modes of League of Legends and form **human-readable** results.

***Random Element Sequence Program is under development for now. This means users need programming skill to modify the code according to personal demand and achieve their intended goals.***

## Features
1. Define a `StatAnvilSequence` class and standard methods of appending elements, recalling snapshots and clearing elements.
2. Support copying stat anvil selection summary into clipboard, for pasting into **Adobe Premiere Pro** software.

## Environment Setup
1. Visit [Python official website](https://www.python.org) to download and install the latest Python release.
    - Refer to [Template: Python Installation and Global Environment Setup](https://zhuanlan.zhihu.com/p/2038292227298996375) for demonstration with pictures.
    - Before installation, please make sure "Add Python.exe to PATH" option is checked.
2. Input `pip install win32` in Command Prompt to install win32 library.

## User Manual
1. Following these two examples, enter stat anvil sequence data and save it into a json file.
    - [Stat Anvil Sequence - Master Yi](example/v1/StatAnvilSequence-MasterYi.json)
    - [Stat Anvil Sequence - Xin Zhao](example/v1/StatAnvilSequence-XinZhao.json)
2. Before running the program, make sure you've copied some text in a text box of Adobe Premiere Pro application.
3. Change the body of `StatAnvilSequence.export` method to control the output form of a stat anvil snapshot.
4. Change the body of `copy_stat_anvil_sequence_PR` function body to control the font and paragraph format.
    - This function's body is divided into several layers by comment.
    - For better understanding of each layer, a Jupyter notebook is provided in the release, which resolves the eight formats in the system clipboard when a text in PR text box is copied.
    - Users can write some text that uses the target format in PR, copy it into the clipboard, and then run "Export PR clipboard" code block in the Jupyter notebook to export clipboard information into json file. Compare this file with the function body and change the corresponding values.

## Video Demo
[Video Creation Process of Stat Anvil Tier Probability Test Series](https://youtu.be/pDSbs6z8oeQ)
