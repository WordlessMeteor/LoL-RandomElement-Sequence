import copy, json, os, re, time, win32clipboard
from typing import Any, Callable, Literal, NotRequired, Optional, TypedDict
from pywintypes import HANDLEType

#第一部分：PR剪贴板仿真模拟（Part 1: PR clipboard simulation）
STANDARD_FORMATS: dict[int, str] = {
    win32clipboard.CF_BITMAP: "CF_BITMAP",
    win32clipboard.CF_DIB: "CF_DIB",
    win32clipboard.CF_DIBV5: "CF_DIBV5",
    win32clipboard.CF_DIF: "CF_DIF",
    win32clipboard.CF_DSPBITMAP: "CF_DSPBITMAP",
    win32clipboard.CF_DSPENHMETAFILE: "CF_DSPENHMETAFILE",
    win32clipboard.CF_DSPMETAFILEPICT: "CF_DSPMETAFILEPICT",
    win32clipboard.CF_DSPTEXT: "CF_DSPTEXT",
    win32clipboard.CF_ENHMETAFILE: "CF_ENHMETAFILE",
    win32clipboard.CF_HDROP: "CF_HDROP",
    win32clipboard.CF_LOCALE: "CF_LOCALE",
    win32clipboard.CF_MAX: "CF_MAX",
    win32clipboard.CF_METAFILEPICT: "CF_METAFILEPICT",
    win32clipboard.CF_OEMTEXT: "CF_OEMTEXT",
    win32clipboard.CF_OWNERDISPLAY: "CF_OWNERDISPLAY",
    win32clipboard.CF_PALETTE: "CF_PALETTE",
    win32clipboard.CF_PENDATA: "CF_PENDATA",
    win32clipboard.CF_RIFF: "CF_RIFF",
    win32clipboard.CF_SYLK: "CF_SYLK",
    win32clipboard.CF_TEXT: "CF_TEXT",
    win32clipboard.CF_TIFF: "CF_TIFF",
    win32clipboard.CF_UNICODETEXT: "CF_UNICODETEXT",
    win32clipboard.CF_WAVE: "CF_WAVE"
} #为每个预定义的格式编号指定一个名称（Specify each pre-defined format id with a name）
REQUIRED_CLIPBOARD_FORMATS_PR: list[str] = ["DataObject", "CF_UNICODETEXT", "Photoshop Text", "Adobe Text Engine 2.0", "Ole Private Data", "CF_LOCALE", "CF_TEXT", "CF_OEMTEXT"] #Premiere Pro软件的文本框涉及到的剪贴板格式（Clipboard formats involved in a text box of Premiere Pro software）

def get_clipboard_formats(hWnd: Optional[HANDLEType] = None) -> dict[str, int]:
    '''
    获取当前剪贴板中的所有格式编号及其名称。<br>Get all available formats' ids and names in the current clipboard.
    
    :param hWnd: 窗口句柄。如果未指定，则使用当前活动的剪贴板窗口。<br>A handle to the window. If not specified, the currently active clipboard window will be used.
    :type hWnd: pywintypes.HANDLEType
    :return: 格式字典。键是名称，值是编号。<br>A format dictionary, where each key is a name and each value is an id.
    :rtype: dict[int, str]
    '''
    win32clipboard.OpenClipboard(hWnd)
    formats: dict[int, str] = {}
    current_formatId: int = 0
    while True:
        next_formatId: int = win32clipboard.EnumClipboardFormats(current_formatId)
        if next_formatId == 0:
            break
        elif next_formatId in STANDARD_FORMATS:
            next_formatName: str = STANDARD_FORMATS[next_formatId]
        else:
            try:
                next_formatName = win32clipboard.GetClipboardFormatName(next_formatId)
            except:
                next_formatName = str(next_formatId)        
        formats[next_formatName] = next_formatId
        current_formatId = next_formatId
    win32clipboard.CloseClipboard()
    return formats

#解析PR文本框剪贴板（Resolve PR textbox clipboard）
def traverse_PRClipboard_Photoshop_Text(source: bytes, data: Any, indent_level: int = 0) -> bytes:
    '''
    遍历一段由格式名称为“Photoshop Text”的PR剪贴板转化而成的Python字典，将各键和值通过递归的形式追加到一个字符串中。<br>Traverse a Python dictionary converted from a PR clipboard with format name "Photoshop Text", and append all keys and values into a byte string recursively.
    
    :param source: 原始字节字符串。作为参数的同时也作为返回值。<br>The original byte string. It acts as both the parameter and the returned value.
    :type source: bytes
    :param data: 遍历PR剪贴板字典过程中的部分数据。<br>A part of PR clipboard dictionary data.
    :type data: Any
    :param indent_level: 缩进层数。默认为0。<br>Recursive layer. 0 by default.
    
        注意，Premiere Pro的文本框的剪贴板数据缩进写法和json数据的标准缩进写法有所不同，其缩进层数不能按照常规json的缩进来看待。因此`indent_level`不等于函数调用参数。<br>Note that the indentation of a piece of PR textbox clipboard data are somehow different from that of a piece pf json data, so the indentation can't directly inherit from that json's. Therefore, `indent_level` isn't equal to the function call level.
    :type indent_level: int
    '''
    if isinstance(data, dict):
        source += b"\n" + b"\t" * indent_level
        source += b"<<"
        indent_level += 1
        for (key, value) in data.items():
            source += b"\n" + b"\t" * indent_level
            source += b"/" + key.encode()
            source = traverse_PRClipboard_Photoshop_Text(source, value, indent_level = indent_level)
        indent_level -= 1
        source += b"\n" + b"\t" * indent_level
        source += b">>"
    elif isinstance(data, list):
        if len(data) == 0:
            source += b" [ ]"
        else:
            if all(map(lambda x: isinstance(x, (int | float)), data)):
                data_transform: list[str] = list(map(lambda x: "0.0" if x == 0 else str(x).replace("0.", ".") if x > -1 and x < 1 else str(x), data))
                source += (" [ " + " ".join(data_transform) + " ]").encode() #在使用默认编码的情况下，字节字符串和字面字符串的形式一定是相同（Using the default encoding, the form of the literal string must be the same as the byte string）
            else:
                source += b" ["
                #indent_level += 1 #根据实际测试下来，方括号不会更改制表位个数（According to practice, square bracket doesn't change the number of tabs）
                for elem in data:
                    source = traverse_PRClipboard_Photoshop_Text(source, elem, indent_level = indent_level)
                #indent_level -= 1
                source += b"\n" + b"\t" * indent_level
                source += b"]"
    else:
        source += b" "
        if isinstance(data, bytes):
            source += b"(%s)" %data
        elif isinstance(data, str):
            source += b"/" + data.encode()
        elif isinstance(data, bool):
            source += str(data).lower().encode()
        elif isinstance(data, int):
            source += str(data).encode()
        elif isinstance(data, float):
            data_norm: str = "0.0" if data == 0 else str(data).replace("0.", ".") if data > -1 and data < 1 else str(data)
            source += data_norm.encode()
        else:
            source += b"(%s)" %(data.encode())
    return source

def restore_PRClipboard_Photoshop_Text(data: dict[str, Any]) -> bytes:
    '''
    将从PR文本框中复制到剪贴板中的内容中格式名称为“Photoshop Text”的文本解析成的Python字典还原成原始字节字符串。<br>Transform a Python dictionary parsed from the text with format name "Photoshop Text" in the content copied from a PR textbox into the raw byte string.
    
    如果这个字典曾经被json序列化过，那么需要处理字节串。只需要识别开头是“b"”以及结尾是“"”的字符串即可。<br>If this dictionary has been JSON serialized once, then the user should deal with the byte strings. Judge whether this string starts with 'b"' and ends with '"'.
    
    :param data: 格式名称为“Photoshop Text”的PR剪贴板的Json数据。<br>Json data from a PR clipboard with format name "Photoshop Text".
    :type data: dict[str, Any]
    :return: 原始字节字符串。<br>Raw byte string.
    :rtype: bytes
    '''
    source: bytes = traverse_PRClipboard_Photoshop_Text(b"\n", data)
    return source

def traverse_PRClipboard_Adobe_Text_Engine_v2(source: bytes, data: Any) -> bytes: #和“Photoshop Text”不同，“Adobe Text Engine 2.0”格式是没有缩进的（Different from "Photoshop Text", format "Adobe Text Engine 2.0" doesn't have any indentation）
    '''
    遍历一段由格式名称为“Adobe Text Engine 2.0”的PR剪贴板转化而成的Python字典，将各键和值通过递归的形式追加到一个字符串中。<br>Traverse a Python dictionary converted from a PR clipboard with format name "Adobe Text Engine 2.0", and append all keys and values into a byte string recursively.
    
    :param source: 原始字节字符串。作为参数的同时也作为返回值。<br>The original byte string. It acts as both the parameter and the returned value.
    :type source: bytes
    :param data: 遍历PR剪贴板字典过程中的部分数据。<br>A part of PR clipboard dictionary data.
    :type data: Any
    '''
    source += b" "
    if isinstance(data, dict):
        source += b"<<"
        for (key, value) in data.items():
            source += b" /" + key.encode()
            source = traverse_PRClipboard_Adobe_Text_Engine_v2(source, value)
        source += b" >>"
    elif isinstance(data, list):
        if len(data) == 0:
            source += b"[ ]"
        else:
            if all(map(lambda x: isinstance(x, (int | float)), data)):
                data_transform: list[str] = list(map(lambda x: "0.0" if x == 0 else str(x).replace("0.", ".") if x > -1 and x < 1 else str(x), data))
                source += ("[ " + " ".join(data_transform) + " ]").encode() #在使用默认编码的情况下，字节字符串和字面字符串的形式一定是相同（Using the default encoding, the form of the literal string must be the same as the byte string）
            else:
                source += b"["
                for elem in data:
                    source = traverse_PRClipboard_Adobe_Text_Engine_v2(source, elem)
                source += b" ]"
    else:
        if isinstance(data, bytes):
            source += b"(%s)" %data
        elif isinstance(data, str):
            source += b"/" + data.encode()
        elif isinstance(data, bool):
            source += str(data).lower().encode()
        elif isinstance(data, int):
            source += str(data).encode()
        elif isinstance(data, float):
            data_norm: str = "0.0" if data == 0 else str(data).replace("0.", ".") if data > -1 and data < 1 else str(data)
            source += data_norm.encode()
        else:
            source += b"(%s)" %(data.encode())
    return source

def restore_PRClipboard_Adobe_Text_Engine_v2(data: dict[str, Any]) -> bytes:
    '''
    将从PR文本框中复制到剪贴板中的内容中格式名称为“Adobe Text Engine 2.0”的文本解析成的Python字典还原成原始字节字符串。<br>Transform a Python dictionary parsed from the text with format name "Adobe Text Engine 2.0" in the content copied from a PR textbox into the raw byte string.
    
    如果这个字典曾经被json序列化过，那么需要处理字节串。只需要识别开头是“b"”以及结尾是“"”的字符串即可。<br>If this dictionary has been JSON serialized once, then the user should deal with the byte strings. Judge whether this string starts with 'b"' and ends with '"'.
    
    :param data: 格式名称为“Adobe Text Engine 2.0”的PR剪贴板的Json数据。<br>Json data from a PR clipboard with format name "Adobe Text Engine 2.0".
    :type data: dict[str, Any]
    :return: 原始字节字符串。<br>Raw byte string.
    :rtype: bytes
    '''
    source: bytes = traverse_PRClipboard_Adobe_Text_Engine_v2(b"", data)[3:-3] #原始数据不带开头和结尾的管道符（The raw data don't have the starting and ending pipes）
    return source

#准备一些编码转换函数（Prepare some encoding transformation function）
def decodePSText(b: bytes) -> str:
    '''
    解析一段PS文本。<br>Resolve a "Photoshop Text".
    
    :param b: 在复制一段Premiere Pro的文本框中的文本时，在剪贴板中进行重编码的文本内容。<br>The encoded text in the clipboard after the user copies a piece of text from a textbox in Premiere Pro.
    :type b: bytes
    :return: 解码后的原始文本。<be>The original text after decoding.
    :rtype: str
    '''
    return b.replace(b"\\\\", b"\\").replace(rb"\(", b"(").replace(rb"\)", b")").decode("utf-16")

def unicode2PSText(s: str) -> bytes:
    '''
    将一段unicode编码的字符串转换成PS文本格式的剪贴板数据中的字节字符串。<br>Convert a unicode-encoded string into a byte string in clipboard data in "Photoshop Text" format.
    
    :param s: 字符串。具有人类可读性。<br>A human-readable string.
    :type s: str
    :return: 适用于PS文本格式的剪贴板数据中的字节字符串。<br>A byte string that can be used in the clipboard data in "Photoshop Text" format.
    :rtype: bytes
    '''
    return b"\xfe\xff" + s.encode("utf-16-be").replace(b"\\", b"\\\\").replace(b"(", rb"\(").replace(b")", rb"\)")

#第二部分：随机元素序列处理（Part 2: Random element sequence handling）
class Option(TypedDict): #仅用于类型注释（Only used for type annotation）
    '''
    每个选择界面中的选项。<br>An option in a selection screen.
    '''
    tier: NotRequired[str] #在25.09版本，斗魂竞技场引入了萨科荣誉嘉宾，它会使得同一个强化符文选择界面中的位阶不同。当该字段未指定时，使用默认位阶（GoH Shaco was introduced in Patch 25.09, who makes the tier in the same selection screen different. When this field isn't specified, the default tier is used）
    id: str #选项识别码（Option identifier）
    upgrade: NotRequired[bool] #是否是升级选项。适用于25.09版本之后的斗魂竞技场（Whether this option is an upgrade. Applies to Arena after Patch 25.09）
    picked: NotRequired[bool] #是否选择该选项。同一个选择界面中只能选择一个选项（Whether this option is picked. Only one option can be picked in the same selection screen）
    rerolled: NotRequired[bool] #是否重随过该栏位。适用于海克斯大乱斗和25.09版本之后的斗魂竞技场（Whether this slot is rerolled. Applies to ARAM: Mayhem and Arena after Patch 25.09）
    value: NotRequired[float] #该选项的取值。适用于属性锻造器（The value of this option. Applies to stat anvil）
    reroll: NotRequired[int] #该选项的剩余重随次数。适用于海克斯大乱斗和25.09版本之后的斗魂竞技场。当该字段未指定时，使用默认重随次数（The remaining reroll times of this option. Applies to ARAM: Mayhem and Arena after Patch 25.09. When this field isn't specified, the default reroll count is used）

class Selection(TypedDict): #仅用于类型注释（Only used for type annotation）
    '''
    一次选择。<br>A selection.
    '''
    action: str #该选择界面的动作（The action of this selection screen）
    tier: NotRequired[str] #该选择界面的位阶。当该字段未指定时，必须在`selections`字段下的每个选项中指定位阶（The tier of this selection screen. When this field isn't specified, each option under the `selections` field must specify a tier）
    selections: list[Option] #该选择界面的所有选项（All options in this selection screen）
    rerolled: NotRequired[bool] #是否重随过该选择界面。适用于25.09版本之前的斗魂竞技场。当该字段未指定时，必须在`selections`字段下的每个选项中指定是否重随过（Whether this selection screen is rerolled. Applies to Arena before Patch 25.09. When this field isn't specified, each option under the `selections` field must specify whether it's rerolled）
    reroll: NotRequired[int] #该选择界面的剩余重随次数。适用于25.09版本之前的斗魂竞技场。当该字段未指定时，必须在`selections`字段下的每个选项中指定重随次数（The remaining reroll times of this selection screen. Applies to Arena before Patch 25.09. When this field isn't specified, each option under the `selections` field must specify a reroll count）
    source: str #唤起选择界面的来源。可为任意字符串（Source that invokes this selection screen. Can be any string）

def isOption(option: Any) -> tuple[bool, str]:
    '''
    判断一个对象是不是代表一个选择界面中的一个选项。<br>Judge whether an object represents an option in a selection screen.
    
    这个函数只做格式检查，不做逻辑检查。<br>This function only checks the format, not the logic.
    
    :param option: 选项数据。<br>Option data.
    :type option: Any
    :return: 一个二元组。<br>A two-tuple.
    
        - 选项记录是否合法。<br>Whether the option record is legal.
        - 消息。<br>Message.
    :rtype: tuple[bool, str]
    '''
    if not isinstance(option, dict):
        return (False, "选项类型错误。\nInvalid option data type.")
    if "tier" in option and not isinstance(option["tier"], (int, str)):
        return (False, "选项位阶类型错误。应为字符串或整数类型。实际收到%s。\nInvalid option tier data type. Expected str or int, received %s." %(type(option["tier"]).__name__, type(option["tier"]).__name__))
    if "reroll" in option:
        if not isinstance(option["reroll"], int):
            return (False, "选项剩余重随次数类型错误。应为整数类型。实际收到%s。\nInvalid option reroll data type. Expected int, received %s." %(type(option["reroll"]).__name__, type(option["reroll"]).__name__))
        elif option["reroll"] < 0:
            return (False, "选项剩余重随次数不能为负数。实际收到%d。\nInvalid option reroll data. Expected non-negative integer, received %d." %(option["reroll"], option["reroll"]))
    if not "id" in option:
        return (False, "选项缺少ID字段。\nMissing option ID field.")
    elif not isinstance(option["id"], str):
        return (False, "选项ID类型错误。应为字符串类型。实际收到%s。\nInvalid option ID data type. Expected str, received %s." %(type(option["id"]).__name__, type(option["id"]).__name__))
    # if not "upgrade" in option:
    #     return (False, "选项缺少是否升级字段。\nMissing option upgrade field.")
    if "upgrade" in option and not isinstance(option["upgrade"], bool):
        return (False, "选项升级状态类型错误。应为逻辑值。实际收到%s。\nInvalid option upgrade data type. Expected bool, received %s." %(type(option["upgrade"]).__name__, type(option["upgrade"]).__name__))
    # if not "picked" in option:
    #     return (False, "选项缺少是否选择字段。\nMissing option picked field.")
    if "picked" in option and not isinstance(option["picked"], bool):
        return (False, "选项选择状态类型错误。应为逻辑值。实际收到%s。\nInvalid option picked data type. Expected bool, received %s." %(type(option["picked"]).__name__, type(option["picked"]).__name__))
    # if not "rerolled" in option:
    #     return (False, "选项缺少是否重随字段。\nMissing option rerolled field.")
    if "rerolled" in option and not isinstance(option["rerolled"], bool):
        return (False, "选项重随状态类型错误。应为逻辑值。实际收到%s。\nInvalid option rerolled data type. Expected bool, received %s." %(type(option["rerolled"]).__name__, type(option["rerolled"]).__name__))
    # if not "value" in option:
    #     return (False, "选项缺少取值字段。\nMissing option value field.")
    if "value" in option and not isinstance(option["value"], (int, float)):
        return (False, "选项取值类型错误。应为数值类型。实际收到%s。\nInvalid option value data type. Expected int or float, received %s." %(type(option["value"]).__name__, type(option["value"]).__name__))
    return (True, "")

def isSelection(selection: Any) -> tuple[bool, str]:
    '''
    判断一个对象是不是代表一个选择界面。<br>Judge whether an object represents a selection screen.
    
    这个函数只做格式检查，不做逻辑检查。<br>This function only checks the format, not the logic.
    
    :param selection: 选择界面数据。<br>Selection screen data.
    :type selection: Any
    :return: 一个二元组。<br>A two-tuple.
    
        - 选择记录是否合法。<br>Whether the selection record is legal.
        - 消息。<br>Message.
    :rtype: tuple[bool, str]
    '''
    if not isinstance(selection, dict):
        return (False, "选择界面类型错误。\nInvalid selection screen data type.")
    if not "selections" in selection:
        return (False, "选择界面缺少选项字段。\nMissing selection screen selection field.")
    elif not isinstance(selection["selections"], list):
        return (False, "选择界面选项类型错误。应为列表类型。实际收到%s。\nInvalid selection screen selection data type. Expected list, received %s." %(type(selection["selections"]).__name__, type(selection["selections"]).__name__))
    else:
        invalid_value_struct: dict[int, str] = {} #存储格式不正确的值。键是格式不正确的元素的下标，值是报错信息（Store the index of the values with invalid format. Each key is the index of the invalid element, and each value is the error message）
        for i, value in enumerate(selection["selections"]):
            isOptionFormat, message = isOption(value)
            if not isOptionFormat:
                invalid_value_struct[i] = message
        if len(invalid_value_struct) > 0:
            message: str = ""
            if len(invalid_value_struct) > 0:
                message += "格式不正确的选项：\nInvalid options:\n"
                for i, err_msg in invalid_value_struct.items():
                    message += f"  - [{i}] {err_msg}\n"
            return (False, message)
    if selection.get("tier") is None and any(map(lambda x: x.get("tier") is None, selection["selections"])):
        return (False, "选择界面缺少位阶字段，且选项中也缺少位阶字段。\nMissing selection screen tier field, and missing option tier field as well.")
    # if selection.get("rerolled") is None and any(map(lambda x: x.get("rerolled") is None, selection["selections"])):
    #     return (False, "选择界面缺少是否重随字段，且选项中也缺少是否重随字段。\nMissing selection screen rerolled field, and missing option rerolled field as well.")
    # if selection.get("reroll") is None and any(map(lambda x: x.get("reroll") is None, selection["selections"])):
    #     return (False, "选择界面缺少剩余重随次数字段，且选项中也缺少剩余重随次数字段。\nMissing selection screen remaining reroll field, and missing option remaining reroll field as well.")
    if "action" in selection and not selection["action"] in {"supply", "reroll", "select"}:
        return (False, '选择界面动作字段值错误。应为“供应”“重随”和“选择”之一。实际收到%s。\nInvalid selection screen action field value. Expected one of "supply", "reroll" and "select", received %s.' %(selection["action"], selection["action"]))
    if "tier" in selection and not isinstance(selection["tier"], (int, str)):
        return (False, "选择界面位阶类型错误。应为字符串或整数类型。实际收到%s。\nInvalid selection screen tier data type. Expected str or int, received %s." %(type(selection["tier"]).__name__, type(selection["tier"]).__name__))
    if "rerolled" in selection and not isinstance(selection["rerolled"], bool):
        return (False, "选择界面是否重随字段类型错误。应为逻辑值。实际收到%s。\nInvalid selection screen rerolled data type. Expected bool, received %s." %(type(selection["rerolled"]).__name__, type(selection["rerolled"]).__name__))
    if "reroll" in selection and not isinstance(selection["reroll"], int):
        return (False, "选择界面剩余重随次数类型错误。应为整数类型。实际收到%s。\nInvalid selection screen remaining reroll data type. Expected int, received %s." %(type(selection["reroll"]).__name__, type(selection["reroll"]).__name__))
    if not "source" in selection:
        return (False, "选择界面缺少来源字段。\nMissing selection screen source field.")
    elif not isinstance(selection["source"], str):
        return (False, "选择界面来源类型错误。应为字符串类型。实际收到%s。\nInvalid selection screen source data type. Expected str, received %s." %(type(selection["source"]).__name__, type(selection["source"]).__name__))
    return (True, "")

Locale = Literal["en_US", "zh_CN"] #定义语言文化代码的枚举类型（Define the enumeration type of locale）
Stringtable = dict[str, dict[Locale, str]] #定义字符串常量池类型（Define the stringtable type）

class LoLRandomElementSequence:
    VALID_TIERS_STR: set[str] = {"Silver", "Gold", "Prismatic", "Sheenglow"} #存储所有合法的位阶（Store all valid tiers）
    VALID_TIERS_INT: set[int] = {0, 1, 2, 4}
    TIER_MAP: dict[int, str] = {0: "Silver", 1: "Gold", 2: "Prismatic", 4: "Sheenglow"} #用于读取文件时处理整数类型的稀有度（Used to handle the rarity of integer type from a file）
    VALID_TYPES: dict[Any, list[str]] = {tier: list() for tier in VALID_TIERS_STR} #存储所有合法的随机元素类型（Store all valid random element types）
    TIER_STRINGTABLE: Stringtable = {
        "Silver": {
            "en_US": "Silver",
            "zh_CN": "白银阶"
        },
        "Gold": {
            "en_US": "Gold",
            "zh_CN": "黄金阶"
        },
        "Prismatic": {
            "en_US": "Prismatic",
            "zh_CN": "棱彩阶"
        },
        "Sheenglow": {
            "en_US": "SheenGlow",
            "zh_CN": "晶耀阶"
        }
    }
    TIER_CASE_MAP: dict[str, str] = {key.lower(): key for key in VALID_TIERS_STR}
    
    def __init__(self) -> None:
        '''
        一个处理英雄联盟中采用Rogue-like思想的游戏模式中的部分随机元素的统计序列的基类，包括斗魂竞技场和海克斯大乱斗。<br>A base class that handles the sequence of some random elements in Rogue-like game modes in League of Legends, including Arena and ARAM: Mayhem.
        
        目前支持的随机元素包括强化符文、装备锻造器和属性锻造器。<br>Currently supported random elements include augments, item anvils and stat anvils.
        '''
        self.counter: dict[str, dict[str, dict[str, int | float]]] = {} #随机元素计数器。中间变量，存储特定时刻的随机元素数量和取值。结构是位阶—名称—统计指标—统计值（Random element counter. An intermediate variable that stores random element count at specific time. The structure is tier - name - statistical indicator - statistics）
        self.sequence: list[dict[str, dict[str, dict[str, int | float]]]] = [] #随机元素时间序列。随着程序运行，存储各个时刻下的`self.counter`（Random element sequence, which stores `self.counter` at each point in time as the program runs）
        self.selections: list[Selection] = [] #用户经历过的所有选择界面（All selections the user has encountered）
        self.latest_selection: Selection = {"action": "", "tier": "", "selections": [], "rerolled": False, "reroll": 0, "source": ""} #初始化最近遇到的一次选择界面（Initialize the recently encountered selection）
    
    @property
    def snapshot_count(self) -> int:
        '''
        动态返回快照的数量。<br>Dynamically return the number of snapshots.
        
        注意：在刚刚构造一个子类的对象时，快照数量为1。<br>Note: When an object of a subclass is just constructed, the number of snapshots is 1.
        
        :return: 快照数量。逻辑上等于`self.sequence`的长度。<br>The number of snapshots. Logically, it's equal to the size of `self.sequence`.
        :rtype: int
        '''
        return len(self.sequence)
    
    @property
    def selection_count(self) -> int:
        '''
        动态返回用户做出的选择次数。<br>Dynamically return the number of selections the user has made.
        
        在一个基类对象中，这个属性值应总是为0。<br>In an object of the base class, the value of this property should always be 0.
        
        :return: 用户的选择次数。逻辑上等于`self.selections`的长度。<br>The number of selections made by the user. Logically, it's equal to the size of `self.selections`.
        :rtype: int
        '''
        return len(self.selections)
    
    @classmethod
    def normalize_tier(cls, tier: int | str) -> str:
        '''
        将位阶转化成字符串类型并统一大小写。<br>Transform the tier into a string and unify its case.
        
        :param tier: 来自用户输入的位阶。<br>Tier from user input.
        :type tier: int | str
        :return: 标准化后的位阶。<br>Normalized tier.
        :rtype: str
        '''
        if isinstance(tier, int): #虽然内存中要求位阶必须是标准的字符串，但是用户在传入数据时可以用数字简单表示（Although tier is required to be standard strings in the memory, users may input a simple number）
            return cls.TIER_MAP[tier]
        else:
            return tier.lower().capitalize()
    
    def snapshot(self) -> None:
        '''
        将当前计数器添加到时间序列中。<br>Append the current counter to the end of the sequence.
        
        不应在基类中调用此方法。<br>Shouldn't call this method in the base class.
        '''
        self.sequence.append(copy.deepcopy(self.counter))
    
    @classmethod
    def verify_selection_record(cls, selection: Any, count_verify: int = 3) -> tuple[bool, str]:
        '''
        检查一条选择记录是否合法。<br>Check whether a selection record is legal.
        
        :param selection: 选择界面数据。<br>Selection screen data.
        
            相关要求见`increment`方法。<br>Refer to `increment` method for its requirements.
        :type selection: Selection
        :param count_verify: 选项数量校验。当用户传入的选项数量不对时，该方法将不会执行任何操作。<br>Option number verification. When there's a wrong number of options passed into this method, no operation will be performed.
        
            在当前版本，选择界面提供3个选项。<br>In current version, there're 3 options in a selection screen.
        :type count_verify: int
        :return: 一个二元组。<br>A two-tuple.
        
            - 选择记录是否合法。<br>Whether the selection record is legal.
            - 消息。<br>Message.
        :rtype: tuple[bool, str]
        '''
        #初始化返回值（Initialize the returned value）
        message: str = ""
        #格式校验（Format verification）
        isSelectionFormat, message = isSelection(selection)
        if not isSelectionFormat:
            return (False, message)
        #逻辑检验（Logic verification）
        ##位阶（Tier）
        if "tier" in selection and not selection["tier"] in cls.VALID_TIERS_STR | cls.VALID_TIERS_INT: #虽然内存中要求位阶必须是标准的字符串，但是用户在传入数据时可以用数字简单表示（Although tier is required to be standard strings in the memory, users may input a simple number）
            message = "不存在的选择界面位阶：%s。\nInvalid selection screen tier: %s." %(selection["tier"], selection["tier"])
            return (False, message)
        invalid_tier_struct: dict[int, str] = {} #存储不正确的选项位阶。键是不正确的选项的下标，值是位阶（Store the index of the options with invalid tier. Each key is the index of the invalid option, and each value is the tier）
        for i, value in enumerate(selection["selections"]):
            if "tier" in value and not value["tier"] in cls.VALID_TIERS_STR | cls.VALID_TIERS_INT:
                invalid_tier_struct[i] = value["tier"]
        if len(invalid_tier_struct) > 0:
            message = "不存在的选项位阶：\nInvalid option tiers:\n"
            for i, tier in invalid_tier_struct.items():
                message += f"  - [{i}] {tier}\n"
            return (False, message)
        ##选项数量（Number）
        if len(selection["selections"]) != count_verify:
            message = "选项数量错误。应为%d，实际收到%d。\nWrong number of options. Expected %d, received %d." %(count_verify, len(selection["selections"]), count_verify, len(selection["selections"]))
            return (False, message)
        ##类型（Type）
        unidentified_elementTypes: list[str] = []
        for option in selection["selections"]:
            option_tier: str | int = selection.get("tier", option.get("tier", ""))
            if isinstance(option_tier, int):
                option_tier = cls.TIER_MAP[option_tier] #因为前面对位阶做过检验了，所以这里不需要担心键不存在的问题（Because the tier has been verified, there's no need to worry about the KeyError）
            if not option["id"].lower() in set(map(lambda x: x.lower(), cls.VALID_TYPES[option_tier])):
                unidentified_elementTypes.append(option["id"])
        if len(unidentified_elementTypes) > 0:
            message = "以下选项不存在：\nOptions not found:\n" + str(unidentified_elementTypes).replace("'", '"')
            return (False, message)
        ##行为（Action）
        total_rerolled: int = sum(map(lambda x: x.get("rerolled", False), selection["selections"])) + selection.get("rerolled", False)
        total_picked: int = sum(map(lambda x: x.get("picked", False), selection["selections"]))
        if selection["action"] == "supply":
            if total_rerolled != 0:
                message = "选择行为错误。供应行为不应重随任何选项，实际重随%d个选项。\nWrong selection behavior. Supply action shouldn't have any option rerolled but received %d option(s) rerolled." %(total_rerolled, total_rerolled)
                return (False, message)
            if total_picked != 0:
                message = "选择行为错误。供应行为不应选择任何选项，实际选择%d个选项。\nWrong selection behavior. Supply action shouldn't have any option picked but received %d option(s) picked." %(total_picked, total_picked)
                return (False, message)
        elif selection["action"] == "reroll":
            if total_rerolled != 1:
                message = "选择行为错误。重随行为应重随1个选项，实际重随%d个选项。\nWrong selection behavior. Reroll action should have 1 option rerolled but received %d option(s) rerolled." %(total_rerolled, total_rerolled)
                return (False, message)
            if total_picked != 0:
                message = "选择行为错误。重随行为不应选择任何选项，实际选择%d个选项。\nWrong selection behavior. Reroll action shouldn't have any option picked but received %d option(s) picked." %(total_picked, total_picked)
                return (False, message)
        else:
            if total_rerolled != 0:
                message = "选择行为错误。选择行为不应有任何选项被重随过，实际重随%d个选项。\nWrong selection behavior. Select action shouldn't have any option rerolled but received %d option(s) rerolled." %(total_rerolled, total_rerolled)
                return (False, message)
            if total_picked != 1:
                message = "选择行为错误。选择行为应选择1个选项，实际选择%d个选项。\nWrong selection behavior. Expected 1 option selected but received %d option(s) selected." %(total_picked, total_picked)
                return (False, message)
        return (True, message)
    
    @classmethod
    def verify_selection_recordList(cls, records: Any) -> tuple[bool, str]:
        '''
        检查多条记录是否合法。<br>Check whether multiple selection records are legal.
        
        :param records: 选择记录列表。<br>Selection record list.
        
            相关要求见`extend`方法。<br>Refer to `extend` method for its requirements.
        :type records: list[tuple[str, Selection]]
        :return: 一个二元组。<br>A two-tuple.
        
            - 选择记录列表是否合法。<br>Whether the selection record list is legal.
            - 消息。<br>Message.
        :rtype: tuple[bool, str]
        '''
        #初始化返回值（Initialize the returned value）
        message: str = ""
        if not isinstance(records, list):
            message = "选择记录列表参数格式错误。\nSelection record list parameter format error."
            return (False, message)
        format_mismatch: list[tuple[int, Selection]] = []
        for i, record in enumerate(records):
            selection_legal, selection_message = cls.verify_selection_record(record)
            if not selection_legal:
                print(f"[{i}]", selection_message)
                format_mismatch.append((i, record))
        if len(format_mismatch) > 0:
            message += "以下选择记录的参数格式有误：\nThe following records have an incorrect format of parameters:\n"
            for i, record in format_mismatch:
                message += "[%d] %s\n" %(i, str(record).replace("'", '"'))
        return (len(format_mismatch) == 0, message)
    
    @classmethod
    def default_elementId_map(cls, elementId: str) -> str:
        '''
        默认的元素识别码映射方式。用于对来自用户输入的元素识别码进行大小写规范。<br>The default mapping method for element id. It's meant to normalize the case of element ids from user input.
        
        基类中的此方法直接返回原始字符串。它只是起占位作用。开发者应当在子类中模仿此方法定义相应的映射方法。<br>This method in the base class just returns the original string. It's just a dummy. The developer should define corresponding mapping method in the sub-class.
        
        在类的外部调用子类的元素识别码映射方法时，推荐用户调用另行定义的方法，而不是调用子类中用来覆盖基类的方法。<br>When the user is calling the elementId mapping method outside of the class, it's highly recommended that users call the separately defined method, instead of the sub-class method used to override the class method.
        
        例如，推荐用户使用`StatAnvilSequence.anvilId_map`而不是`StatAnvilSequence.default_elementId_map`。<br>For example, users are recommended to call `StatAnvilSequence.anvilId_map` instead of `StatAnvilSequence.default_elementId_map`.
        
        :param elementId: 元素识别码。<br>Element id.
        :type elementId: str
        :return: 标准化后的元素识别码。<br>Normalized element id.
        :rtype: str
        '''
        raise NotImplementedError("Method body not declared. Call this method in a sub-class instead.")
    
    def increment(self, selection: Selection, elementId_map: Optional[Callable[[str], str]] = None) -> int:
        '''
        递增计数器。<br>Increment the counter.
        
        该方法会校验用户的输入正确性。如果发现错误，则不执行任何操作。<br>This method verifies the correctness of the user input. If an error is found, then no operation will be performed.
        
        :param selection: 选择界面数据。<br>Selection screen data.
        
            格式（Schemas）：{"action": str, "tier": str, "selections": [{"tier": str, "id": str, "upgrade": bool, "picked": bool, "rerolled": bool, "value": float, "reroll": int}], "rerolled": bool, "reroll": int}
            - 所有字符串不区分大小写。<br>All strings are case insensitive.
            
            位阶有以下取值：<br>Tier has the following values:
            - 0 | "silver": 白银阶（Silver）
            - 1 | "gold": 黄金阶（Gold）
            - 2 | "prismatic": 棱彩阶（Prismatic）
            - 4 | "sheenglow": 晶耀阶（SheenGlow）
            - 该参数可同时接受整数或字符串类型。<br>This parameter accepts both an integer or a string.
        :type selection: dict[str, bool]
        :return: 状态码。<br>Status code.
        
            - 0: 导入成功。<br>Import succeeded.
            - 1: 导入失败。<br>Import failed.
        :rtype: int
        '''
        #参数预处理（Parameter pre-processing）
        if elementId_map is None:
            elementId_map = self.default_elementId_map
        #参数校验（Parameter verification）
        valid, message = self.verify_selection_record(selection)
        if not valid:
            print(message)
            return 1
        #准备一些标志（Prepare some flags）
        action: str = selection["action"]
        #标准化选择数据（Normalize the selection data）
        selection_norm: Selection = copy.deepcopy(selection)
        if "tier" in selection: #标准化选择界面位阶（Normalize the selection screen's tier）
            selection_norm["tier"] = self.normalize_tier(selection["tier"])
        #递增（Increment）
        for i, option in enumerate(selection["selections"]):
            rarity: int | str = option.get("tier", selection.get("tier", ""))
            tier: str = self.normalize_tier(rarity)
            if "tier" in selection["selections"][i]: #标准化选项位阶，但是仅在选项有位阶字段时（Normalize the option's tier, but only when the option data has the tier field）
                selection_norm["selections"][i]["tier"] = tier
            elementId: str = elementId_map(option["id"].lower())
            selection_norm["selections"][i]["id"] = elementId #标准化选项代码（Normalize the option's code）
            option_counter: dict[str, int | float] = self.counter[tier][elementId]
            option_selected: bool = option.get("picked", False)
            option_upgrade: bool = option.get("upgrade", False)
            option_rerolled: bool = option.get("rerolled", False)
            option_value: float = option.get("value", 0)
            if not option_upgrade: #计数器不对升级强化符文进行统计（The counter doesn't count augments to level up）
                if action == "supply":
                    option_counter["supplyCount"] += 1
                elif action == "reroll":
                    if option_rerolled:
                        option_counter["supplyCount"] += 1
                else:
                    if option_selected:
                        option_counter["selectCount"] += 1
            if action == "reroll" and option_rerolled: #计数器仍统计对升级强化符文的重随（The counter still count the rerolls of augments to level up）
                option_counter["reroll"] -= 1
            option_counter["value"] = option_value
        self.snapshot() #将最近一次变动保存到序列中（Save the latest change into the sequence）
        self.latest_selection = selection_norm
        self.selections.append(self.latest_selection)
        return 0
    
    def extend(self, records: list[Selection], elementId_map: Optional[Callable[[str], str]] = None) -> int:
        '''
        批量导入多个选择界面。<br>Import multiple selection screens in batch.
        
        :param records: 选择界面列表。<br>Selection screen list.
        
            注意，一旦有一个选择界面出现问题，所有的选择界面都无法导入。<br>Note that if there's any erroneous selection screen, then no record will be imported.
        :type records: list[selection]
        :param elementId_map: 元素识别码映射函数，用于统一大小写。如果未指定，则使用类内指定的默认对应方式。<br>A element identifier map function used to unify the case. If it's not specified, then the default mapping defined in the class is used.
        :type elementId_map: Optional[Callable[[str], str]]
        :return: 状态码。<br>Status code.
        
            - 0: 导入成功。<br>Import succeeded.
            - 1: 导入失败。<br>Import failed.
        :rtype: int
        '''
        #参数预处理（Parameter pre-processing）
        if elementId_map is None:
            elementId_map = self.default_elementId_map
        #参数校验（Parameter verification）
        valid, message = self.verify_selection_recordList(records)
        if valid:
            for record in records:
                self.increment(record, elementId_map = elementId_map)
            return 0
        else:
            print(message)
            return 1
    
    def recall(self) -> None:
        '''
        返回上一个选择界面快照。<br>Revert to the last selection screen snapshot.
        '''
        if self.selection_count == 0:
            print("尚未做出选择。\nNo selection has been made.")
            return
        #准备一些标志（Prepare some flags）
        action: str = self.latest_selection["action"]
        #递减（Decrement）
        for option in self.latest_selection["selections"]:
            tier: str = self.latest_selection.get("tier", option.get("tier", "")) #存储在内存中的位阶一定是字符串类型（The tier stored in memory must be a string）
            elementId: str = option["id"]
            option_counter: dict[str, int | float] = self.counter[tier][elementId]
            option_selected: bool = option.get("picked", False)
            option_upgrade: bool = option.get("upgrade", False)
            option_rerolled: bool = option.get("rerolled", False)
            if not option_upgrade: #计数器不对升级强化符文进行统计（The counter doesn't count augments to level up）
                if action == "supply":
                    option_counter["supplyCount"] -= 1
                elif action == "reroll":
                    if option_rerolled:
                        option_counter["supplyCount"] -= 1
                else: #action == "select"
                    if option_selected:
                        option_counter["selectCount"] -= 1
            if action == "reroll" and option_rerolled: #计数器仍统计对升级强化符文的重随（The counter still count the rerolls of augments to level up）
                option_counter["reroll"] += 1
            option_counter["value"] = self.sequence[-2][tier][elementId]["value"] #恢复到上一个快照的值（Restore to the value of the previous snapshot）
        #后处理（Post processing）
        self.selections.pop(-1)
        self.latest_selection = {"action": "", "tier": "", "selections": [], "rerolled": False, "reroll": 0, "source": ""} if self.selection_count == 0 else self.selections[-1]
        self.sequence.pop(-1)
        # self.counter = copy.deepcopy(self.sequence[-1]) #为了便于追踪同一内存地址，这里没有使用此简化代码，而是手动实现递增的逆运算（For the convenience of tracing the same memory address, here this simplified code isn't used. Instead, a reserve operation is implemented manually above）
    
    def restore(self, index: int = -2) -> None:
        '''
        将对象恢复到某个快照所在状态。<br>Restore the object to some snapshot.
        
        :param index: 快照下标。取值范围是`[-self.snapshot_count, self.snapshot_count - 1]`内的整数。<br>The index of the snapshot. Should be within `[-self.snapshot_count, self.snapshot_count - 1]` range.
        
            如果未指定，则撤销最近一次选择。<br>If it's not specified, then revert the latest selection.
        :type index: int
        '''
        if self.selection_count == 0:
            print("尚未做出选择。\nNo selection has been made.")
            return
        if index < - self.snapshot_count or index >= self.snapshot_count:
            print("下标越界。\nIndex out of bounds.")
            return
        #确定撤回几次选择（Determine the number of recalls）
        if index < 0:
            recall_count: int = -1 - index
        else:
            recall_count = self.snapshot_count - 1 - index
        #恢复快照（Restore to the snapshot）
        for _ in range(recall_count):
            self.recall()
    
    def reset(self) -> None:
        '''
        重置时间序列和计数器。<br>Reset the sequence and the counter.
        
        不应在基类中调用此方法。<br>Shouldn't call this method in the base class.
        '''
        for countDict in self.counter.values():
            for elementType in countDict:
                countDict[elementType]["supplyCount"] = 0
                countDict[elementType]["selectCount"] = 0
                countDict[elementType]["value"] = 0
        self.sequence.clear()
        self.snapshot()
        self.selections.clear()
        self.latest_selection = {"action": "", "tier": "", "selections": [], "rerolled": False, "reroll": 0, "source": ""}

class StatAnvilSequence(LoLRandomElementSequence):
    VALID_SILVER_TYPES: list[str] = ["AH", "AD", "AP", "Hybrid2", "AM", "MR", "Hybrid3", "HP", "AS", "Hybrid1", "CSC", "LTH", "MRPF", "Random"]
    VALID_GOLD_TYPES: list[str] = ["AH", "AD", "AP", "Hybrid2", "AM", "MR", "Hybrid3", "HP", "AS", "Hybrid1", "CSC", "LTH", "MRPF", "Random", "ShardBladeAnvils"]
    VALID_PRISMATIC_TYPES: list[str] = ["MS", "HPSZ", "CSD", "OMV", "TNC", "HSP", "AMP", "MRPP", "Gold", "GoldRoundLoss", "Pristine", "UpgradeShards"]
    VALID_TYPES: dict[str | int, list[str]] = {"Silver": VALID_SILVER_TYPES, "Gold": VALID_GOLD_TYPES, "Prismatic": VALID_PRISMATIC_TYPES} #之所以设置成列表而不是集合，是为了保证输出排版时的有序性（The reason why each value is a list instead of a set is to ensure the output is organized）
    VALID_SOURCES: list[str] = ["Items/6032", "Items/220008", "Items/220009", "Items/220010", "Items/220011", "Maps/Shipping/Map30/AugmentTags/PrismaticEgg", "Maps/Shipping/Map30/AugmentTags/Stats", "Maps/Shipping/Map30/AugmentTags/StatsOnStats", "Maps/Shipping/Map30/AugmentTags/StatsOnStatsOnStats", "Maps/Shipping/Map30/AugmentTags/CraftingPrisStatAnvil", "Maps/Shipping/Map30/AugmentTags/GainStatAnvil", "Maps/Shipping/Map30/AugmentTags/GoHAbstainFromPower", "Maps/Shipping/Map30/AugmentTags/GoHCravingForPower", "Maps/Shipping/Map30/AugmentTags/GoHCompulsionForPower", "Maps/ModeSpecificData/Augments/DustToDiamonds", "Maps/ModeSpecificData/Augments/ARAM_StatsOnStatsOnStats", "Maps/ModeSpecificData/Augments/ARAM_StatsOnStats", "Maps/ModeSpecificData/Augments/ARAM_Stats", "{d8f6a848}", "Maps/Shipping/Map30/GuestOfHonor/Draven", "Maps/Shipping/Map30/GuestOfHonor/Swain", "Maps/Shipping/Map30/GuestOfHonor/Atakhan", "Maps/Shipping/Map30/GuestOfHonor/Fiddlesticks", "Maps/Shipping/Map30/GuestOfHonor/Kayle", "Maps/Shipping/Map30/GuestOfHonor/Locke", "{a241b299}"]
    # STAT_ANVIL_SNAPSHOT_TEMPLATE: dict[str, dict[str, dict[str, int | float]]] = {tier: {anvilType: {"supplyCount": 0, "selectCount": 0, "value": 0} for anvilType in VALID_TYPES[tier]} for tier in LoLRandomElementSequence.VALID_TIERS_STR} #NameError: name 'VALID_TYPES' is not defined
    STAT_ANVIL_SNAPSHOT_TEMPLATE: dict[str, dict[str, dict[str, int | float]]] = {}
    for _tier in LoLRandomElementSequence.VALID_TIERS_STR:
        if _tier in VALID_TYPES:
            STAT_ANVIL_SNAPSHOT_TEMPLATE[_tier] = {_anvilType: {"supplyCount": 0, "selectCount": 0, "value": 0} for _anvilType in VALID_TYPES[_tier]}
    ANVILSOURCE_STRINGTABLE: Stringtable = {
        "Items/6032": {
            "en_US": "Stat Bonus",
            "zh_CN": "属性加成",
        },
        "Items/220008": {
            "en_US": "Anvil Voucher",
            "zh_CN": "锻造器兑换券"
        },
        "Items/220009": {
            "en_US": "Gold Stat Anvil Voucher",
            "zh_CN": "黄金阶属性锻造器兑换券"
        },
        "Items/220010": {
            "en_US": "Prismatic Stat Voucher",
            "zh_CN": "棱彩阶属性锻造器兑换券"
        },
        "Items/220011": {
            "en_US": "Bravery Voucher",
            "zh_CN": "勇敢举动兑换券"
        },
        "Maps/Shipping/Map30/AugmentTags/PrismaticEgg": {
            "en_US": "Prismatic Egg",
            "zh_CN": "棱彩蛋"
        },
        "Maps/Shipping/Map30/AugmentTags/Stats": {
            "en_US": "Stats!",
            "zh_CN": "属性！"
        },
        "Maps/Shipping/Map30/AugmentTags/StatsOnStats": {
            "en_US": "Stats on Stats!",
            "zh_CN": "属性叠属性！"
        },
        "Maps/Shipping/Map30/AugmentTags/StatsOnStatsOnStats": {
            "en_US": "Stats on Stats on Stats!",
            "zh_CN": "属性叠属性叠属性！"
        },
        "Maps/Shipping/Map30/AugmentTags/CraftingPrisStatAnvil": {
            "en_US": "Gain A Prismatic Stat Anvil",
            "zh_CN": "获得一个棱彩阶属性锻造器"
        },
        "Maps/Shipping/Map30/AugmentTags/GainStatAnvil": {
            "en_US": "Gain Stat Anvil",
            "zh_CN": "获得属性锻造器"
        },
        "Maps/Shipping/Map30/AugmentTags/GoHAbstainFromPower": {
            "en_US": "Abstain from Power",
            "zh_CN": "戒绝权力"
        },
        "Maps/Shipping/Map30/AugmentTags/GoHCravingForPower": {
            "en_US": "Craving for Power",
            "zh_CN": "渴望权力"
        },
        "Maps/Shipping/Map30/AugmentTags/GoHCompulsionForPower": {
            "en_US": "Compulsion for Power",
            "zh_CN": "强求权力"
        },
        "Maps/ModeSpecificData/Augments/DustToDiamonds": {
            "en_US": "Dust to Diamonds",
            "zh_CN": "变废为宝"
        },
        "Maps/ModeSpecificData/Augments/ARAM_StatsOnStatsOnStats": {
            "en_US": "Stats on Stats on Stats!",
            "zh_CN": "属性叠属性叠属性！"
        },
        "Maps/ModeSpecificData/Augments/ARAM_StatsOnStats": {
            "en_US": "Stats on Stats!",
            "zh_CN": "属性叠属性！"
        },
        "Maps/ModeSpecificData/Augments/ARAM_Stats": {
            "en_US": "Stats!",
            "zh_CN": "属性！"
        },
        "{d8f6a848}": {
            "en_US": "Hone Shardblade",
            "zh_CN": "打磨碎片之刃"
        },
        "Maps/Shipping/Map30/GuestOfHonor/Draven": {
            "en_US": "Risky Show",
            "zh_CN": "冒险秀"
        },
        "Maps/Shipping/Map30/GuestOfHonor/Swain": {
            "en_US": "Demonic Ascension",
            "zh_CN": "恶魔升华"
        },
        "Maps/Shipping/Map30/GuestOfHonor/Atakhan": {
            "en_US": "Atakhan's Bounty",
            "zh_CN": "厄塔汗的悬赏"
        },
        "Maps/Shipping/Map30/GuestOfHonor/Fiddlesticks": {
            "en_US": "A Harmless Scarecrow",
            "zh_CN": "巫骇草人"
        },
        "Maps/Shipping/Map30/GuestOfHonor/Kayle": {
            "en_US": "Divine Ascent",
            "zh_CN": "登神长阶"
        },
        "Maps/Shipping/Map30/GuestOfHonor/Locke": {
            "en_US": "Soul Unbound",
            "zh_CN": "灵魂跃迁"
        },
        "{a241b299}": {
            "en_US": "True Damage",
            "zh_CN": "真实伤害"
        }
    }
    ANVILTYPE_STRINGTABLE: Stringtable = {
        "AH": {
            "en_US": "Ability Haste Shard",
            "zh_CN": "技能急速碎片"
        },
        "AD": {
            "en_US": "Attack Damage Shard",
            "zh_CN": "攻击力碎片"
        },
        "AP": {
            "en_US": "Ability Power Shard",
            "zh_CN": "法术强度碎片"
        },
        "AM": {
            "en_US": "Armor Shard",
            "zh_CN": "护甲碎片"
        },
        "MR": {
            "en_US": "Magic Resist Shard",
            "zh_CN": "魔法抗性碎片"
        },
        "HP": {
            "en_US": "Health Shard",
            "zh_CN": "生命值碎片"
        },
        "AS": {
            "en_US": "Attack Speed Shard",
            "zh_CN": "攻击速度碎片"
        },
        "CSC": {
            "en_US": "Critical Strike Shard",
            "zh_CN": "暴击碎片"
        },
        "LTH": {
            "en_US": "Lethality Shard",
            "zh_CN": "穿甲碎片"
        },
        "MRPF": {
            "en_US": "Fixed Magic Penetration Shard", #这里为了方便后续可能的字典键值颠换，特意将其与MRPP的字符串区分开来。在读取用户输入或者导出数据时，应当针对这两个锻造器类型进行特殊处理（To facilitate any potential future swapping of dictionary keys and values, this string is explicitly distinguished from the MRPP strings. When the program reads user input or exports data, special handling should be implemented for these two anvil types）
            "zh_CN": "固定法术穿透碎片"
        },
        "MS": {
            "en_US": "Move Speed Shard",
            "zh_CN": "移动速度碎片"
        },
        "HPSZ": {
            "en_US": "Health and Size Shard",
            "zh_CN": "生命值与体型碎片"
        },
        "CSD": {
            "en_US": "Critical Damage Shard",
            "zh_CN": "暴击伤害碎片"
        },
        "OMV": {
            "en_US": "Omnivamp Shard",
            "zh_CN": "全能吸血碎片"
        },
        "TNC": {
            "en_US": "Tenacity Shard",
            "zh_CN": "韧性碎片"
        },
        "HSP": {
            "en_US": "Heal & Shield Power Shard",
            "zh_CN": "治疗与护盾强度碎片"
        },
        "AMP": {
            "en_US": "Armor Penetration Shard",
            "zh_CN": "护甲穿透碎片"
        },
        "MRPP": {
            "en_US": "Pencentage Magic Penetration Shard",
            "zh_CN": "百分比法术穿透碎片"
        },
        "Hybrid1": {
            "en_US": "Swiftness Shard",
            "zh_CN": "迅捷碎片"
        },
        "Hybrid2": {
            "en_US": "Might Shard",
            "zh_CN": "力量碎片"
        },
        "Hybrid3": {
            "en_US": "Unbreakable Shard",
            "zh_CN": "坚不可摧碎片"
        },
        "Random": {
            "en_US": "Two Random Shards",
            "zh_CN": "两个随机碎片"
        },
        "Gold": {
            "en_US": "Fortune Shard",
            "zh_CN": "好运碎片"
        },
        "GoldRoundLoss": {
            "en_US": "Care Package",
            "zh_CN": "关爱包裹"
        },
        "Pristine": {
            "en_US": "Shardholder Value Shard",
            "zh_CN": "碎片增幅碎片"
        },
        "UpgradeShards": {
            "en_US": "Shardholder Value Shard",
            "zh_CN": "碎片增幅碎片"
        },
        "ShardBladeAnvils": {
            "en_US": "Hone Shardblade",
            "zh_CN": "打磨碎片之刃"
        }
    }
    ANVILSOURCE_CASE_MAP: dict[str, str] = {key.lower(): key for key in VALID_SOURCES} #注意：斗魂竞技场和海克斯大乱斗的叠属性强化符文的主键不同，但是本地化名称完全相同。这是一个无关紧要的二义性（Note: The keys of stats augments are different between Arena and ARAM: Mayhem. However, they share the same localized names between the two modes. This is an unimportant ambiguity）
    ANVILTYPE_CASE_MAP: dict[str, str] = {key.lower(): key for value in STAT_ANVIL_SNAPSHOT_TEMPLATE.values() for key in value} #用户输入的时候允许忽略大小写，在方法内部还原大小写（The user input is case sensitive. Restore the case inside this method）
    
    def __init__(self) -> None:
        '''
        初始化一个属性锻造器时间序列对象。<br>Initialize a `StatAnvilSequence` object.
        '''
        super().__init__()
        self.counter: dict[str, dict[str, dict[str, int | float]]] = copy.deepcopy(self.STAT_ANVIL_SNAPSHOT_TEMPLATE) #深复制防止修改模板常量字典（Deep copy avoids changing the template constant dictionary）
        self.snapshot() #在该类对象初始化时立即拍一次快照（Take the first snapshot right when an object of this class is initialized）
    
    @classmethod
    def anvilId_map(cls, anvilId: str) -> str: #为了使得子类有配套的文档字符串，并引导外部调用，特定义此方法（This method is defined to make sure the method in the sub-class has suited DocString and to facilitate external call）
        '''
        规范来自用户输入的锻造器代码的大小写。<br>Standardize the case of the anvilId from user input.
        
        :param anvilId: 锻造器代码。参见此类的`VALID_TYPES`属性。<br>Anvil id. Refer to the `VALID_TYPES` attribute of this class for the detail.
        :type anvilId: str
        :return: 标准化后的锻造器代码。<br>Normalized anvil id.
        :rtype: str
        '''
        return cls.ANVILTYPE_CASE_MAP[anvilId.lower()]
    
    @classmethod
    def default_elementId_map(cls, elementId: str) -> str:
        return cls.anvilId_map(elementId)
    
    def increment_statanvil(self, selection: Selection) -> int:
        '''
        递增属性锻造器计数器。<br>Increment stat anvil counters.
        
        该方法会校验用户的输入正确性。如果发现错误，则不执行任何操作。<br>This method verifies the correctness of the user input. If an error is found, then no operation will be performed.
        
        :param selection: 属性锻造器选择界面数据。格式见基类的递增方法。<br>Stat anvil selection screen data. Refer to the `increment` method in the base class for the schemas.
        
            锻造器类型列举如下：（这里不区分位阶。）<br>All anvil types are listed below: (Here we don't consider tiers.)
            - AH: 技能急速碎片（Ability Haste Shard）
            - AD: 攻击力碎片（Attack Damage Shard）
            - AP: 法术强度碎片（Ability Power Shard）
            - AM: 护甲碎片（Armor Shard）
            - MR: 魔法抗性碎片（Magic Resist Shard）
            - HP: 生命值碎片（Health Shard）
            - AS: 攻击速度碎片（Attack Speed Shard）
            - CSC: 暴击碎片（Critical Strike Shard）
            - LTH: 穿甲碎片（Lethality Shard）
            - MRPF: 固定法术穿透碎片（Fixed Magic Penetration Shard）
            - MS: 移动速度碎片（Move Speed Shard）
            - HPSZ: 生命值与体型碎片（Health and Size Shard）
            - CSD: 暴击伤害碎片（Critical Damage Shard）
            - OMV: 全能吸血碎片（Omnivamp Shard）
            - TNC: 韧性碎片（Tenacity Shard）
            - HSP: 治疗与护盾强度碎片（Heal & Shield Power Shard）
            - AMP: 护甲穿透碎片（Armor Penetration Shard）
            - MRPP: 百分比法术穿透碎片（Pencentage Magic Penetration Shard）
            - Hybrid1: 迅捷碎片（Swiftness Shard）
            - Hybrid2: 力量碎片（Might Shard）
            - Hybrid3: 坚不可摧碎片（Unbreakable Shard）
            - Random: 两个随机碎片（Two Random Shards）
            - Gold: 好运碎片（Fortune Shard）
            - GoldRoundLoss: 关爱包裹（Care Package）
            - Pristine: 碎片增幅碎片（Shardholder Value Shard）
            - UpgradeShards: 碎片增幅碎片（Shardholder Value Shard）
            - ShardBladeAnvils: 打磨碎片之刃（Hone Shardblade）
        :type selection: dict[str, bool]
        :return: 状态码。<br>Status code.
        
            - 0: 导入成功。<br>Import succeeded.
            - 1: 导入失败。<br>Import failed.
        :rtype: int
        '''
        return self.increment(selection, elementId_map = self.anvilId_map)
    
    def parse(self, timeline_text: str, useInternalName: bool = False, locale: Locale = "zh_CN", version: int = 2) -> None:
        '''
        从一段时间轴文本中加载属性锻造器时间序列信息。<br>Load stat anvil sequence from a piece of timeline text.
        
        :param timeline_text: 时间轴文本。<br>Timeline text.
        
            一个可用的示例见`export`方法。<br>See `export` method for an available example.
        :type timeline_text: str
        :param useInternalName: 是否将属性锻造器的标识符识别为内部代码。默认为假。<br>Whether to identify the stat anvil as an internal code. False by default.
        
            当指定该参数为真时，用户需要输入属性锻造器的简写。例如：AH。<br>When this parameter is specified as True, the user needs to input the abbreviation of stat anvils. For example: AH.
            
            当指定该参数为假时，用户需要输入属性锻造器的全称。例如：技能急速碎片。<br>When this parameter is specified as False, the user needs to input the whole name of stat anvils. For example: Ability Haste Shard.
        :type useInternalName: bool
        :param locale: 时间轴文本的语言文化代码。决定使用哪个正则表达式来识别位阶和属性锻造器类型。<br>Language code of the timeline text, which determines which regular expression will be used to identify tier and stat anvil type.
        :type locale: Literal["en_US", "zh_CN"]
        :param version: （已弃用）时间轴文本格式版本。<br>(Deprecated) Version of the timeline text format.
        
            - 1: 属性锻造器提供随机数值。此时每个属性锻造器应备注其实际取值。<br>Stat anvil grants random value. In that case, each stat anvil should have a note of its actual value.
            - 2: 属性锻造器提供固定数值。<br>Stat anvil grants fixed value.
        :type version: int
        '''
        #准备正则表达式（Prepare regular expressions）
        _sFloat: str = r"-?\d*\.\d+"
        _sInteger: str = r"-?\d+"
        _sNumber: str = f"(?:(?:{_sFloat})|(?:{_sInteger}))"
        NAME_CHAR_MIDDLE_ZH: str = "[^（）]" #既然括号是用于分隔语境的，那么这种情况下括号可被视为一个元字符。这要求名称中不出现元字符。这是十分合理的（Since the Chinese brackets are used to separate context - capture groups, in this case they can be considered as metacharacters. This requires metacharacters not to appear in a name, which is very reasonable）
        NAME_CHAR_SIDE_ZH: str = "[^（） ]" #因为空格作为分隔符，所以规定名称不能以空格作为首尾字符（Since spaces are used as delimiters, names aren't permitted to begin or end with a space）
        NAME_CHAR_ZH: str = f"(?:(?:{NAME_CHAR_SIDE_ZH}{NAME_CHAR_MIDDLE_ZH}*{NAME_CHAR_SIDE_ZH})|{NAME_CHAR_SIDE_ZH})"
        NAME_CHAR_MIDDLE_EN: str = r"[^\(\)]"
        NAME_CHAR_SIDE_EN: str = r"[^\(\) ]"
        NAME_CHAR_EN: str = f"(?:(?:{NAME_CHAR_SIDE_EN}{NAME_CHAR_MIDDLE_EN}*{NAME_CHAR_SIDE_EN})|{NAME_CHAR_SIDE_EN})"
        PICKED_SYMBOL_ZH: str = "（√）"
        PICKED_SYMBOL_EN: str = r"\(√\)"
        sRecordZH: str = rf"（(?P<index>\d+)）\s*（(?P<source>{NAME_CHAR_ZH})）\s*（(?P<tier>{NAME_CHAR_ZH})）\s*(?P<anvil1>{NAME_CHAR_ZH})\s*(（(?P<anvil1value>{_sNumber})）)?\s*(?P<anvil1picked>{PICKED_SYMBOL_ZH})?\s*、\s*(?P<anvil2>{NAME_CHAR_ZH})\s*(（(?P<anvil2value>{_sNumber})）)?\s*(?P<anvil2picked>{PICKED_SYMBOL_ZH})?\s*、\s*(?P<anvil3>{NAME_CHAR_ZH})\s*(（(?P<anvil3value>{_sNumber})）)?\s*(?P<anvil3picked>{PICKED_SYMBOL_ZH})?"
        sRecordEN: str = rf"\((?P<index>\d+)\)\s*\((?P<source>{NAME_CHAR_EN})\)\s*\((?P<tier>{NAME_CHAR_EN})\)\s*(?P<anvil1>{NAME_CHAR_EN})\s*(\((?P<anvil1value>{_sNumber})\))?\s*(?P<anvil1picked>{PICKED_SYMBOL_EN})?\s*,\s*(?P<anvil2>{NAME_CHAR_EN})\s*(\((?P<anvil2value>{_sNumber})\))?\s*(?P<anvil2picked>{PICKED_SYMBOL_EN})?\s*,\s*(?P<anvil3>{NAME_CHAR_EN})\s*(\((?P<anvil3value>{_sNumber})\))?\s*(?P<anvil3picked>{PICKED_SYMBOL_EN})?"
        pRecordZH: re.Pattern[str] = re.compile(sRecordZH)
        pRecordEN: re.Pattern[str] = re.compile(sRecordEN)
        pRecord: re.Pattern[str] = pRecordZH if locale == "zh_CN" else pRecordEN
        #准备一些对应关系，用于规范用户输入的名称的大小写（Prepare some mappings to normalize the case of names from user input）
        tier_match_map: dict[str, str] = {value[locale]: key for key, value in self.TIER_STRINGTABLE.items()} #从位阶的本地化文本到位阶代码的映射（The reflection from tier localized text to tier code）
        anvilSource_match_map: dict[str, str] = {value[locale]: key for key, value in self.ANVILSOURCE_STRINGTABLE.items()} #从属性锻造器来源本地化文本到来源主键的映射（The reflection from stat anvil source's localized text to source key）
        anvilType_match_map: dict[str, str] = {value[locale]: key for key, value in self.ANVILTYPE_STRINGTABLE.items()} #从属性锻造器类型本地化文本到类型代码的映射（The reflection from stat anvil type localized text to type code）
        ##注意到此时`anvilType_match_map`键中含有“固定法术穿透碎片”和“百分比法术穿透碎片”两个键。这样的话，当用户输入这两个字符串作为属性锻造器的名称时，程序可以正确地将其转化为相应的锻造器代码（Note that here "Fixed Magic Penetration Shard" and "Percentage Magic Penetration Shard" exist in `anvilType_match_map`. In that case, when the user inputs these two strings as the stat anvil's name, the program can correctly transform it into the correponding anvilId）
        #判断属性锻造器标识合法性（Judge the validity of the stat anvil identifier）
        def isValidAnvilTier(anvil_tier: str) -> bool:
            '''
            判断用户输入的属性锻造器位阶是否有效。<br>Judge whether the stat anvil's tier from user input is valid.
            
            :param anvil_tier: 属性锻造器的位阶。<br>The tier of a stat anvil.
            :type anvil_tier: str
            :return: 属性锻造器的来源的有效性。<br>Validity of the stat anvil's source.
            :rtype: bool
            '''
            return useInternalName and (anvil_tier.isdigit() and int(anvil_tier) in self.VALID_TIERS_INT or anvil_tier.lower() in self.TIER_CASE_MAP) or not useInternalName and anvil_tier in tier_match_map
        
        def isValidAnvilSource(anvil_source: str) -> bool:
            '''
            判断用户输入的属性锻造器来源是否有效。<br>Judge whether the stat anvil's source from user input is valid.
            
            :param anvil_source: 属性锻造器的来源。<br>The source of a stat anvil.
            :type anvil_source: str
            :return: 属性锻造器的来源的有效性。<br>Validity of the stat anvil's source.
            :rtype: bool
            '''
            return useInternalName and anvil_source.lower() in self.ANVILSOURCE_CASE_MAP or not useInternalName and anvil_source in anvilSource_match_map
        
        def isValidAnvilName(anvil_name: str) -> bool:
            '''
            判断用户输入的属性锻造器的名称是否有效。<br>Judge whether the stat anvil's name from user input is valid.
            
            :param anvil_name: 属性锻造器的名称。<br>The name of a stat anvil.
            :type anvil_name: str
            :return: 属性锻造器的名称的有效性。<br>Validity of the stat anvil's name.
            :rtype: bool
            '''
            return useInternalName and (anvil_name == "MRP" or anvil_name.lower() in self.ANVILTYPE_CASE_MAP) or not useInternalName and (anvil_name in anvilType_match_map or locale == "en_US" and anvil_name == "Magic Penetration Shard" or locale == "zh_CN" and anvil_name == "法术穿透碎片") #固定法术穿透碎片和百分比法术穿透碎片的名字都是“法术穿透碎片”。必须要处理这一个特例（Both Fixed Magic Penetration Shard and Percentage Magic Penetration Shard use the name "Magic Penetration Shard". This special case must be discussed individually）
        #词法分析（Parse）
        selections: list[Selection] = []
        recordLines: list[str] = timeline_text.splitlines()
        for i, recordLine in enumerate(recordLines):
            if matchObj := pRecord.search(recordLine):
                groups: dict[str, Any] = matchObj.groupdict()
                rarity: str = groups["tier"] #位阶（Tier）
                anvil_names: list[str] = [groups["anvil1"], groups["anvil2"], groups["anvil3"]] #各属性锻造器的本地化名称（Each stat anvil's localized name）
                anvils_picked: list[bool] = [groups.get("anvil1picked") is not None, groups.get("anvil2picked") is not None, groups.get("anvil3picked") is not None] #各属性锻造器是否被选择（Whether each stat anvil is picked）
                anvil_values: list[float] = [float(groups.get("anvil1value") or 0), float(groups.get("anvil2value") or 0), float(groups.get("anvil3value") or 0)] #未识别到属性锻造器的取值时，则使用or右边的值（When the value of a stat anvil isn't identified, the value to the right of "or" is used）
                source: str = groups["source"] #属性锻造器选择界面来源（Source of the stat anvil selection screen）
                if isValidAnvilTier(rarity) and sum(anvils_picked) <= 1 and all(map(isValidAnvilName, anvil_names)) and isValidAnvilSource(source):
                    #动作（Action）
                    action: str = "select" if sum(anvils_picked) == 1 else "supply"
                    #位阶（Tier）
                    if useInternalName:
                        if rarity.isdigit():
                            tier: str = self.TIER_MAP[int(rarity)]
                        else:
                            tier = self.TIER_CASE_MAP[rarity.lower()]
                    else:
                        tier = tier_match_map[rarity]
                    #选项（Options）
                    options_supply: list[Option] = []
                    options_select: list[Option] = []
                    for j, anvil_name in enumerate(anvil_names):
                        #选项识别码（Option id）
                        if useInternalName:
                            if anvil_name == "MRP":
                                anvil_id: str = "MRPP" if tier == "Prismatic" else "MRPF"
                            else:
                                anvil_id = self.ANVILTYPE_CASE_MAP[anvil_name.lower()]
                        else:
                            if anvil_name in {"法术穿透碎片", "Magic Penetration Shard"}:
                                anvil_id = "MRPP" if tier == "Prismatic" else "MRPF"
                            else:
                                anvil_id = anvilType_match_map[anvil_name]
                        option_supply: Option = {"id": anvil_id}
                        option_select: Option = {"id": anvil_id}
                        #已选择状态（Picked status）
                        if anvils_picked[j]:
                            option_select["picked"] = True
                        #取值（Value）
                        if anvil_values[j] != 0: #只在属性锻造器的数值不是0时添加值字段（Add "value" field only when the value of the stat anvil isn't 0）
                            option_supply["value"] = anvil_values[j]
                            option_select["value"] = anvil_values[j]
                        #追加（Append）
                        options_supply.append(option_supply)
                        options_select.append(option_select)
                    #来源（Source）
                    if useInternalName:
                        sourceKey: str = self.ANVILSOURCE_CASE_MAP[source.lower()]
                    else:
                        sourceKey = anvilSource_match_map[source]
                    #赋值（Assignment）
                    selection_supply: Selection = {
                        "action": "supply",
                        "tier": tier,
                        "selections": options_supply,
                        "source": sourceKey
                    }
                    selection_select: Selection = {
                        "action": "select",
                        "tier": tier,
                        "selections": options_select,
                        "source": sourceKey
                    }
                    selections.append(selection_supply)
                    if action == "select":
                        selections.append(selection_select)
                else:
                    if not isValidAnvilTier(rarity):
                        print(f"第{i + 1}行位阶不正确。\nIncorrect tier in Line {i + 1}.")
                    if sum(anvils_picked) > 1:
                        print("第%d行选择行为错误。应选择1个选项，实际选择%d个选项。\nWrong selection behavior of Line %d. Expected 1 option selected but received %d options selected." %(i + 1, sum(anvils_picked), i + 1, sum(anvils_picked)))
                    unidentified_anvil_names: list[str] = [_ for _ in anvil_names if not isValidAnvilName(_)]
                    if len(unidentified_anvil_names) > 0:
                        print("第%d行中以下属性锻造器不存在：\nStat anvils not found in Line %d:\n%s" %(i + 1, i + 1, str(unidentified_anvil_names).replace("'", '"')))
                    if not isValidAnvilSource(source):
                        print(f"第{i + 1}行来源不正确。\nIncorrect source in Line {i + 1}.")
        self.extend(selections, elementId_map = None)
    
    def export_timeline(self, useInternalName: bool = False, useIntegerTier: bool = False, locale: Locale = "zh_CN", version: int = 2) -> str:
        '''
        将属性锻造器时间序列导出为适用于时间轴文本文档中的字符串。<br>Export the stat anvil sequence into a long string used in a timeline text file.
        
        例如：（1）（属性叠属性！）（白银阶）穿甲碎片、攻击速度碎片、生命值碎片（√）<br>For example: (1) (Stats on Stats!) (Silver) Lethality Shard, Attack Speed Shard, Health Shard (√)
        
        需要指出，这个方法和`parse`方法互为逆运算。<br>It's worthy of a note that this method is an inverse operation of `parse` method.
        
        :param useInternalName: 是否将属性锻造器的标识符识别为内部代码。默认为假。<br>Whether to identify the stat anvil as an internal code. False by default.
        
            当指定该参数为真时，将属性锻造器导出为简写。例如：AH。<br>When this parameter is specified as True, stat anvils will be exported in abbreviated form. For example: AH.
            
            当指定该参数为假时，将属性锻造器导出为全名。例如：技能急速碎片。<br>When this parameter is specified as False, stat anvils will be exported into whole names. For example: Ability Haste Shard.
        :type useInternalName: bool
        :param useIntegerTier: 在将位阶导出为内部代码时，是否使用整数来表示。默认为假。<br>When tiers are exported into internal code, whether to represent them as integers. False by default.
        
            这个参数只在`useInternalName`参数指定为真时才发挥作用。<br>Only when `useInternalName` parameter is set to True will this parameter make a difference.
        :type useIntegerTier: bool
        :param locale: 时间轴文本的语言文化代码。<br>Language code of the timeline text.
        :type locale: Literal["en_US", "zh_CN"]
        :param version: （已弃用）时间轴文本格式版本。<br>(Deprecated) Version of the timeline text format.
        
            - 1: 属性锻造器提供随机数值。此时每个属性锻造器应备注其实际取值。<br>Stat anvil grants random value. In that case, each stat anvil should have a note of its actual value.
            - 2: 属性锻造器提供固定数值。<br>Stat anvil grants fixed value.
        :type version: int
        :return: 属性锻造器时间轴字符串。<br>A stat anvil timeline string.
        :rtype: str
        '''
        PICKED_SYMBOL: str = "（√）" if locale == "zh_CN" else " (√)"
        TIER_MAP: dict[str, int] = {value: key for key, value in self.TIER_MAP.items()} #交换位阶映射的键值对（Exchange the keys and values of tier mapping）
        result: str = "" #初始化结果字符串（Initialize the result string）
        for i, selection in enumerate(self.selections):
            if selection["action"] != "select" and i != len(self.selections) - 1: #导出结果时，将供应和选择行为导出为一行。同时，如果最后一条记录是供应行为，也应单独导出，例如在水晶枢纽爆炸时购买了一个属性锻造器但是没有选择。这要求原始数据是合理的（When the program is going to export the result, the supply and select actions should be exported into one line. Meanwhile, if the final record is a supply action, it should also be exported, for example a player buys a stat anvil but never select it even if the Nexus explodes. This requires the source data are legal）
                continue
            #序号（Index）
            index: int = i // 2 + 1
            #来源（Source）
            sourceKey: str = selection["source"]
            source: str = sourceKey if useInternalName else self.ANVILSOURCE_STRINGTABLE[sourceKey][locale]
            #位阶（Tier）
            tier: str = selection.get("tier", "Silver") #如果真的出现了选择界面和选项中都没有指定位阶的情形，则认为是白银阶。但是这个情形是不可能发生的。换言之，这个get方法只是为了应对严格的类型检查模式（If the case where neither the selection screen nor the options specify the tier, then the program considers that the tier is silver. However, this case can't happen. In other words, this get method is just meant for the strict type checking mode）
            if useInternalName:
                if useIntegerTier:
                    rarity: str = str(TIER_MAP[tier])
                else:
                    rarity = tier
            else:
                rarity = self.TIER_STRINGTABLE[tier][locale]
            #属性锻造器1（Stat anvil 1）
            anvil1: Option = selection["selections"][0]
            anvil1_id: str = anvil1["id"]
            if useInternalName:
                if anvil1_id == "MRPF" or anvil1_id == "MRPP":
                    anvil1_name: str = "MRP"
                else:
                    anvil1_name = anvil1_id
            else:
                if anvil1_id == "MRPF" or anvil1_id == "MRPP":
                    anvil1_name = "法术穿透碎片" if locale == "zh_CN" else "Magic Penetration Shard"
                else:
                    anvil1_name = self.ANVILTYPE_STRINGTABLE[anvil1_id][locale]
            anvil1_value: float = anvil1.get("value", 0)
            anvil1_value_str: str = "" if anvil1_value == 0 else f"（{anvil1_value}）" if locale == "zh_CN" else f" ({anvil1_value})"
            anvil1_picked: bool = anvil1.get("picked", False)
            anvil1_picked_str: str = PICKED_SYMBOL if anvil1_picked else ""
            #属性锻造器2（Stat anvil 2）
            anvil2: Option = selection["selections"][1]
            anvil2_id: str = anvil2["id"]
            if useInternalName:
                if anvil2_id == "MRPF" or anvil2_id == "MRPP":
                    anvil2_name: str = "MRP"
                else:
                    anvil2_name = anvil2_id
            else:
                if anvil2_id == "MRPF" or anvil2_id == "MRPP":
                    anvil2_name: str = "法术穿透碎片" if locale == "zh_CN" else "Magic Penetration Shard"
                else:
                    anvil2_name = self.ANVILTYPE_STRINGTABLE[anvil2_id][locale]
            anvil2_value: float = anvil2.get("value", 0)
            anvil2_value_str: str = "" if anvil2_value == 0 else f"（{anvil2_value}）" if locale == "zh_CN" else f" ({anvil2_value})"
            anvil2_picked: bool = anvil2.get("picked", False)
            anvil2_picked_str: str = PICKED_SYMBOL if anvil2_picked else ""
            #属性锻造器3（Stat anvil 3）
            anvil3: Option = selection["selections"][2]
            anvil3_id: str = anvil3["id"]
            if useInternalName:
                if anvil3_id == "MRPF" or anvil3_id == "MRPP":
                    anvil3_name: str = "MRP"
                else:
                    anvil3_name = anvil3_id
            else:
                if anvil3_id == "MRPF" or anvil3_id == "MRPP":
                    anvil3_name: str = "法术穿透碎片" if locale == "zh_CN" else "Magic Penetration Shard"
                else:
                    anvil3_name = self.ANVILTYPE_STRINGTABLE[anvil3_id][locale]
            anvil3_value: float = anvil3.get("value", 0)
            anvil3_value_str: str = "" if anvil3_value == 0 else f"（{anvil3_value}）" if locale == "zh_CN" else f" ({anvil3_value})"
            anvil3_picked: bool = anvil3.get("picked", False)
            anvil3_picked_str: str = PICKED_SYMBOL if anvil3_picked else ""
            #赋值（Assignment）
            if locale == "zh_CN":
                record: str = f"（{index}）（{source}）（{rarity}）{anvil1_name}{anvil1_value_str}{anvil1_picked_str}、{anvil2_name}{anvil2_value_str}{anvil2_picked_str}、{anvil3_name}{anvil3_value_str}{anvil3_picked_str}"
            else:
                record = f"({index}) ({source}) ({rarity}) {anvil1_name}{anvil1_value_str}{anvil1_picked_str}, {anvil2_name}{anvil2_value_str}{anvil2_picked_str}, {anvil3_name}{anvil3_value_str}{anvil3_picked_str}"
            result += record + "\n"
        return result
    
    def organize_anvil_data(self, index: int = -1) -> dict[str, dict[str, dict[str, Any]]]:
        '''
        将某个属性锻造器快照进一步加工成一个另一个Python字典，以供`export_clip`方法使用。<br>Further process a stat anvil snapshot into another Python dictionary to be used by `export_clip` method.
        
        :param index: 快照下标。取值范围是`[-self.snapshot_count, self.snapshot_count - 1]`内的整数。<br>The index of the snapshot. Should be within `[-self.snapshot_count, self.snapshot_count - 1]` range.
        
            如果未指定，则处理当前状态。<br>If it's not specified, this function will try to organize the current status by default.
        :type index: int
        :return: 用于输出为文本的属性锻造器数据。<br>Stat anvil data to be output as a text.
        
            一级键是位阶。二级键是锻造器类型。三级键值对是锻造器相关字段。<br>Each Level-1 key is a tier. Each Level-2 key is an anvil type. Each Level-3 key-value pair is an anvil field.
        :rtype: dict[str, dict[str, dict[str, Any]]]
        '''
        counter: dict[str, dict[str, dict[str, int | float]]] = self.sequence[index]
        anvil_block: dict[str, dict[str, dict[str, Any]]] = {
            tier: {
                anvilId: {
                    "desc_zh": "法术穿透碎片" if anvilId == "MRPF" or anvilId == "MRPP" else self.ANVILTYPE_STRINGTABLE[anvilId]["zh_CN"], #这里期望使用游戏内显示的名称，所以对这两类属性锻造器进行特殊处理（Here I expect the name practically used in game is displayed, so special handling is performed for these two types of stat anvils）
                    "desc_en": "Magic Penetration Shard" if anvilId == "MRPF" or anvilId == "MRPP" else self.ANVILTYPE_STRINGTABLE[anvilId]["en_US"],
                    "supply_count": counter[tier][anvilId]["supplyCount"],
                    "select_count": counter[tier][anvilId]["selectCount"]
                } for anvilId in self.VALID_TYPES[tier]
            } for tier in ["Silver", "Gold", "Prismatic"]
        }
        return anvil_block
    
    def export_clip(self, index: int = -1, mode: str = "cherry", highlight_change: bool = True) -> tuple[str, list[str], list[int]]:
        '''
        将属性锻造器时间序列中的各个时刻的计数导出为适用于Premiere Pro中的一个文本框剪辑的快照字符串。这个字符串包含所有属性锻造器类型和数量，并通过空格和制表位进行排版。<br>Export the count at each point in the stat anvil sequence into a snapshot string used in a textbox clip in Premiere Pro, which contains the type and the number of all stat anvil types and is inserted with spaces and tabs to beautify the output.
        
        :param index: 快照下标。取值范围是`[-self.snapshot_count, self.snapshot_count - 1]`内的整数。<br>The index of the snapshot. Should be within `[-self.snapshot_count, self.snapshot_count - 1]` range.
        
            如果未指定，则默认导出最近一次选择。<br>If it's not specified, this function will try to export the latest selection by default.
        :type index: int
        :param mode: 游戏模式。决定要导出的属性锻造器字段。包含以下取值：<br>Game mode, which determines the stat anvil fields to export. It supports the following values:
        
            - cherry: （☆）斗魂竞技场。<br>Arena.
            - kiwi: 海克斯大乱斗。<br>ARAM: Mayhem.
        :type mode: Literal["cherry", "kiwi"]
        :param highlight_change: 是否高亮显示变化。默认为真。<br>Whether to highlight all changed numbers. True by default.
        
            如果置为真，则将每个变化的数字单独设置为一个格式运行单位。否则将整个位阶的文本设置为一个格式运行单位。<br>If it's True, then set each changed number as a format run unit. Otherwise, the text of the whole tier is set as a single format run unit.
        :type highlight_change: bool
        :return: 一个三元组。<br>A three-tuple.
        
            - 属性锻造器数量统计表文本。<br>Stat anvil statistics text.
            - 格式列表。<br>Format list.
            - 每个格式运行单位的长度数组。<br>A run length array, composed of each format run unit.
            
            这个运行长度数组用于Premiere Pro的格式范围。<br>This run length array is used as the ranges of formats in Premiere Pro.
        :rtype: tuple[str, list[int]]
        '''
        #参数预处理（Parameter preprocessing）
        if index < - self.snapshot_count or index >= self.snapshot_count:
            print("下标越界。\nIndex out of bounds.")
            return ("", [], [])
        if mode == "kiwi":
            anvilTypes_silver: set[str] = {"AH", "AD", "AP", "Hybrid2", "AM", "MR", "Hybrid3", "HP", "AS", "Hybrid1", "CSC", "LTH", "MRPF"}
            anvilTypes_gold: set[str] = {"AH", "AD", "AP", "Hybrid2", "AM", "MR", "Hybrid3", "HP", "AS", "Hybrid1", "CSC", "LTH", "MRPF"}
            anvilTypes_prismatic: set[str] = {"MS", "HPSZ", "OMV", "TNC", "HSP", "AMP", "MRPP"}
        else:
            anvilTypes_silver = set(self.VALID_SILVER_TYPES)
            anvilTypes_gold = set(self.VALID_GOLD_TYPES)
            anvilTypes_prismatic = set(self.VALID_PRISMATIC_TYPES)
        anvilTypes: dict[str, set[str]] = {"Silver": anvilTypes_silver, "Gold": anvilTypes_gold, "Prismatic": anvilTypes_prismatic} #和`export_counter`方法不同，该方法中`anvilTypes`仅用于执行条件判断，没有顺序的要求，所以用集合加快检索速度（Different `export_counter` method, here `anvilTypes` is only used for condition judgment and doesn't require order, so set is used to accelerate query speed）
        #准备一些常量（Prepare some constants）
        if self.selection_count == 0 or index == 0: #如果是最初的快照，则没有做出任何选择（If the user chooses to export the initial snapshot, then no selection had been made yet）
            phase: str = "initial" #可初始化为任意值（Can be initialized as any value）
            current_tier: str = ""
            current_anvilType_selected: str = ""
            anvilTypes_supplied: tuple[str, ...] = ("", "", "")
        else:
            selection_index: int = index if index < 0 else index - 1 #时间序列中包含原始快照，因此其长度比选择列表大1（The sequence contains the initial snapshot, so its length is greater than the selection list by 1）
            current_selection: Selection = self.selections[selection_index]
            phase = current_selection["action"]
            current_tier = current_selection.get("tier", "Silver")
            current_anvilType_selected = ""
            for option in current_selection["selections"]:
                if option.get("picked", False):
                    current_anvilType_selected = option["id"]
                    break #这要求最多只有一个属性锻造器被选择（This requires at most one stat anvil is selected）
            anvilTypes_supplied = tuple(map(lambda x: x["id"], current_selection["selections"]))
        #构建文本（Construct the text and the run length array）
        ##标题和表头（Title and header）
        title_line: str = "<b>              属性锻造器数量统计表"
        header_line: str = "\r位阶\t属性锻造器类别\t数量</b>"
        ##表格主体（Table body）
        anvil_block: dict[str, dict[str, dict[str, Any]]] = self.organize_anvil_data(index = index)
        ###白银阶（Silver）
        silver_block: str = "<normal>" #normal标签为自定义标签，表示不添加任何格式（"normal" tag is a custom tag, which means no format is added）
        silver_append_counter: int = 0
        for (anvilType, anvilData) in anvil_block["Silver"].items():
            if "Silver" in anvilTypes and not anvilType in anvilTypes["Silver"]:
                continue
            #行首（Line header）
            if silver_append_counter == 0:
                silver_header: str = "白银阶" #存储白银阶属性锻造器区块的行首字符串（Store the line header string in the silver stat anvil block）
            elif silver_append_counter == 1:
                supplied_anvil_count: int = sum(map(lambda x: x["supply_count"], anvil_block["Silver"].values())) // 3 #已选择的锻造器数量可能少1（The number of selected stat anvils may be one less）
                if supplied_anvil_count == 0:
                    silver_header: str = ""
                else:
                    if current_tier == "Silver" and highlight_change and phase == "supply": #仅在弹出白银阶属性锻造器选择界面时，设置白银阶属性锻造器总数的格式（Only when a silver stat anvil selection screen pops up, set the default format of the total number of silver stat anvils）
                        if supplied_anvil_count == 1:
                            silver_header = "</normal><green>" + f"({supplied_anvil_count})" + "</green><normal>" #<green> = <font color=#00ff00>
                        else:
                            silver_header = "(</normal><green>" + str(supplied_anvil_count) + "</green><normal>)"
                    else:
                        silver_header = f"({supplied_anvil_count})"
            else:
                silver_header = ""
            #锻造器选取比例（Anvil selection ratio）
            if anvilData["select_count"] == 0 and anvilData["supply_count"] == 0: #未出现过的锻造器类型不显示数字（Anvil types that haven't appeared don't display）
                select_ratio_str: str = ""
            else:
                ##已选锻造器数量（Number of selected anvils）
                if current_tier == "Silver" and anvilType == current_anvilType_selected and highlight_change and phase == "select":
                    select_count_str: str = "</normal><green>" + str(anvilData["select_count"]) + "</green><normal>"
                else:
                    select_count_str = str(anvilData["select_count"])
                ##提供锻造器数量（Number of supplied anvils）
                if current_tier == "Silver" and anvilType in anvilTypes_supplied and highlight_change and phase == "supply":
                    supply_count_str: str = "</normal><green>" + str(anvilData["supply_count"]) + "</green><normal>"
                else:
                    supply_count_str = str(anvilData["supply_count"])
                select_ratio_str = "%s/%s" %(select_count_str, supply_count_str)
            #汇总（Aggregate）
            silver_block += "\r%s\t    %s%s\t%s" %(silver_header, anvilData["desc_zh"], "" if len(anvilData["desc_zh"]) > 4 else "\t", select_ratio_str)
            silver_append_counter += 1
        silver_block += "</normal>"
        ###黄金阶（Gold）
        gold_block: str = "<yellow>" #<yellow> = <font color=#ffff00>
        gold_append_counter: int = 0
        for (anvilType, anvilData) in anvil_block["Gold"].items():
            if "Gold" in anvilTypes and not anvilType in anvilTypes["Gold"]:
                continue
            #行首（Line header）
            if gold_append_counter == 0:
                gold_header: str = "黄金阶" #存储黄金阶属性锻造器区块的行首字符串（Store the line header string in the gold stat anvil block）
            elif gold_append_counter == 1:
                supplied_anvil_count: int = sum(map(lambda x: x["supply_count"], anvil_block["Gold"].values())) // 3
                if supplied_anvil_count == 0:
                    gold_header: str = ""
                else:
                    if current_tier == "Gold" and highlight_change and phase == "supply": #仅在弹出黄金阶属性锻造器选择界面时，设置黄金阶属性锻造器总数的格式（Only when a gold stat anvil selection screen pops up, set the default format of the total number of gold stat anvils）
                        if supplied_anvil_count == 1:
                            gold_header = "</yellow><green>" + f"({supplied_anvil_count})" + "</green><yellow>"
                        else:
                            gold_header = "(</yellow><green>" + str(supplied_anvil_count) + "</green><yellow>)"
                    else:
                        gold_header = f"({supplied_anvil_count})"
            else:
                gold_header = ""
            #锻造器选取比例（Anvil selection ratio）
            if anvilData["select_count"] == 0 and anvilData["supply_count"] == 0:
                select_ratio_str: str = ""
            else:
                #已选锻造器数量（Number of selected anvils）
                if current_tier == "Gold" and anvilType == current_anvilType_selected and highlight_change and phase == "select":
                    select_count_str: str = "</yellow><green>" + str(anvilData["select_count"]) + "</green><yellow>"
                else:
                    select_count_str = str(anvilData["select_count"])
                #提供锻造器数量（Number of supplied anvils）
                if current_tier == "Gold" and anvilType in anvilTypes_supplied and highlight_change and phase == "supply":
                    supply_count_str: str = "</yellow><green>" + str(anvilData["supply_count"]) + "</green><yellow>"
                else:
                    supply_count_str = str(anvilData["supply_count"])
                select_ratio_str = "%s/%s" %(select_count_str, supply_count_str)
            #汇总（Aggregate）
            gold_block += "\r%s\t    %s%s\t%s" %(gold_header, anvilData["desc_zh"], "" if len(anvilData["desc_zh"]) > 4 else "\t", select_ratio_str)
            gold_append_counter += 1
        gold_block += "</gold>"
        ###棱彩阶（Prismatic）
        prismatic_block: str = "<purple>" #<purple> = <font color=#ff00ff>
        prismatic_append_counter: int = 0
        for (anvilType, anvilData) in anvil_block["Prismatic"].items():
            if "Prismatic" in anvilTypes and not anvilType in anvilTypes["Prismatic"]:
                continue
            #行首（Line header）
            if prismatic_append_counter == 0:
                prismatic_header: str = "棱彩阶" #存储棱彩阶属性锻造器区块的行首字符串（Store the line header string in the prismatic stat anvil block）
            elif prismatic_append_counter == 1:
                supplied_anvil_count: int = sum(map(lambda x: x["supply_count"], anvil_block["Prismatic"].values())) // 3
                if supplied_anvil_count == 0:
                    prismatic_header: str = ""
                else:
                    if current_tier == "Prismatic" and highlight_change and phase == "supply": #仅在弹出棱彩阶属性锻造器选择界面时，设置棱彩阶属性锻造器总数的格式（Only when a prismatic stat anvil selection screen pops up, set the default format of the total number of prismatic stat anvils）
                        if supplied_anvil_count == 1:
                            prismatic_header = "</purple><green>" + f"({supplied_anvil_count})" + "</green><purple>"
                        else:
                            prismatic_header = "(</purple><green>" + str(supplied_anvil_count) + "</green><purple>)"
                    else:
                        prismatic_header = f"({supplied_anvil_count})"
            else:
                prismatic_header = ""
            #锻造器选取比例（Anvil selection ratio）
            if anvilData["select_count"] == 0 and anvilData["supply_count"] == 0:
                select_ratio_str: str = ""
            else:
                #已选锻造器数量（Number of selected anvils）
                if current_tier == "Prismatic" and anvilType == current_anvilType_selected and highlight_change and phase == "select":
                    select_count_str: str = "</purple><green>" + str(anvilData["select_count"]) + "</green><purple>"
                else:
                    select_count_str = str(anvilData["select_count"])
                #提供锻造器数量（Number of supplied anvils）
                if current_tier == "Prismatic" and anvilType in anvilTypes_supplied and highlight_change and phase == "supply":
                    supply_count_str: str = "</purple><green>" + str(anvilData["supply_count"]) + "</green><purple>"
                else:
                    supply_count_str = str(anvilData["supply_count"])
                select_ratio_str = "%s/%s" %(select_count_str, supply_count_str)
            #汇总（Aggregate）
            prismatic_block += "\r%s\t    %s%s\t%s" %(prismatic_header, anvilData["desc_zh"], "" if len(anvilData["desc_zh"]) > 4 else "\t", select_ratio_str)
            prismatic_append_counter += 1
        prismatic_block += "</purple>"
        anvilTable: str = title_line + header_line + silver_block + gold_block + prismatic_block
        # anvilTable = anvilTable.replace("\n", "\r") #将换行符转换成回车符，以便正则表达式识别。因为元字符“.”不识别换行符（Replace line feed characters by carriage returns for the sake of regex identification, for the metacharacter "." doesn't identify the line feed character）
        #构建运行长度数组（Build the run length array）
        CSS_tag: str = r"[\s\w=#\'\"@\-\.]*"
        sFormat_start: str = f"<(?P<tag>{CSS_tag})>"
        sFormat_end: str = f"</{CSS_tag}>"
        sFormatText: str = sFormat_start + "(?P<text>.*?)" + sFormat_end #贪婪模式求最小匹配（Use greedy mode to get the smallest match）
        pFormatText: re.Pattern[str] = re.compile(sFormatText)
        formatArray: list[str] = [matchObj.group("tag") for matchObj in pFormatText.finditer(anvilTable)]
        style_runLengthArray: list[int] = [len(matchObj.group("text")) for matchObj in pFormatText.finditer(anvilTable)]
        #最后移除所有CSS标签（Finally, remove all CSS tags）
        # sFormat: str = r"<(?P<conclude>/?)(?P<tag>[\s\w=#\'\"@\-\.]*)>" #“conclude”标记是不是一段格式的收尾。“tag”标记格式名称（"conclude" marks whether this is the end of a style. "tag" marks the style name）
        sFormat: str = r"</?[\s\w=#\'\"@\-\.]*>"
        pFormat: re.Pattern[str] = re.compile(sFormat)
        anvilTable = pFormat.sub("", anvilTable)
        return (anvilTable, formatArray, style_runLengthArray)
    
    def copy_counter_PR(self, begIndex: int = 0, mode: str = "cherry", res: str = "1920x1080") -> None:
        '''
        将属性锻造器序列快照复制到剪贴板中。此时可在Premiere Pro软件的文本框中粘贴排版后的属性锻造器快照文本。<br>Copy a stat anvil snapshot into clipboard. Now, users can paste the typeset stat anvil snapshot text into the text box in Premiere Pro application.
        
        由于PR剪贴板的参数太过复杂，用户应当根据自身需求修改该函数的主体。可参考《属性锻造器时间序列处理》Jupyter笔记本。<br>Since parameters PR clipboard are way too complex, users should modify this function's body based on personal demands. Users may refer to "属性锻造器时间序列处理.ipynb".
        
        :param mode: 游戏模式。决定要导出的属性锻造器字段。包含以下取值：<br>Game mode, which determines the stat anvil fields to export. It supports the following values:
        
            - cherry: （☆）斗魂竞技场。<br>Arena.
            - kiwi: 海克斯大乱斗。<br>ARAM: Mayhem.
        :type mode: Literal["cherry", "kiwi"]
        :param begIndex: 遍历快照的起始索引。默认为0。<br>The beginning index to traverse the snapshots. 0 by default.
        
            当程序因异常而退出或者用户误操作时，这个参数能帮助快速进展到最新的状态。<br>When the program exits due to an exception or the user has made a mistake, this parameter is very helpful to quickly progress to the latest status.
        :type begIndex: int
        :param res: 视频分辨率。决定字号和制表位排版。<br>Video resolution, which determines the font size and the layout optimization strategy regarding the number of tabs.
        
            支持以下分辨率：<br>The following resolutions are supported:
            - 1080P: 1920 × 1080
            - 2K: 2560 × 1440
        :type res: Literal["1920x1080", "2560x1440"]
        '''
        #参数预处理（Parameter preprocessing）
        if res != "2560x1440":
            res = "1920x1080"
        #定义配置层（Define the config layer）
        config: dict[str, dict[str, Any]] = {
            "1920x1080": {
                "FontSize": 24.0,
                "Leading": 28.8,
                "TabWidth": 96.0,
                "formatCode": {
                    "normal": "QAEAAAAAAABEMyIRDAAAAAAABgAKAAQABgAAAGQAAAAAAF4AHAAUABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADwAAAAgAAAAAABsABwBeAAAAAAAAARQAAAAAAAABHAAAADQAAAAAAAAAWP///1z///9g////ZP///wEAAAAEAAAADgAAAE1pY3Jvc29mdFlhSGVpAAABAAAADAAAAAgADAAEAAgACAAAAAgAAABAAAAAAQAAAGEANgAYAAAAFAAAAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAwAAAAIAAQANgAAAAIAAAAQAAAAEAAAAAAAgEAAAJBB9P////j////8////BAAEAAQAAAA=",
                    "b": "RAEAAAAAAABEMyIRDAAAAAAABgAKAAQABgAAAGQAAAAAAF4AHAAUABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADwAAAAgAAAAAABsABwBeAAAAAAAAARQAAAAAAAABHAAAADgAAAAAAAAAVP///1j///9c////YP///wEAAAAEAAAAEwAAAE1pY3Jvc29mdFlhSGVpLUJvbGQAAQAAAAwAAAAIAAwABAAIAAgAAAAIAAAAQAAAAAEAAABhADYAGAAAABQAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAMAAAACAAEADYAAAACAAAAEAAAABAAAAAAAIBAAACQQfT////4/////P///wQABAAEAAAA",
                    "green": "WAEAAAAAAABEMyIRDAAAAAAABgAKAAQABgAAAGQAAAAAAF4AHAAUABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADwAAAAgAAAAAABsABwBeAAAAAAAAARQAAAAAAAABHAAAADQAAAAAAAAAXP///2D///9k////aP///wEAAAAEAAAADgAAAE1pY3Jvc29mdFlhSGVpAAABAAAADAAAAAgADAAEAAgACAAAAAgAAABAAAAAAQAAAGEANgAcAAAAGAAUAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAwAAAAIAAQANgAAAAIAAAAUAAAAGAAAAAAAgEAoAAAAAACQQfz///8EAAQABAAAAAQABgAEAAAAAAAKAAgABgAAAAcACgAAAAAAAAA=",
                    "yellow": "WAEAAAAAAABEMyIRDAAAAAAABgAKAAQABgAAAGQAAAAAAF4AHAAUABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADwAAAAgAAAAAABsABwBeAAAAAAAAARQAAAAAAAABHAAAADQAAAAAAAAAXP///2D///9k////aP///wEAAAAEAAAADgAAAE1pY3Jvc29mdFlhSGVpAAABAAAADAAAAAgADAAEAAgACAAAAAgAAABAAAAAAQAAAGEANgAcAAAAGAAUAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAwAAAAIAAQANgAAAAIAAAAUAAAAGAAAAAAAgEAoAAAAAACQQfz///8EAAQABAAAAAQABgAEAAAAAAAKAAgAAAAAAAcACgAAAAAAAAA=",
                    "purple": "UAEAAAAAAABEMyIRDAAAAAAABgAKAAQABgAAAGQAAAAAAF4AHAAUABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADwAAAAgAAAAAABsABwBeAAAAAAAAARQAAAAAAAABHAAAADQAAAAAAAAAWP///1z///9g////ZP///wEAAAAEAAAADgAAAE1pY3Jvc29mdFlhSGVpAAABAAAADAAAAAgADAAEAAgACAAAAAgAAABAAAAAAQAAAGEANgAcAAAAGAAUAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAwAAAAIAAQANgAAAAIAAAAUAAAAFAAAAAAAgEAgAAAAAACQQfj////8////BAAEAAQAAAAIAAgAAAAHAAgAAAAAAAAA"
                }
            },
            "2560x1440": {
                "FontSize": 18.0,
                "Leading": 21.6,
                "TabWidth": 128.0,
                "formatCode": {
                    "normal": "QAEAAAAAAABEMyIRDAAAAAAABgAKAAQABgAAAGQAAAAAAF4AHAAUABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADwAAAAgAAAAAABsABwBeAAAAAAAAARQAAAAAAAABHAAAADQAAAAAAAAAWP///1z///9g////ZP///wEAAAAEAAAADgAAAE1pY3Jvc29mdFlhSGVpAAABAAAADAAAAAgADAAEAAgACAAAAAgAAABAAAAAAQAAAGEANgAYAAAAFAAAAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAwAAAAIAAQANgAAAAIAAAAQAAAAEAAAAAAAgEAAAMBB9P////j////8////BAAEAAQAAAA=",
                    "b": "RAEAAAAAAABEMyIRDAAAAAAABgAKAAQABgAAAGQAAAAAAF4AHAAUABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADwAAAAgAAAAAABsABwBeAAAAAAAAARQAAAAAAAABHAAAADgAAAAAAAAAVP///1j///9c////YP///wEAAAAEAAAAEwAAAE1pY3Jvc29mdFlhSGVpLUJvbGQAAQAAAAwAAAAIAAwABAAIAAgAAAAIAAAAQAAAAAEAAABhADYAGAAAABQAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAMAAAACAAEADYAAAACAAAAEAAAABAAAAAAAIBAAADAQfT////4/////P///wQABAAEAAAA",
                    "green": "WAEAAAAAAABEMyIRDAAAAAAABgAKAAQABgAAAGQAAAAAAF4AHAAUABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADwAAAAgAAAAAABsABwBeAAAAAAAAARQAAAAAAAABHAAAADQAAAAAAAAAXP///2D///9k////aP///wEAAAAEAAAADgAAAE1pY3Jvc29mdFlhSGVpAAABAAAADAAAAAgADAAEAAgACAAAAAgAAABAAAAAAQAAAGEANgAcAAAAGAAUAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAwAAAAIAAQANgAAAAIAAAAUAAAAGAAAAAAAgEAoAAAAAADAQfz///8EAAQABAAAAAQABgAEAAAAAAAKAAgABgAAAAcACgAAAAAAAAA=",
                    "yellow": "WAEAAAAAAABEMyIRDAAAAAAABgAKAAQABgAAAGQAAAAAAF4AHAAUABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADwAAAAgAAAAAABsABwBeAAAAAAAAARQAAAAAAAABHAAAADQAAAAAAAAAXP///2D///9k////aP///wEAAAAEAAAADgAAAE1pY3Jvc29mdFlhSGVpAAABAAAADAAAAAgADAAEAAgACAAAAAgAAABAAAAAAQAAAGEANgAcAAAAGAAUAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAwAAAAIAAQANgAAAAIAAAAUAAAAGAAAAAAAgEAoAAAAAADAQfz///8EAAQABAAAAAQABgAEAAAAAAAKAAgAAAAAAAcACgAAAAAAAAA=",
                    "purple": "UAEAAAAAAABEMyIRDAAAAAAABgAKAAQABgAAAGQAAAAAAF4AHAAUABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADwAAAAgAAAAAABsABwBeAAAAAAAAARQAAAAAAAABHAAAADQAAAAAAAAAWP///1z///9g////ZP///wEAAAAEAAAADgAAAE1pY3Jvc29mdFlhSGVpAAABAAAADAAAAAgADAAEAAgACAAAAAgAAABAAAAAAQAAAGEANgAcAAAAGAAUAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAwAAAAIAAQANgAAAAIAAAAUAAAAFAAAAAAAgEAgAAAAAADAQfj////8////BAAEAAQAAAAIAAgAAAAHAAgAAAAAAAAA"
                }
            }
        }
        print("本方法将遍历所有的序列节点，将其文本信息依次导出为适用于Adobe Premiere Pro软件的剪贴板。\nThis method will traverse all nodes in the sequence one by one and export the text into a clipboard window that can be pasted into Adobe Premiere Pro.\n\n在准备就绪后，按下回车键以复制初始状态的文本。\nWhen you're ready, press Enter to copy the text of the initial snapshot.")
        quit: bool = False #标记是否提前退出循环（Marks whether to exit the loop in advance）
        for i in range(begIndex, self.snapshot_count): #遍历序列节点（Traverse sequence nodes）
            phase: str = "initial" if i == 0 else self.selections[i - 1]["action"] #在提示语中显式标记初始状态（Explicitly mark the initial status in the prompt）
            #获取文本和格式信息（Get text and encoding）
            anvilTable, formatArray, styleSheet_runLengthArray = self.export_clip(index = i, mode = mode)
            nFormats: int = len(formatArray)
            #分块复制（Block-wise copy）
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            ##数据对象（DataObject）
            bDataObject: bytes = b"\x00\x00\x00\x00\x00\x00\x00\x00"
            win32clipboard.SetClipboardData(clipboard_formats["DataObject"], bDataObject)
            ##原始文本（CF_UNICODETEXT）
            win32clipboard.SetClipboardData(clipboard_formats["CF_UNICODETEXT"], anvilTable)
            ##PS文本格式（Photoshop Text）
            ###编码文本（Encoded text）
            editor_text: bytes = unicode2PSText(anvilTable)
            ###段落表单（Paragraph sheet）
            paragraph_count: int = anvilTable.count("\r") + 1
            paragraphSheet_default: dict[str, dict[str, Any]] = {
                "ParagraphSheet": {
                    "DefaultStyleSheet": 0,
                    "Properties": {
                        "Justification": 0
                    }
                },
                "Adjustments": {
                    "Axis": [1.0, 0.0, 1.0],
                    "XY": [0.0, 0.0]
                }
            }
            paragraphSheet_runArray: list[dict[str, dict[str, Any]]] = [copy.deepcopy(paragraphSheet_default) for _ in range(paragraph_count)] #36段（36 paragraphs）
            paragraphSheet_runLengthArray: list[int] = list(map(len, anvilTable.splitlines(keepends = True))) #段数和上面一致（The number of paragraphs is coincident with above）
            ###样式表单（Style sheet）
            styleSheet_default: dict[str, dict[str, Any]] = {
                "StyleSheet": {
                    "StyleSheetData": {
                        "Font": 0,
                        "FontSize": config[res]["FontSize"],
                        "FauxBold": False,
                        "FauxItalic": False,
                        "AutoLeading": False,
                        "Leading": config[res]["Leading"],
                        "Tracking": 0,
                        "AutoKerning": True,
                        "Kerning": 0,
                        "BaselineShift": 0.0,
                        "FontCaps": 0,
                        "FontBaseline": 0,
                        "Underline": False,
                        "Ligatures": True,
                        "Tsume": 0.0,
                        "FillColor": {
                            "Type": 1,
                            "Values": [1.0, 1.0, 1.0, 1.0]
                        },
                        "StrokeColor": {
                            "Type": 1,
                            "Values": [1.0, 1.0, 1.0, 1.0]
                        },
                        "FillFlag": True,
                        "StrokeFlag": False,
                        "FillFirst": False,
                        "YUnderline": 1,
                        "OutlineWidth": 4.0,
                        "HindiNumbers": False
                    }
                }
            }
            styleSheet_runArray: list[dict[str, dict[str, Any]]] = [copy.deepcopy(styleSheet_default) for _ in range(nFormats)]
            for j in range(nFormats):
                textFormat: str = formatArray[j]
                if textFormat == "normal":
                    pass
                elif textFormat == "b":
                    styleSheet_runArray[j]["StyleSheet"]["StyleSheetData"]["Font"] = 1 #微软雅黑粗体（MicrosoftYaHei bold）
                elif textFormat == "yellow":
                    styleSheet_runArray[j]["StyleSheet"]["StyleSheetData"]["FillColor"]["Values"] = [1.0, 1.0, 1.0, 0.0] #黄色（Yellow）
                elif textFormat == "purple":
                    styleSheet_runArray[j]["StyleSheet"]["StyleSheetData"]["FillColor"]["Values"] = [1.0, 1.0, 0.0, 1.0] #紫色（Purple）
                elif textFormat == "green":
                    styleSheet_runArray[j]["StyleSheet"]["StyleSheetData"]["FillColor"]["Values"] = [1.0, 0.0, 1.0, 0.0] #绿色（Green）
            ###日文换行规则（Kinsoku）
            kinsokuSet: list[dict[str, str]] = [
                {
                    "Name": "PhotoshopKinsokuHard",
                    "NoStart": "、。，．・：；？！ー―’”）〕］｝〉》」』】ヽヾゝゞ々ぁぃぅぇぉっゃゅょゎァィゥェォッャュョヮヵヶ゛゜?!)]},.:;℃℉¢％‰",
                    "NoEnd": "‘“（〔［｛〈《「『【([{￥＄£＠§〒＃",
                    "Keep": "―‥",
                    "Hanging": "、。.,"
                },
                {
                    "Name": "PhotoshopKinsokuSoft",
                    "NoStart": "、。，．・：；？！’”）〕］｝〉》」』】ヽヾゝゞ々",
                    "NoEnd": "‘“（〔［｛〈《「『【",
                    "Keep": "―‥",
                    "Hanging": "、。.,"
                }
            ]
            kinsokuSet_encoded: list[dict[str, bytes]] = [{key: unicode2PSText(value) for (key, value) in elem.items()} for elem in kinsokuSet]
            ###日文字符间距规则（Mojikumi set）
            mojiKumiSet: list[dict[str, str]] = [
                {
                    "InternalName": "Photoshop6MojiKumiSet1"
                },
                {
                    "InternalName": "Photoshop6MojiKumiSet2"
                },
                {
                    "InternalName": "Photoshop6MojiKumiSet3"
                },
                {
                    "InternalName": "Photoshop6MojiKumiSet4"
                }
            ]
            mojiKumiSet_encoded: list[dict[str, bytes]] = [{key: unicode2PSText(value) for (key, value) in elem.items()} for elem in mojiKumiSet]
            ###段落表单集合（Paragraph sheet set）
            paragraphSheetSet_element_default: dict[str, Any] = {
                "Name": unicode2PSText("Normal"),
                "DefaultStyleSheet": 0,
                "Properties": {
                    "Justification": 0,
                    "FirstLineIndent": 0.0,
                    "StartIndent": 0.0,
                    "EndIndent": 0.0,
                    "SpaceBefore": 0.0,
                    "SpaceAfter": 0.0,
                    "AutoHyphenate": True,
                    "HyphenatedWordSize": 6,
                    "PreHyphen": 2,
                    "PostHyphen": 2,
                    "ConsecutiveHyphens": 8,
                    "Zone": 36.0,
                    "WordSpacing": [0.8, 1.0, 1.33],
                    "LetterSpacing": [0.0, 0.0, 0.0],
                    "GlyphSpacing": [1.0, 1.0, 1.0],
                    "AutoLeading": 1.2,
                    "LeadingType": 0,
                    "Hanging": False,
                    "Burasagari": False,
                    "KinsokuOrder": 0,
                    "EveryLineComposer": False
                }
            }
            paragraphSheetSet: list[dict[str, Any]] = [paragraphSheetSet_element_default]
            ###样式表单集合（Style sheet set）
            styleSheetSet_element_default: dict[str, Any] = {
                "Name": unicode2PSText("Normal"),
                "StyleSheetData": {
                    "Font": 2,
                    "FontSize": 12.0,
                    "FauxBold": False,
                    "FauxItalic": False,
                    "AutoLeading": True,
                    "Leading": 27.0,
                    "HorizontalScale": 1.0,
                    "VerticalScale": 1.0,
                    "Tracking": 0,
                    "AutoKerning": True,
                    "Kerning": 0,
                    "BaselineShift": 0.0,
                    "FontCaps": 0,
                    "FontBaseline": 0,
                    "Underline": False,
                    "Strikethrough": False,
                    "Ligatures": True,
                    "DLigatures": False,
                    "BaselineDirection": 2,
                    "Tsume": 0.0,
                    "StyleRunAlignment": 2,
                    "Language": 0,
                    "NoBreak": False,
                    "FillColor": {
                        "Type": 1,
                        "Values": [1.0, 0.0, 0.0, 0.0]
                    },
                    "StrokeColor": {
                        "Type": 1,
                        "Values": [1.0, 0.0, 0.0, 0.0]
                    },
                    "FillFlag": True,
                    "StrokeFlag": False,
                    "FillFirst": True,
                    "YUnderline": 1,
                    "OutlineWidth": 1.0,
                    "CharacterDirection": 0,
                    "HindiNumbers": False,
                    "Kashida": 1,
                    "DiacriticPos": 2
                }
            }
            styleSheetSet: list[dict[str, Any]] = [styleSheetSet_element_default]
            ###字体集（Font set）
            fontSet: list[dict[str, Any]] = [
                {
                    "Name": "MicrosoftYaHei",
                    "Script": 3,
                    "FontType": 1,
                    "Synthetic": 0
                },
                {
                    "Name": "MicrosoftYaHei-Bold",
                    "Script": 3,
                    "FontType": 1,
                    "Synthetic": 0
                },
                {
                    "Name": "Myriad-Roman",
                    "Script": 0,
                    "FontType": 0,
                    "Synthetic": 0
                },
                {
                    "Name": "AdobeInvisFont",
                    "Script": 0,
                    "FontType": 0,
                    "Synthetic": 0
                }
            ]
            fontSet_encoded: list[dict[str, Any]] = [{key: unicode2PSText(value) if key == "Name" else value for (key, value) in elem.items()} for elem in fontSet]
            ###资源字典（Resource dictionary）
            resourceDict: dict[str, Any] = {
                "KinsokuSet": kinsokuSet_encoded,
                "MojiKumiSet": mojiKumiSet_encoded,
                "TheNormalStyleSheet": 0,
                "TheNormalParagraphSheet": 0,
                "ParagraphSheetSet": paragraphSheetSet,
                "StyleSheetSet": styleSheetSet,
                "FontSet": fontSet_encoded,
                "SuperscriptSize": 0.583,
                "SuperscriptPosition": 0.333,
                "SubscriptSize": 0.583,
                "SubscriptPosition": 0.333,
                "SmallCapSize": 0.7
            }
            ###汇总赋值（Consolidated assignment）
            photoshopText_data: dict[str, Any] = {
                "ParagraphTextEditor": {
                    "Editor": {
                        "Text": editor_text
                    },
                    "ParagraphRun": {
                        "DefaultRunData": {
                            "ParagraphSheet": {
                                "DefaultStyleSheet": 0,
                                "Properties": {}
                            },
                            "Adjustments": {
                                "Axis": [1.0, 0.0, 1.0],
                                "XY": [0.0, 0.0]
                            }
                        },
                        "RunArray": paragraphSheet_runArray,
                        "RunLengthArray": paragraphSheet_runLengthArray,
                        "IsJoinable": 1
                    },
                    "StyleRun": {
                        "DefaultRunData": {
                            "StyleSheet": {
                                "StyleSheetData": {}
                            }
                        },
                        "RunArray": styleSheet_runArray,
                        "RunLengthArray": styleSheet_runLengthArray,
                        "IsJoinable": 2
                    },
                    "GridInfo": {
                        "GridIsOn": False,
                        "ShowGrid": False,
                        "GridSize": 18.0,
                        "GridLeading": 22.0,
                        "GridColor": {
                            "Type": 1,
                            "Values": [0.0, 0.0, 0.0, 1.0]
                        },
                        "GridLeadingFillColor": {
                            "Type": 1,
                            "Values": [0.0, 0.0, 0.0, 1.0]
                        },
                        "AlignLineHeightToGridFlags": False
                    },
                    "AntiAlias": 0,
                    "UseFractionalGlyphWidths": False,
                    "Rendered": {
                        "Version": 1,
                        "Shapes": {
                            "WritingDirection": 0,
                            "Children": []
                        }
                    }
                },
                "ResourceDict": resourceDict,
                "DocumentResources": resourceDict
            }
            photoshop_text: bytes = restore_PRClipboard_Photoshop_Text(photoshopText_data)
            win32clipboard.SetClipboardData(clipboard_formats["Photoshop Text"], photoshop_text)
            ##Adobe文本引擎v2（Adobe Text Engine 2.0）
            ###编码文本（Encoded text）
            editor_text: bytes = unicode2PSText(anvilTable)
            ###字体集（Font set）
            fontSet_engine: list[dict[str, dict[str, Any]]] = [
                {
                    "0": {
                        "99": "CoolTypeFont",
                        "0": {
                            "0": unicode2PSText("MicrosoftYaHei"),
                            "1": 3,
                            "2": 1,
                            "5": unicode2PSText("Version 6.31")
                        }
                    }
                },
                {
                    "0": {
                        "99": "CoolTypeFont",
                        "0": {
                            "0": unicode2PSText("MicrosoftYaHei-Bold"),
                            "1": 3,
                            "2": 1,
                            "5": unicode2PSText("Version 6.31")
                        }
                    }
                },
                {
                    "0": {
                        "99": "CoolTypeFont",
                        "0": {
                            "0": unicode2PSText("Myriad-Roman"),
                            "2": 0
                        }
                    }
                }
            ]
            ###日文换行规则（Kinsoku）
            kinsokuSet_engine: list[dict[str, dict[str, Any]]] = [
                {
                    "0": {
                        "0": unicode2PSText("Hard"),
                        "5": {
                            "0": unicode2PSText("!),.:;?]}¢—’”‰℃℉、。々〉》」』】〕ぁぃぅぇぉっゃゅょゎ゛゜ゝゞァィゥェォッャュョヮヵヶ・ーヽヾ！％），．：；？］｝"),
                            "1": unicode2PSText("([{£§‘“〈《「『【〒〔＃＄（＠［｛￥"),
                            "2": unicode2PSText("—‥…"),
                            "3": unicode2PSText("、。，．"),
                            "4": 1
                        }
                    }
                },
                {
                    "0": {
                        "0": unicode2PSText("Soft"),
                        "5": {
                            "0": unicode2PSText("’”、。々〉》」』】〕ゝゞ・ヽヾ！），．：；？］｝"),
                            "1": unicode2PSText("‘“〈《「『【〔（［｛"),
                            "2": unicode2PSText("—‥…"),
                            "3": unicode2PSText("、。，．"),
                            "4": 2
                        }
                    }
                }
            ]
            ###样式表单集合（Style sheet set）
            styleSheetSet_element_engine_default: dict[str, dict[str, Any]] = {
                "0": {
                    "0": unicode2PSText("Normal"),
                    "6": {
                        "0": 2,
                        "1": 12.0,
                        "2": False,
                        "3": False,
                        "4": True,
                        "5": 27.0,
                        "6": 1.0,
                        "7": 1.0,
                        "8": 0,
                        "9": 0.0,
                        "10": 0.0,
                        "11": 1,
                        "12": 0,
                        "13": 0,
                        "14": 0,
                        "15": 0,
                        "16": 0,
                        "17": 0.0,
                        "18": True,
                        "19": False,
                        "20": False,
                        "21": False,
                        "22": False,
                        "23": False,
                        "24": False,
                        "25": False,
                        "26": False,
                        "27": False,
                        "28": False,
                        "29": False,
                        "30": 0,
                        "31": False,
                        "32": False,
                        "33": False,
                        "34": False,
                        "35": 2,
                        "36": 0.0,
                        "37": 2,
                        "38": 0,
                        "39": 0,
                        "40": False,
                        "41": 2,
                        "42": 0,
                        "43": {
                            "0": 0.5
                        },
                        "44": 2,
                        "45": 2,
                        "46": 7,
                        "47": 0,
                        "48": 0,
                        "49": -1.0,
                        "50": -1.0,
                        "51": 0,
                        "52": False,
                        "53": {
                            "99": "SimplePaint",
                            "0": {
                                "0": 1,
                                "1": [1.0, 0.0, 0.0, 0.0]
                            }
                        },
                        "54": {
                            "99": "SimplePaint",
                            "0": {
                                "0": 1,
                                "1": [1.0, 0.0, 0.0, 0.0]
                            }
                        },
                        "55": {
                            "99": "SimpleBlender"
                        },
                        "56": True,
                        "57": False,
                        "58": True,
                        "59": False,
                        "60": False,
                        "61": 0,
                        "62": 0,
                        "63": 1.0,
                        "64": 4.0,
                        "65": 0.0,
                        "66": [],
                        "67": [],
                        "68": 0,
                        "69": 0,
                        "70": 0,
                        "71": 4,
                        "72": 0.0,
                        "73": 0.0,
                        "74": False,
                        "75": False,
                        "76": False,
                        "77": True,
                        "78": True,
                        "79": {
                            "99": "SimplePaint",
                            "0": {
                                "0": 1,
                                "1": [1.0, 1.0, 1.0, 0.0]
                            }
                        },
                        "80": False,
                        "81": 0,
                        "82": 3.0,
                        "83": 3.0,
                        "84": False,
                        "85": 0,
                        "86": {
                            "99": "SimpleCustomFeature"
                        },
                        "87": 100.0,
                        "88": True,
                        "92": 0.0,
                        "95": {
                            "0": 0.0,
                            "1": 0
                        },
                        "96": True
                    }
                }
            }
            styleSheetSet_engine: list[dict[str, dict[str, Any]]] = [styleSheetSet_element_engine_default]
            ###段落表单集合（Paragraph sheet set）
            paragraphSheetSet_element_engine_default: dict[str, dict[str, Any]] = {
                "0": {
                    "0": unicode2PSText("Normal"),
                    "5": {
                        "0": 0,
                        "1": 0.0,
                        "2": 0.0,
                        "3": 0.0,
                        "4": 0.0,
                        "5": 0.0,
                        "6": 1,
                        "7": 1.2,
                        "8": 0,
                        "9": True,
                        "10": 6,
                        "11": 2,
                        "12": 2,
                        "13": 0,
                        "14": 36.0,
                        "15": True,
                        "16": 0.5,
                        "17": [0.8, 1.0, 1.33],
                        "18": [0.0, 0.0, 0.0],
                        "19": [1.0, 1.0, 1.0],
                        "20": 6,
                        "21": False,
                        "22": 0,
                        "23": False,
                        "24": 0,
                        "25": 0,
                        "27": "nil",
                        "26": False,
                        "28": "nil",
                        "29": False,
                        "30": {},
                        "31": 36.0,
                        "32": {},
                        "33": 0,
                        "34": 7,
                        "35": 1,
                        "36": "nil",
                        "37": 0,
                        "38": False,
                        "39": 0,
                        "40": 2,
                        "41": 0
                    }
                }
            }
            paragraphSheetSet_engine: list[dict[str, dict[str, Any]]] = [paragraphSheetSet_element_engine_default]
            ###段落表单（Paragraph sheet）
            paragraphSheet_engine_default: dict[str, dict[str, Any]] = {
                "0": {
                    "0": unicode2PSText(""),
                    "5": {
                        "0": 0,
                        "31": config[res]["TabWidth"],
                        "33": 0
                    },
                    "6": 0
                }
            }
            paragraphSheet_runArray_engine: list[dict[str, dict[str, Any]]] = [copy.deepcopy(paragraphSheet_engine_default) for _ in range(paragraph_count)]
            paragraphSheet_runLengthArray_engine: list[int] = paragraphSheet_runLengthArray
            ###样式表单（Style sheet）
            # serializedTextProperties: dict[str, str] = {"normal": config[res]["formatCode"]["normal"], "b": config[res]["formatCode"]["b"], "green": config[res]["formatCode"]["green"], "yellow": config[res]["formatCode"]["yellow"], "purple": config[res]["formatCode"]["purple"]} #预定义一些样式的序列化文本属性（Predefine some styles' serialized text properties）
            styleSheet_engine_default: dict[str, dict[str, Any]] = {
                "0": {
                    "0": unicode2PSText(""),
                    "5": 0,
                    "6": {
                        "0": 0,
                        "1": config[res]["FontSize"],
                        "2": False,
                        "3": False,
                        "4": False,
                        "5": config[res]["Leading"],
                        "8": 0,
                        "9": 0.0,
                        "12": 0,
                        "13": 0,
                        "16": 0,
                        "18": True,
                        "36": 0.0,
                        "53": {
                            "99": "SimplePaint",
                            "0": {
                                "0": 1,
                                "1": [1.0, 1.0, 1.0, 1.0]
                            }
                        },
                        "54": {
                            "99": "SimplePaint",
                            "0": {
                                "0": 1,
                                "1": [1.0, 1.0, 1.0, 1.0]
                            }
                        },
                        "56": True,
                        "57": False,
                        "58": False,
                        "63": 4.0,
                        "70": 1,
                        "77": True,
                        "78": False,
                        "86": {
                            "99": "ATEWrapperStyleParamFB",
                            "0": b""
                        },
                        "92": 0.0
                    }
                }
            }
            styleSheet_engine_default["0"]["6"]["86"]["0"] = unicode2PSText(config[res]["formatCode"]["normal"]) #该字符串无法推导得出。用户必须事先在Premiere Pro软件中先套用相关样式，再获取对应的字符串（This string can't be derivated for now. Users must apply the corresponding format in Premiere Pro app and then get this string）
            styleSheet_runArray_engine: list[dict[str, dict[str, Any]]] = [copy.deepcopy(styleSheet_engine_default) for _ in range(nFormats)]
            for j in range(nFormats):
                textFormat: str = formatArray[j]
                if textFormat == "normal":
                    pass
                elif textFormat == "b":
                    styleSheet_runArray_engine[j]["0"]["6"]["0"] = 1 #微软雅黑粗体（MicrosoftYaHei bold）
                    styleSheet_runArray_engine[j]["0"]["6"]["86"]["0"] = unicode2PSText(config[res]["formatCode"]["b"])
                elif textFormat == "yellow":
                    styleSheet_runArray_engine[j]["0"]["6"]["53"]["0"]["1"] = [1.0, 1.0, 1.0, 0.0] #黄色（Yellow）
                    styleSheet_runArray_engine[j]["0"]["6"]["86"]["0"] = unicode2PSText(config[res]["formatCode"]["yellow"])
                elif textFormat == "purple":
                    styleSheet_runArray_engine[j]["0"]["6"]["53"]["0"]["1"] = [1.0, 1.0, 0.0, 1.0] #紫色（Purple）
                    styleSheet_runArray_engine[j]["0"]["6"]["86"]["0"] = unicode2PSText(config[res]["formatCode"]["purple"])
                elif textFormat == "green":
                    styleSheet_runArray_engine[j]["0"]["6"]["53"]["0"]["1"] = [1.0, 0.0, 1.0, 0.0] #绿色（Green）
                    styleSheet_runArray_engine[j]["0"]["6"]["86"]["0"] = unicode2PSText(config[res]["formatCode"]["green"])
            ###汇总赋值（Consolidated assignment）
            adobeTextEngine_data: dict[str, Any] = {
                "98": {
                    "0": 12
                },
                "0": {
                    "1": {
                        "0": fontSet_engine
                    },
                    "4": {
                        "0": kinsokuSet_engine,
                        "1": [
                            {
                                "0": 0
                            },
                            {
                                "0": 1
                            }
                        ]
                    },
                    "5": {
                        "0": styleSheetSet_engine,
                        "1": [
                            {
                                "0": 0
                            }
                        ]
                    },
                    "6": {
                        "0": paragraphSheetSet_engine,
                        "1": [
                            {
                                "0": 0
                            }
                        ]
                    },
                    "8": {}
                },
                "1": {
                    "0": editor_text,
                    "1": {
                        "0": paragraphSheet_runArray_engine,
                        "1": paragraphSheet_runLengthArray_engine
                    },
                    "2": {
                        "0": styleSheet_runArray_engine,
                        "1": styleSheet_runLengthArray
                    },
                    "3": {
                        "0": [
                            {}
                        ],
                        "1": [
                            635
                        ]
                    },
                    "4": {
                        "0": [
                            {}
                        ],
                        "1": [
                            634
                        ]
                    },
                    "6": {
                        "0": [
                            {}
                        ],
                        "1": [
                            634
                        ]
                    }
                }
            }
            adobeTextEngine_text: bytes = restore_PRClipboard_Adobe_Text_Engine_v2(adobeTextEngine_data)
            win32clipboard.SetClipboardData(clipboard_formats["Adobe Text Engine 2.0"], adobeTextEngine_text)
            ##对象链接与嵌入私有数据（OLE Private Data）
            # bOlePrivateData: bytes = b"\x00\x00\x00\x00\x08\x01\x00\x00\x01\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\r\x00O\x99\xa7\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\xff\xff\xff\xff\x01\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc3\xc4 \x8f\xa7\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\xff\xff\xff\xff\x01\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc4\xc4\x8a\xab\xa7\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\xff\xff\xff\xff\x01\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            # win32clipboard.SetClipboardData(clipboard_formats["Ole Private Data"], bOlePrivateData)
            ##区域设置（CF_LOCALE）
            win32clipboard.SetClipboardData(clipboard_formats["CF_LOCALE"], b"\x04\x08\x00\x00")
            ##ANSI文本（CF_TEXT）
            win32clipboard.SetClipboardData(clipboard_formats["CF_TEXT"], anvilTable.encode("ansi"))
            ##GBK文本（CF_OEMTEXT）
            win32clipboard.SetClipboardData(clipboard_formats["CF_OEMTEXT"], anvilTable.encode("gbk"))
            win32clipboard.CloseClipboard()
            
            #打印快照内容以便比对（Print snapshot content for the sake of comparison）
            print(anvilTable.replace("\r", "\n"))
            
            print("[%d/%d][%s]已复制快照。 | Snapshot copied." %(i + 1, self.snapshot_count, phase))
            print("按回车键以继续，或者输入任意非空字符串以退出。\nPress Enter to continue, or submit any non-empty string to quit.")
            quit: bool = bool(input())
            if quit:
                break
    
    def export_counter(self, mode: str = "cherry") -> str:
        '''
        将属性锻造器时间序列中的各个时刻的计数导出为一张表格。<br>Export the count at each point in the stat anvil sequence into a table.
        
        这个表格曾计划用于通过CompsFromSpreadsheet插件导入Adobe After Effects软件中，从而批量创建计数器快照剪辑。但是，因为该插件不支持设置复杂的文本格式，所以目前没有用到这个方法。<br>This table had intended to be exported into Adobe After Effects software by CompsFromSpreadsheet plugin to create counter snapshot clips in batches. However, because this plugin doesn't support complex text format, currently this method isn't put to use.
        
        :param mode: 游戏模式。决定要导出的属性锻造器字段。包含以下取值：<br>Game mode, which determines the stat anvil fields to export. It supports the following values:
        
            - cherry: （☆）斗魂竞技场。<br>Arena.
            - kiwi: 海克斯大乱斗。<br>ARAM: Mayhem.
        :type mode: Literal["cherry", "kiwi"]
        :return: 用制表位分隔的文本。<br>Text delimited by tab characters.
        :rtype: str
        '''
        #准备表头相关常量（Prepare header related constants）
        if mode == "kiwi":
            anvilTypes_silver: list[str] = ["AH", "AD", "AP", "Hybrid2", "AM", "MR", "Hybrid3", "HP", "AS", "Hybrid1", "CSC", "LTH", "MRPF"]
            anvilTypes_gold: list[str] = ["AH", "AD", "AP", "Hybrid2", "AM", "MR", "Hybrid3", "HP", "AS", "Hybrid1", "CSC", "LTH", "MRPF"]
            anvilTypes_prismatic: list[str] = ["MS", "HPSZ", "OMV", "TNC", "HSP", "AMP", "MRPP"]
        else:
            anvilTypes_silver = self.VALID_SILVER_TYPES
            anvilTypes_gold = self.VALID_GOLD_TYPES
            anvilTypes_prismatic = self.VALID_PRISMATIC_TYPES
        anvilTypes: dict[str, list[str]] = {"Silver": anvilTypes_silver, "Gold": anvilTypes_gold, "Prismatic": anvilTypes_prismatic}
        #确定表头顺序（Determine the order of the headers）
        counters: dict[str, list[Any]] = {"index": [0], "action": [""], "silver_total": [0], "gold_total": [0], "prismatic_total": [0]}
        for tier, anvilTypes_tier in anvilTypes.items():
            for anvilType in anvilTypes_tier:
                key_supply: str = "%s_%s_supplied" %(tier.lower(), anvilType.lower())
                key_select: str = "%s_%s_selected" %(tier.lower(), anvilType.lower())
                counters[key_supply] = [0]
                counters[key_select] = [0]
        #赋值（Assignment）
        for i in range(1, self.snapshot_count):
            selection: Selection = self.selections[i - 1]
            counter2: dict[str, dict[str, dict[str, int | float]]] = self.sequence[i]
            action: str = selection["action"]
            counters["index"].append((i + 1) // 2) #要求选择界面数据必须符合实际顺序，即供应和选择相互交替（Requires the selection data must obey the practical order, namely supply and selection alternate with each other）
            counters["action"].append(action)
            counters["silver_total"].append(sum(map(lambda x: x["selectCount"], counter2["Silver"].values())))
            counters["gold_total"].append(sum(map(lambda x: x["selectCount"], counter2["Gold"].values())))
            counters["prismatic_total"].append(sum(map(lambda x: x["selectCount"], counter2["Prismatic"].values())))
            for tier, anvilTypes_tier in anvilTypes.items():
                for anvilType in anvilTypes_tier:
                    key_supply: str = "%s_%s_supplied" %(tier.lower(), anvilType.lower())
                    key_select: str = "%s_%s_selected" %(tier.lower(), anvilType.lower())
                    counters[key_supply].append(counter2[tier][anvilType]["supplyCount"])
                    counters[key_select].append(counter2[tier][anvilType]["selectCount"])
        #导出表格字符串（Export the tabular string）
        result: str = "\t".join(list(counters.keys())) + "\n" + "\n".join(["\t".join([str(counters[key][i]) for key in counters]) for i in range(self.snapshot_count)])
        return result

def main() -> int:
    '''
    主函数。在运行此脚本时执行此函数。<br>Main function, called when this program is run.
    
    :return: 状态码。<br>Status code.
    
        - 0: 如期运行。<br>Run as expected.
        - 1: 剪贴板格式缺失。<br>Missing clipboard formats.
    :rtype: int
    '''
    anvilSeq: StatAnvilSequence = StatAnvilSequence() #初始化属性锻造器时间序列对象（Initialize a `StatAnvilSequence` object）
    #检查剪贴板格式（Check clipboard formats）
    missing_clipboard_formats: list[str] = [_ for _ in REQUIRED_CLIPBOARD_FORMATS_PR if not _ in clipboard_formats]
    if len(missing_clipboard_formats) > 0:
        print("剪贴板数据格式不符。请确保您在运行程序前复制了某个PR文本框中的一段文字。\nClipboard format mismatched. Please make sure you've copied some text in a PR textbox before running this program.")
        print("当前系统剪贴板窗口缺失以下格式：\nThe following formats are missing from the current system clipboard window:")
        # print(json.dumps(missing_clipboard_formats, ensure_ascii = False))
        for missing_clipboard_format in missing_clipboard_formats:
            print(f"- {missing_clipboard_format}")
        print("请打开Adobe Premiere Pro软件，在一个序列中创建一个文本框，输入一些文字之后复制该文本框中的文字，再运行本程序。\nPlease open Adobe Premiere Pro software, create a text box in a sequence, input some text into it, then copy the text and finally restart this program.\n\n程序即将退出。\nThe program will exit soon.")
        time.sleep(3)
        return 1
    #设置参数（Set parameters）
    step: int = 1 #步骤（Step）
    mode: str = "cherry" #属性锻造器的模式。决定呈现哪些属性锻造器的数量（The mode that stat anvils belong to, which determines the number of which types of stat anvils will be displayed）
    begIndex: int = 0 #复制和导出的起始快照的下标（The index of the snapshot to begin to copy and export）
    res: str = "1920x1080" #视频分辨率，决定复制到Premiere Pro的文本框中的文本的字号和制表位排版（Video resolution, which determines the font size and typesetting regarding tabs of the text to be copied into a text box in Premiere Pro）
    while True:
        if step == 0:
            break
        elif step == 1:
            print("第一步：请输入一个属性锻造器时间序列Json文件的路径。\nStep 1: Please input the path of a json file of stat anvil sequence.")
            while True:
                file_path: str = input()
                if file_path == "":
                    continue
                elif file_path == "0":
                    step -= 2
                elif not os.path.exists(file_path):
                    print("路径不存在。请重新输入。\nPath not found. Please try again.")
                elif not os.path.isfile(file_path):
                    print("请输入一个文件的路径。\nPlease input the path of a file.")
                else:
                    try:
                        with open(file_path, "r", encoding = "utf-8") as fp:
                            records: list[Selection] = json.load(fp)
                    except json.JSONDecodeError:
                        print("选择序列文件格式错误。请尝试输入另一个文件。\nSelection sequence format mismatch. Please try another file.")
                    else:
                        status: int = anvilSeq.extend(records)
                        if status == 0:
                            break
        elif step == 2:
            print("第二步：请选择一个游戏模式。\nStep 2: Please select a game mode.\n1\t斗魂竞技场（Arena）\n☆2\t海克斯大乱斗（ARAM: Mayhem）")
            while True:
                mode_option: str = input()
                if mode_option == "":
                    mode_option = "2"
                if mode_option[0] == "0":
                    step -= 2
                    break
                elif mode_option[0] == "1":
                    mode = "cherry"
                    break
                elif mode_option[0] == "2":
                    mode = "kiwi"
                    break
                else:
                    print("您的输入有误！请重新输入。\nERROR input! Please try again.")
        elif step == 3:
            print("第三步：请设置开始复制和导出快照的序号。\nPlease set the index of the snapshot to start to copy and export.")
            print("取值范围（Range）：[%d, %d]" %(-anvilSeq.snapshot_count, anvilSeq.snapshot_count - 1))
            print('输入空字符串以从头开始。输入“0”以返回上一步。\nEnter nothing to start from the beginning. Submit "0" to return to the last step.')
            while True:
                begIndex_str: str = input()
                if begIndex_str == "":
                    begIndex = 0
                    break
                elif begIndex_str == "0":
                    step -= 2
                    break
                else:
                    try:
                        begIndex = int(begIndex_str)
                    except ValueError:
                        print("请输入一个整数。\nPlease input an integer.")
                    else:
                        if begIndex >= -anvilSeq.snapshot_count and begIndex < anvilSeq.snapshot_count:
                            break
                        else:
                            print("下标越界。请重新输入。\nIndex out of bounds. Please try again.")
        elif step == 4:
            print("第四步：请选择视频分辨率。\nStep 4: Please select a resolution of the video.\n☆1\t1920 × 1080\n2\t2560 × 1440")
            while True:
                res_option: str = input()
                if res_option == "":
                    res_option = "1"
                if res_option[0] == "0":
                    step -= 2
                    break
                elif res_option[0] == "1":
                    res = "1920x1080"
                    break
                elif res_option[0] == "2":
                    res = "2560x1440"
                    break
                else:
                    print("您的输入有误！请重新输入。\nERROR input! Please try again.")
        elif step == 5:
            break
        else:
            print("步骤异常。请联系开发人员修复程序。\nStep error. Please contact the developer to fix the program.")
        step += 1
    #逐时间点复制（Timewise copy）
    if step == 5:
        anvilSeq.copy_counter_PR(begIndex = begIndex, mode = mode, res = res)
    return 0

def debug() -> None:
    '''
    调试函数。用于测试。<br>Debug function. For test.
    '''
    #属性锻造器时间序列（Stat anvil sequence）
    anvilSeq: StatAnvilSequence = StatAnvilSequence()
    #时间轴文本读写（Timeline text read and export）
    with open(os.path.expanduser("example/v2/StatAnvilSequence-Malphite-zh_CN.txt"), "r", encoding = "utf-8") as fp:
        timeline_text: str = fp.read()
    # timeline_text: str = "（1）（属性叠属性！）（白银阶）穿甲碎片、攻击速度碎片、生命值碎片（√）\n（2）（属性叠属性！）（棱彩阶）护甲穿透碎片、生命值与体型碎片（√）、全能吸血碎片\n（3）（属性叠属性！）（棱彩阶）韧性碎片、全能吸血碎片（√）、治疗与护盾强度碎片"
    anvilSeq.parse(timeline_text, useInternalName = False, locale = "zh_CN")
    timeline_text_transform: str = anvilSeq.export_timeline(useInternalName = False, useIntegerTier = False, locale = "en_US")
    print(timeline_text_transform)
    counter_table: str = anvilSeq.export_counter(mode = "kiwi")
    anvil_block: dict[str, dict[str, dict[str, Any]]] = anvilSeq.organize_anvil_data()
    print(json.dumps(anvil_block, indent = 4, ensure_ascii = False))
    import pyperclip
    pyperclip.copy(timeline_text_transform)
    input("按回车键复制属性锻造器选择序列数据。\nPress Enter to copy the stat anvil selection sequence data.\n")
    pyperclip.copy(json.dumps(anvilSeq.selections, indent = 4, ensure_ascii = False))
    input("按回车键复制属性锻造器计数表格。\nPress Enter to copy the stat anvil counter table.\n")
    pyperclip.copy(counter_table)

if __name__ == "__main__":
    clipboard_formats: dict[str, int] = get_clipboard_formats()
    # print(json.dumps(clipboard_formats, indent = 4, ensure_ascii = False))
    main()
    # debug()
