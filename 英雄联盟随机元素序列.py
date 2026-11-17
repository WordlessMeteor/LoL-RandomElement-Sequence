import copy, json, os, re, win32clipboard
from typing import Any, Literal, Optional
from pywintypes import HANDLEType

#第一部分：PR剪贴板仿真模拟（Part 1: PR clipboard simulation）
standard_formats: dict[int, str] = {
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

clipboard_formats: dict[str, int] = {} #初始化剪贴板格式（Initialize the clipboard formats）

def get_clipboard_format_name(formatId: int, hWnd: Optional[HANDLEType] = None) -> str:
    '''
    获取当前剪贴板中某个编号的格式的名称。<br>Get the name of some format with certain id in the current clipboard.
    
    本函数仅供获取单个剪贴板格式的名称。在批量获取多个格式编号的名称时，为了避免反复开关剪贴板，请仿照此函数主体自行声明逻辑。<br>This function is only intended for getting the name of a single clipboard format. To access names of multiple clipboard formats, please implement the logic based on this function's body by yourself, in case the clipboard would be opened and closed for multiple times.
    
    :param formatId: 格式编号。<br>Format id.
    :type formatId: int
    :param hWnd: 窗口句柄。如果未指定，则使用当前活动的剪贴板窗口。<br>A handle to the window. If not specified, the currently active clipboard window will be used.
    :type hWnd: pywintypes.HANDLEType
    :return: 格式名称。<br>Format name.
    
        - 如果格式是预定义的，那么返回win32clipboard库中对应变量的名称。<br>If the format is predefined, then return the name of the corresponding variable in `win32clipboard` library.
        - 如果格式不是预定义的，且能够通过标准剪贴板名称获取函数访问名称，那么返回这个名称。<br>If the format isn't predefined and the name can be accessed through `win32clipboard.GetClipboardFormatName` function, then return this name.
        - 其它情形下，返回格式编号的字符串形式。<br>In the other cases, return the formatId in string format.
    :rtype: str
    '''
    win32clipboard.OpenClipboard(hWnd)
    if formatId in standard_formats: #预定义的剪贴板格式无法通过标准剪贴板名称获取函数来访问名称（Predefined clipboard formats can't get the name through `win32clipboard.GetClipboardFormatName` function）
        name: str = standard_formats[formatId]
    else:
        try:
            name = win32clipboard.GetClipboardFormatName(formatId)
        except: #可能有部分未收录入标准格式字典（There may be some formats absent from `standard_formats`）
            name = str(formatId)
    win32clipboard.CloseClipboard()
    return name

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
        if next_formatId in standard_formats:
            next_formatName: str = standard_formats[next_formatId]
        else:
            try:
                next_formatName = win32clipboard.GetClipboardFormatName(next_formatId)
            except:
                next_formatName = str(next_formatId)        
        formats[next_formatName] = next_formatId
        current_formatId = next_formatId
    win32clipboard.CloseClipboard()
    return formats

def get_clipboard(hWnd: Optional[HANDLEType] = None) -> dict[str, str | bytes]: #改编自（Adpated from）： https://gist.github.com/sixpetrov/79d0856cae71cdcdf7fcba35ee4f1973
    '''
    获取剪贴板中所有格式编号的当前内容。<br>Get the current content of all format ids in the clipboard.
    
    :param hWnd: 窗口句柄。如果未指定，则使用当前活动的剪贴板窗口。<br>A handle to the window. If not specified, the currently active clipboard window will be used.
    :type hWnd: pywintypes.HANDLEType
    :param formatId: 格式编号。<br>Format id.
    :type formatId: int
    :return: 剪贴板的所有格式的内容。<br>Content of all formats of a clipboard.
    :rtype: dict[str, str | bytes]
    '''
    formats: dict[str, int] = get_clipboard_formats(hWnd)
    win32clipboard.OpenClipboard(hWnd)
    clipboard_content: dict[int, str | bytes] = {}
    for formatName in formats:
        formatId: str = formats[formatName]
        data: str | bytes = win32clipboard.GetClipboardData(formatId)
        clipboard_content[formatName] = data
    win32clipboard.CloseClipboard()
    return clipboard_content

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

#第二部分：属性锻造器序列处理（Part 2: Stat anvil sequence handling）
class StatAnvilSequence:
    STAT_ANVIL_SNAPSHOT_TEMPLATE: dict[str, dict[str, int]] = {"Silver": {"AH": 0, "AD": 0, "AP": 0, "Hybrid2": 0, "AM": 0, "MR": 0, "Hybrid3": 0, "HP": 0, "AS": 0, "Hybrid1": 0, "CSC": 0, "LTH": 0, "MRPF": 0, "Random": 0}, "Gold": {"AH": 0, "AD": 0, "AP": 0, "Hybrid2": 0, "AM": 0, "MR": 0, "Hybrid3": 0, "HP": 0, "AS": 0, "Hybrid1": 0, "CSC": 0, "LTH": 0, "MRPF": 0, "Random": 0, "ShardBladeAnvils": 0}, "Prismatic": {"MS": 0, "HPSZ": 0, "CSD": 0, "OMV": 0, "TNC": 0, "HSP": 0, "AMP": 0, "MRPP": 0, "Gold": 0, "GoldRoundLoss": 0, "Pristine": 0, "UpgradeShards": 0}}
    
    def __init__(self) -> None:
        '''
        属性锻造器时间序列类的构造函数。<br>The constructor of `StatAnvilSequence` class.
        '''
        self.statAnvilCounter_supply: dict[str, dict[str, int]] = self.deepcopy_anvilCounter(self.__class__.STAT_ANVIL_SNAPSHOT_TEMPLATE) #被提供的属性锻造器计数器。中间变量，存储特定时刻的锻造器数量。深复制防止修改模板常量字典（Supplied stat anvil counter. An intermediate variable that stores anvil count at specific time. Deep copy avoids changing the template constant dictionary）
        self.statAnvilCounter_select: dict[str, dict[str, int]] = self.deepcopy_anvilCounter(self.__class__.STAT_ANVIL_SNAPSHOT_TEMPLATE) #已选择的属性锻造器计数器。中间变量同上（Selected stat anvil counter. An intermediate variable, same as above）
        self.statAnvilSequence_supply: list[dict[str, dict[str, int]]] = [] #被提供的属性锻造器时间序列。当一次选择界面出现时，三个选项都应递增（Supplied stat anvil sequence. When a selection screen appears, all of the three options should be incremented）
        self.statAnvilSequence_select: list[dict[str, dict[str, int]]] = [] #已选择的属性锻造器时间序列。当用户做出一次选择时，被选择的选项应递增（Selected stat anvil sequence. When a seletion is made, the selected option should be incremeted）
        self.snapshot() #在该类对象初始化时立即拍一次快照（Take the first snapshot right when an object of this class is initialized）
        self.selections: list[tuple[str, str, tuple[str, ...]]] = [] #用户做出的所有选择。每个列表的元素的第一个元素是位阶，第二个元素是选择的锻造器类型，第三个是提供的锻造器类型（All selections made by the user. Of each element, the first element is tier, the second element is the selected anvil type and the third element is the provided anvil types）
        self.latest_selection: tuple[str, str, tuple[str, ...]] = ("", "", ("", "", "")) #记录最近的一次选择。数据一旦记录就不能修改了，用元组是非常合适的（Records the latest selection. Once the data is recorded, it shouldn't be changed, so tuple works quite well under such circumstance）
    
    @property
    def snapshot_count(self) -> int:
        '''
        动态返回快照的数量。<br>Dynamically return the number of snapshots.
        
        注意：在刚刚构造此类的对象时，快照数量为1。<br>Note: When an object of this class is just constructed, the number of snapshots is 1.
        
        :return: 快照数量。逻辑上等于`self.statAnvilSequence_supply`或`self.statAnvilSequence_select`的长度。<br>The number of snapshots. Logically, it's equal to the size of `self.statAnvilSequence_supply` or `self.statAnvilSequence_select`.
        :rtype: int
        '''
        return len(self.statAnvilSequence_supply)
    
    @property
    def selection_count(self) -> int:
        '''
        动态返回用户做出的选择次数。<br>Dynamically return the number of selections the user has made.
        
        :return: 用户的选择次数。逻辑上等于`self.selections`的长度。<br>The number of selections made by the user. Logically, it's equal to the size of `self.selections`.
        :rtype: int
        '''
        return len(self.selections)
    
    @staticmethod
    def deepcopy_anvilCounter(counter: dict[str, dict[str, int]]) -> dict[str, dict[str, int]]: #建立这个方法的初衷是减少库的依赖（The original intention to define this method is to reduce library dependencies）
        '''
        取代`copy.deepcopy`函数的锻造器计数器深复制方法。<br>A deep copy method of anvil counter, in place of `copy.deepcopy` function.
        
        :param counter: 锻造器计数器字典。<br>Anvil counter dictionary.
        :type counter: dict[str, dict[str, int]]
        :return: 深复制的锻造器计数器字典。<br>Deep copied anvil counter dictionary.
        :rtype: dict[str, dict[str, int]]
        '''
        return {key: value.copy() for (key, value) in counter.items()}
    
    def snapshot(self) -> None:
        '''
        将当前属性锻造器计数器添加到时间序列中。<br>Append the current stat anvil counter to the end of the stat anvil sequence.
        '''
        self.statAnvilSequence_supply.append(self.deepcopy_anvilCounter(self.statAnvilCounter_supply))
        self.statAnvilSequence_select.append(self.deepcopy_anvilCounter(self.statAnvilCounter_select))
    
    @classmethod
    def verify_selection_record(cls, rarity: Any, selection: Any, count_verify: int = 3) -> tuple[bool, str]:
        '''
        检查一条选择记录是否合法。<br>Check whether a selection record is legal.
        
        :param rarity: 位阶。<br>Tier.
        
            相关要求见`increment`方法。<br>Refer to `increment` method for its requirements.
        :type rarity: int | str
        :param selection: 选择界面数据。<br>Selection screen data.
        
            相关要求见`increment`方法。<br>Refer to `increment` method for its requirements.
        :type selection: dict[str, bool]
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
        #位阶（Tier）
        if isinstance(rarity, str):
            tier: str = rarity.lower().capitalize()
        elif rarity == 0:
            tier = "Silver"
        elif rarity == 1:
            tier = "Gold"
        elif rarity == 2:
            tier = "Prismatic"
        else:
            message = "错误的位阶。\nWrong tier."
            return (False, message)
        if not (isinstance(selection, dict) and all(map(lambda x: isinstance(x, str), selection.keys())) and all(map(lambda x: isinstance(x, bool), selection.values()))):
            message = "选择信息格式错误。\nSelection data format error."
            return (False, message)
        #选项数据（Option data）
        ##数量（Number）
        if len(selection) != count_verify:
            message = "选项数量错误。应为%d，实际收到%d。\nWrong number of options. Expected %d, received %d." %(count_verify, len(selection), count_verify, len(selection))
            return (False, message)
        if sum(selection.values()) != 1:
            message = "选择行为错误。应选择1个锻造器，实际选择%d个锻造器。\nWrong selection behavior. Expected 1 anvil selected but received %d anvil(s) selected." %(sum(selection.values()), sum(selection.values()))
            return (False, message)
        ##类型（Type）
        unidentified_anvilTypes: list[str] = []
        for anvilType in selection:
            if not anvilType.lower() in set(map(lambda x: x.lower(), cls.STAT_ANVIL_SNAPSHOT_TEMPLATE[tier].keys())): #可能包含海克斯大乱斗未开放的锻造器（Might include anvils not available in ARAM: Mayhem）
                unidentified_anvilTypes.append(anvilType)
        if len(unidentified_anvilTypes) > 0:
            message = "以下锻造器类型不存在：\nAnvil types not found:\n" + str(unidentified_anvilTypes).replace("'", '"')
            return (False, message)
        return (True, message)
    
    @classmethod
    def verify_selection_recordList(cls, records: Any) -> tuple[bool, str]:
        '''
        检查多条记录是否合法。<br>Check whether multiple selection records are legal.
        
        :param records: 选择记录列表。<br>Selection record list.
        
            相关要求见`extend`方法。<br>Refer to `extend` method for its requirements.
        :type records: list[tuple[str, dict[str, bool]]]
        :return: 一个二元组。<br>A two-tuple.
        
            - 选择记录列表是否合法。<br>Whether the selection record list is legal.
            - 消息。<br>Message.
        :rtype: tuple[bool, str]
        '''
        #初始化返回值（Initialize the returned value）
        message: str = ""
        if not (isinstance(records, list) and all(map(lambda x: isinstance(x, tuple), records))):
            message = "选择记录列表参数格式错误。\nSelection record list parameter format error."
            return (False, message)
        length_mismatch: list[tuple[int, tuple[Any, ...]]] = []
        format_mismatch: list[tuple[int, tuple[Any, ...]]] = []
        for i in range(len(records)):
            record: tuple[Any, ...] = records[i]
            if len(record) < 2:
                length_mismatch.append((i, record))
            elif not cls.verify_selection_record(record[0], record[1])[0]:
                format_mismatch.append((i, record))
        if len(length_mismatch) > 0:
            message += "以下选择记录的参数数量有误：\nThe following records have an incorrect number of parameters:\n"
            for i, record in length_mismatch:
                message += "[%d] %s\n" %(i, record)
        if len(format_mismatch) > 0:
            message += "以下选择记录的参数格式有误：\nThe following records have an incorrect format of parameters:\n"
            for i, record in format_mismatch:
                message += "[%d] %s\t%s\n" %(i, record[0], str(record[1]).replace("'", '"'))
        return (len(length_mismatch) + len(format_mismatch) == 0, message)
    
    def increment(self, rarity: int | str, selection: dict[str, bool]) -> int: #在设计上，本应设计成“选择界面弹出”和“做出选择”两个阶段。但是将两个阶段融合为一个过程，能够保证数据绝对是正确的。否则，如果用户尝试连续执行两个“选择界面弹出”过程，就会出现问题。如果用户想要获取“做出选择”之前的快照，只需要将已选择的属性锻造器计数器的对应锻造器类型的数量减1即可（By design, this method should have fit two phases: "Selection screen pops up" and "A selection is made". However, merging the two phases into one process could ensure the data must be accurate. Otherwise, a mistake will happen if the user tried to perform two "Selection screen pops up" continously. If the user wants to get the snapshot before "A selection is made", simply subtract the number of the latest selected anvil type in `self.statAnvilCounter_select` by 1）
        '''
        递增属性锻造器计数器。<br>Increment stat anvil counters.
        
        该方法同时递增被提供的和已选择的属性锻造器计数器。<br>This method increments both `self.statAnvilCounter_supply` and `self.statAnvilCounter_select`.
        
        该方法会校验用户的输入正确性。如果发现错误，则不执行任何操作。<br>This method verifies the correctness of the user input. If an error is found, then no operation will be performed.
        
        :param rarity: 位阶。不区分大小写。有以下取值：<br>Tier (case insensitive), which has the following values:
        
            - 0 | "silver": 白银阶（Silver）
            - 1 | "gold": 黄金阶（Gold）
            - 2 | "prismatic": 棱彩阶（Prismatic）
            
            该参数可同时接受整数或字符串类型。<br>This parameter accepts both an integer or a string.
        :type rarity: int | str
        :param selection: 选择界面数据。需要同时包含被提供的锻造器类型和已选择的锻造器类型。<br>Selection screen data. Both supplied and selected anvil types should be included.
        
            格式（Schemas）：{"anvilType": bool}
            - 锻造器类型不区分大小写。<br>Anvil type is case insensitive.
            
            示例（Example）：{"AH": False, "AD": True, "AP": False}
            
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
        #参数校验（Parameter verification）
        valid, message = self.verify_selection_record(rarity, selection)
        if not valid:
            print(message)
            return 1
        #准备一些常量（Prepare some constants）
        if isinstance(rarity, str):
            tier: str = rarity.lower().capitalize()
        elif rarity == 0:
            tier = "Silver"
        elif rarity == 1:
            tier = "Gold"
        else:
            tier = "Prismatic"
        anvilType_case_map: dict[str, str] = {key.lower(): key for value in self.STAT_ANVIL_SNAPSHOT_TEMPLATE.values() for key in value} #用户输入的时候允许忽略大小写，在方法内部还原大小写（The user input is case sensitive. Restore the case inside this method）
        selection_norm: dict[str, bool] = {anvilType_case_map[anvilType.lower()]: selected for (anvilType, selected) in selection.items()} #标准化锻造器类型的大小写（Normalize the case of anvil type）
        latest_anvilType_selected: str = "" #这一行语句只是为了满足严格的类型检查（This statement is only needed by the strict type checking mode）
        #递增（Increment）
        for (anvilType, selected) in selection_norm.items():
            self.statAnvilCounter_supply[tier][anvilType] += 1
            if selected: #由于上述参数校验过程，这个分支一定会执行一次（Because of the above parameter verification, this branch will be definitely run once）
                latest_anvilType_selected = anvilType
                self.statAnvilCounter_select[tier][anvilType] += 1
        self.snapshot() #将最近一次变动保存到序列中（Save the latest change into the sequence）
        self.latest_selection = (tier, latest_anvilType_selected, tuple(selection_norm.keys()))
        self.selections.append(self.latest_selection)
        return 0
    
    def extend(self, records: list[tuple[int | str, dict[str, bool]]]) -> int:
        '''
        批量导入多条选择记录。<br>Import multiple selection records in batch.
        
        :param records: 选择记录列表。每条选择记录是一个二元组：<br>Selection record list. Each selection record is a two-tuple:
        
            - 1. 位阶，即`increment`方法的`rarity`参数。<br>Tier, also `rarity` parameter of `increment` method.
            - 2. 选择数据，即`increment`方法的`selection`参数。<br>Selection data, also `selection` parameter of `increment` method.
            
            注意，一旦有一条选择记录出现问题，所有的选择记录都无法导入。<br>Note that if there's any erroneous selection record, then no record will be imported.
        :type records: list[tuple[int | str, dict[str, bool]]]
        :return: 状态码。<br>Status code.
        
            - 0: 导入成功。<br>Import succeeded.
            - 1: 导入失败。<br>Import failed.
        :rtype: int
        '''
        #参数校验（Parameter verification）
        valid, message = self.verify_selection_recordList(records)
        if valid:
            for record in records:
                self.increment(record[0], record[1])
            return 0
        else:
            print(message)
            return 1
    
    def recall(self) -> None:
        '''
        撤销最近一次选择。<br>Revert the latest selection.
        '''
        if self.selection_count == 0:
            print("尚未做出选择。\nNo selection has been made.")
            return
        #递减（Decrement）
        tier, latest_anvilType_selected, anvilTypes_supplied = self.latest_selection
        self.statAnvilCounter_select[tier][latest_anvilType_selected] -= 1
        for anvilType in anvilTypes_supplied:
            self.statAnvilCounter_supply[tier][anvilType] -= 1
        #后处理（Post processing）
        self.selections.pop(-1)
        self.latest_selection = ("", "", ("", "", "")) if self.selection_count == 0 else self.selections[-1]
        self.statAnvilSequence_supply.pop(-1)
        self.statAnvilSequence_select.pop(-1)
        # self.statAnvilCounter_select = self.deepcopy_anvilCounter(self.statAnvilSequence_select[-1]) #为了便于追踪同一内存地址，这里没有使用此简化代码，而是手动实现递增的逆运算（For the convenience of tracing the same memory address, here this simplified code isn't used. Instead, a reserve operation is implemented manually above）
        # self.statAnvilCounter_supply = self.deepcopy_anvilCounter(self.statAnvilSequence_supply[-1])
    
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
        重置两类属性锻造器时间序列，并重置两类属性锻造器计数器。<br>Reset both stat anvil sequences. Meanwhile, reset both stat anvil counters.
        '''
        for anvilCountDict in self.statAnvilCounter_supply.values():
            for anvilType in anvilCountDict:
                anvilCountDict[anvilType] = 0
        for anvilCountDict in self.statAnvilCounter_select.values():
            for anvilType in anvilCountDict:
                anvilCountDict[anvilType] = 0
        self.statAnvilSequence_supply.clear()
        self.statAnvilSequence_select.clear()
        self.snapshot()
        self.selections.clear()
        self.latest_selection = ("", "", ("", "", ""))

    def organize_anvil_data(self, index: int = -1, phase: Literal["supply", "select"] = "select") -> dict[str, dict[str, dict[str, Any]]]:
        '''
        将某个属性锻造器快照进一步加工成一个另一个Python字典，以供`export`方法使用。<br>Further process a stat anvil snapshot into another Python dictionary to be used by `export` method.
        
        :param index: 快照下标。取值范围是`[-self.snapshot_count, self.snapshot_count - 1]`内的整数。<br>The index of the snapshot. Should be within `[-self.snapshot_count, self.snapshot_count - 1]` range.
        
            如果未指定，则处理当前状态。<br>If it's not specified, this function will try to organize the current status by default.
        :type index: int
        :param phase: 选择界面的状态。有以下取值：<br>Status of the selection screen, which has the following values:
        
            - supply: 被提供的。<br>Supplied.
            - select: （☆）已选择的。<br>Selected.
        :type phase: Literal["supply", "select"]
        :return: 用于输出为文本的属性锻造器数据。<br>Stat anvil data to be output as a text.
        
            一级键是位阶。二级键是锻造器类型。三级键值对是锻造器相关字段。<br>Each Level-1 key is a tier. Each Level-2 key is an anvil type. Each Level-3 key-value pair is an anvil field.
        :rtype: dict[str, dict[str, dict[str, Any]]]
        '''
        statAnvilCounter_supply: dict[str, dict[str, int]] = self.statAnvilSequence_supply[index]
        statAnvilCounter_select: dict[str, dict[str, int]] = self.deepcopy_anvilCounter(self.statAnvilSequence_select[index])
        if self.selection_count > 0 and index != 0:
            selection_index: int = index if index < 0 else index - 1 #时间序列中包含原始快照，因此其长度比选择列表大1（The sequence contains the initial snapshot, so its length is greater than the selection list by 1）
            current_tier, current_anvilType_selected, anvilTypes_supplied = self.selections[selection_index]
            if phase == "supply": #只是提供而未选择，则应删除选择的一个锻造器（If anvils are provided but no decision has been made, the recently selected anvil should be deleted）
                statAnvilCounter_select[current_tier][current_anvilType_selected] -= 1
        anvil_block: dict[str, dict[str, dict[str, Any]]] = {
            "Silver": {
                "AH": {
                    "desc_zh": "技能急速碎片",
                    "desc_en": "Ability Haste Shard",
                    "supply_count": statAnvilCounter_supply["Silver"]["AH"],
                    "select_count": statAnvilCounter_select["Silver"]["AH"]
                },
                "AD": {
                    "desc_zh": "攻击力碎片",
                    "desc_en": "Attack Damage Shard",
                    "supply_count": statAnvilCounter_supply["Silver"]["AD"],
                    "select_count": statAnvilCounter_select["Silver"]["AD"]
                },
                "AP": {
                    "desc_zh": "法术强度碎片",
                    "desc_en": "Ability Power Shard",
                    "supply_count": statAnvilCounter_supply["Silver"]["AP"],
                    "select_count": statAnvilCounter_select["Silver"]["AP"]
                },
                "Hybrid2": {
                    "desc_zh": "力量碎片",
                    "desc_en": "Mighty Shard",
                    "supply_count": statAnvilCounter_supply["Silver"]["Hybrid2"],
                    "select_count": statAnvilCounter_select["Silver"]["Hybrid2"]
                },
                "AM": {
                    "desc_zh": "护甲碎片",
                    "desc_en": "Armor Shard",
                    "supply_count": statAnvilCounter_supply["Silver"]["AM"],
                    "select_count": statAnvilCounter_select["Silver"]["AM"]
                },
                "MR": {
                    "desc_zh": "魔法抗性碎片",
                    "desc_en": "Magic Resist Shard",
                    "supply_count": statAnvilCounter_supply["Silver"]["MR"],
                    "select_count": statAnvilCounter_select["Silver"]["MR"]
                },
                "Hybrid3": {
                    "desc_zh": "坚不可摧碎片",
                    "desc_en": "Unbreakable Shard",
                    "supply_count": statAnvilCounter_supply["Silver"]["Hybrid3"],
                    "select_count": statAnvilCounter_select["Silver"]["Hybrid3"]
                },
                "HP": {
                    "desc_zh": "生命值碎片",
                    "desc_en": "Health Shard",
                    "supply_count": statAnvilCounter_supply["Silver"]["HP"],
                    "select_count": statAnvilCounter_select["Silver"]["HP"]
                },
                "AS": {
                    "desc_zh": "攻击速度碎片",
                    "desc_en": "Attack Speed Shard",
                    "supply_count": statAnvilCounter_supply["Silver"]["AS"],
                    "select_count": statAnvilCounter_select["Silver"]["AS"]
                },
                "Hybrid1": {
                    "desc_zh": "迅捷碎片",
                    "desc_en": "Swiftness Shard",
                    "supply_count": statAnvilCounter_supply["Silver"]["Hybrid1"],
                    "select_count": statAnvilCounter_select["Silver"]["Hybrid1"]
                },
                "CSC": {
                    "desc_zh": "暴击碎片",
                    "desc_en": "Critical Strike Shard",
                    "supply_count": statAnvilCounter_supply["Silver"]["CSC"],
                    "select_count": statAnvilCounter_select["Silver"]["CSC"]
                },
                "LTH": {
                    "desc_zh": "穿甲碎片",
                    "desc_en": "Lethality Shard",
                    "supply_count": statAnvilCounter_supply["Silver"]["LTH"],
                    "select_count": statAnvilCounter_select["Silver"]["LTH"]
                },
                "MRPF": {
                    "desc_zh": "法术穿透碎片",
                    "desc_en": "Magic Penetration Shard",
                    "supply_count": statAnvilCounter_supply["Silver"]["MRPF"],
                    "select_count": statAnvilCounter_select["Silver"]["MRPF"]
                },
                "Random": {
                    "desc_zh": "两个随机碎片",
                    "desc_en": "Two Random Shards",
                    "supply_count": statAnvilCounter_supply["Silver"]["Random"],
                    "select_count": statAnvilCounter_select["Silver"]["Random"]
                }
            },
            "Gold": {
                "AH": {
                    "desc_zh": "技能急速碎片",
                    "desc_en": "Ability Haste Shard",
                    "supply_count": statAnvilCounter_supply["Gold"]["AH"],
                    "select_count": statAnvilCounter_select["Gold"]["AH"]
                },
                "AD": {
                    "desc_zh": "攻击力碎片",
                    "desc_en": "Attack Damage Shard",
                    "supply_count": statAnvilCounter_supply["Gold"]["AD"],
                    "select_count": statAnvilCounter_select["Gold"]["AD"]
                },
                "AP": {
                    "desc_zh": "法术强度碎片",
                    "desc_en": "Ability Power Shard",
                    "supply_count": statAnvilCounter_supply["Gold"]["AP"],
                    "select_count": statAnvilCounter_select["Gold"]["AP"]
                },
                "Hybrid2": {
                    "desc_zh": "力量碎片",
                    "desc_en": "Mighty Shard",
                    "supply_count": statAnvilCounter_supply["Gold"]["Hybrid2"],
                    "select_count": statAnvilCounter_select["Gold"]["Hybrid2"]
                },
                "AM": {
                    "desc_zh": "护甲碎片",
                    "desc_en": "Armor Shard",
                    "supply_count": statAnvilCounter_supply["Gold"]["AM"],
                    "select_count": statAnvilCounter_select["Gold"]["AM"]
                },
                "MR": {
                    "desc_zh": "魔法抗性碎片",
                    "desc_en": "Magic Resist Shard",
                    "supply_count": statAnvilCounter_supply["Gold"]["MR"],
                    "select_count": statAnvilCounter_select["Gold"]["MR"]
                },
                "Hybrid3": {
                    "desc_zh": "坚不可摧碎片",
                    "desc_en": "Unbreakable Shard",
                    "supply_count": statAnvilCounter_supply["Gold"]["Hybrid3"],
                    "select_count": statAnvilCounter_select["Gold"]["Hybrid3"]
                },
                "HP": {
                    "desc_zh": "生命值碎片",
                    "desc_en": "Health Shard",
                    "supply_count": statAnvilCounter_supply["Gold"]["HP"],
                    "select_count": statAnvilCounter_select["Gold"]["HP"]
                },
                "AS": {
                    "desc_zh": "攻击速度碎片",
                    "desc_en": "Attack Speed Shard",
                    "supply_count": statAnvilCounter_supply["Gold"]["AS"],
                    "select_count": statAnvilCounter_select["Gold"]["AS"]
                },
                "Hybrid1": {
                    "desc_zh": "迅捷碎片",
                    "desc_en": "Swiftness Shard",
                    "supply_count": statAnvilCounter_supply["Gold"]["Hybrid1"],
                    "select_count": statAnvilCounter_select["Gold"]["Hybrid1"]
                },
                "CSC": {
                    "desc_zh": "暴击碎片",
                    "desc_en": "Critical Strike Shard",
                    "supply_count": statAnvilCounter_supply["Gold"]["CSC"],
                    "select_count": statAnvilCounter_select["Gold"]["CSC"]
                },
                "LTH": {
                    "desc_zh": "穿甲碎片",
                    "desc_en": "Lethality Shard",
                    "supply_count": statAnvilCounter_supply["Gold"]["LTH"],
                    "select_count": statAnvilCounter_select["Gold"]["LTH"]
                },
                "MRPF": {
                    "desc_zh": "法术穿透碎片",
                    "desc_en": "Magic Penetration Shard",
                    "supply_count": statAnvilCounter_supply["Gold"]["MRPF"],
                    "select_count": statAnvilCounter_select["Gold"]["MRPF"]
                },
                "Random": {
                    "desc_zh": "两个随机碎片",
                    "desc_en": "Two Random Shards",
                    "supply_count": statAnvilCounter_supply["Gold"]["Random"],
                    "select_count": statAnvilCounter_select["Gold"]["Random"]
                },
                "ShardBladeAnvils": {
                    "desc_zh": "打磨碎片之刃",
                    "desc_en": "Hone Shardblade",
                    "supply_count": statAnvilCounter_supply["Gold"]["ShardBladeAnvils"],
                    "select_count": statAnvilCounter_select["Gold"]["ShardBladeAnvils"]
                }
            },
            "Prismatic": {
                "MS": {
                    "desc_zh": "移动速度碎片",
                    "desc_en": "Move Speed Shard",
                    "supply_count": statAnvilCounter_supply["Prismatic"]["MS"],
                    "select_count": statAnvilCounter_select["Prismatic"]["MS"]
                },
                "HPSZ": {
                    "desc_zh": "生命值与体型碎片",
                    "desc_en": "Health and Size Shard",
                    "supply_count": statAnvilCounter_supply["Prismatic"]["HPSZ"],
                    "select_count": statAnvilCounter_select["Prismatic"]["HPSZ"]
                },
                "CSD": {
                    "desc_zh": "暴击伤害碎片",
                    "desc_en": "Critical Damage Shard",
                    "supply_count": statAnvilCounter_supply["Prismatic"]["CSD"],
                    "select_count": statAnvilCounter_select["Prismatic"]["CSD"]
                },
                "OMV": {
                    "desc_zh": "全能吸血碎片",
                    "desc_en": "Omnivamp Shard",
                    "supply_count": statAnvilCounter_supply["Prismatic"]["OMV"],
                    "select_count": statAnvilCounter_select["Prismatic"]["OMV"]
                },
                "TNC": {
                    "desc_zh": "韧性碎片",
                    "desc_en": "Tenacity Shard",
                    "supply_count": statAnvilCounter_supply["Prismatic"]["TNC"],
                    "select_count": statAnvilCounter_select["Prismatic"]["TNC"]
                },
                "HSP": {
                    "desc_zh": "治疗与护盾强度碎片",
                    "desc_en": "Heal & Shield Power Shard",
                    "supply_count": statAnvilCounter_supply["Prismatic"]["HSP"],
                    "select_count": statAnvilCounter_select["Prismatic"]["HSP"]
                },
                "AMP": {
                    "desc_zh": "护甲穿透碎片",
                    "desc_en": "Armor Penetration Shard",
                    "supply_count": statAnvilCounter_supply["Prismatic"]["AMP"],
                    "select_count": statAnvilCounter_select["Prismatic"]["AMP"]
                },
                "MRPP": {
                    "desc_zh": "法术穿透碎片",
                    "desc_en": "Magic Penetration Shard",
                    "supply_count": statAnvilCounter_supply["Prismatic"]["MRPP"],
                    "select_count": statAnvilCounter_select["Prismatic"]["MRPP"]
                },
                "Gold": {
                    "desc_zh": "好运碎片",
                    "desc_en": "Fortune Shard",
                    "supply_count": statAnvilCounter_supply["Prismatic"]["Gold"],
                    "select_count": statAnvilCounter_select["Prismatic"]["Gold"]
                },
                "GoldRoundLoss": {
                    "desc_zh": "关爱包裹",
                    "desc_en": "Care Package",
                    "supply_count": statAnvilCounter_supply["Prismatic"]["GoldRoundLoss"],
                    "select_count": statAnvilCounter_select["Prismatic"]["GoldRoundLoss"]
                },
                "Pristine": {
                    "desc_zh": "碎片增幅碎片1",
                    "desc_en": "Shardholder Value Shard 1",
                    "supply_count": statAnvilCounter_supply["Prismatic"]["Pristine"],
                    "select_count": statAnvilCounter_select["Prismatic"]["Pristine"]
                },
                "UpgradeShards": {
                    "desc_zh": "碎片增幅碎片2",
                    "desc_en": "Shardholder Value Shard 2",
                    "supply_count": statAnvilCounter_supply["Prismatic"]["UpgradeShards"],
                    "select_count": statAnvilCounter_select["Prismatic"]["UpgradeShards"]
                }
            }
        }
        return anvil_block

    def export(self, index: int = -1, phase: str = "select", skip_anvilTypes: Optional[list[tuple[int | str, str]]] = None, highlight_change: bool = True) -> tuple[str, list[str], list[int]]:
        '''
        将当前状态的属性锻造器选择情况导出为一段文本。<br>Export the current stat anvil selection into a piece of text.
        
        :param index: 快照下标。取值范围是`[-self.snapshot_count, self.snapshot_count - 1]`内的整数。<br>The index of the snapshot. Should be within `[-self.snapshot_count, self.snapshot_count - 1]` range.
        
            如果未指定，则默认导出最近一次选择。<br>If it's not specified, this function will try to export the latest selection by default.
        :type index: int
        :param phase: 选择界面的状态。有以下取值：<br>Status of the selection screen, which has the following values:
        
            - supply: 被提供的。<br>Supplied.
            - select: （☆）已选择的。<br>Selected.
        :type phase: Literal["supply", "select"]
        :param skip_anvilTypes: 导出时跳过的锻造器类型。如果未指定，则全部导出<br>Anvil types to skip when exporting. If unspecified, then export all anvil data.
        
            每个元素是一个二元组。第一个元素是位阶，第二个元素是锻造器类型（不区分大小写）。<br>Each element is a two-tuple, where the first element is tier and the second element is anvil type (case insensitive).
            
            例如，由于打磨碎片之刃、好运碎片、关爱包裹和碎片增幅碎片不存在于海克斯大乱斗中，因此在导出海克斯大乱斗的锻造器文本时，应指定该参数为以下内容：<br>For example, because Hone Shardblade, Fortune Shard, Care Package and Shardholder Value Shard don't exist in ARAM: Mayhem, to export the anvil text of an ARAM: Mayhem game, this parameter should be specified as the following:
            - [("Gold", "ShardBladeAnvils"), ("Prismatic", "Gold"), ("Prismatic", "GoldRoundLoss"), ("Prismatic", "Pristine"), ("Prismatic", "UpgradeShards")]
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
        if phase != "supply" and phase != "select":
            print("阶段错误。\nPhase error.")
            return ("", [], [])
        skip_anvilTypes_norm: dict[str, set[str]] = {}
        if skip_anvilTypes != None:
            anvilTier_case_map: dict[str, str] = {"0": "Silver", "1": "Gold", "2": "Prismatic"} | {key.lower(): key for key in self.STAT_ANVIL_SNAPSHOT_TEMPLATE} #用户输入的时候允许忽略大小写，在方法内部还原大小写（The user input is case sensitive. Restore the case inside this method）
            anvilType_case_map: dict[str, str] = {key.lower(): key for value in self.STAT_ANVIL_SNAPSHOT_TEMPLATE.values() for key in value}
            if all(map(lambda x: str(x).lower() in anvilTier_case_map, list(map(lambda x: x[0], skip_anvilTypes)))) and all(map(lambda x: x.lower() in anvilType_case_map, list(map(lambda x: x[1], skip_anvilTypes)))):
                for (tier, anvilType) in skip_anvilTypes:
                    tier_norm: str = anvilTier_case_map[str(tier).lower()]
                    anvilType_norm: str = anvilType_case_map[anvilType.lower()]
                    if not tier_norm in skip_anvilTypes_norm:
                        skip_anvilTypes_norm[tier_norm] = set()
                    skip_anvilTypes_norm[tier_norm].add(anvilType_norm)
            else:
                print("跳过的锻造器类型格式错误。\nSkipped anvil type format error.")
                return ("", [], [])
        #准备一些常量（Prepare some constants）
        if self.selection_count == 0 or index == 0: #如果是最初的快照，则没有做出任何选择（If the user chooses to export the initial snapshot, then no selection had been made yet）
            current_tier: str = ""
            current_anvilType_selected: str = ""
            anvilTypes_supplied: tuple[str, ...] = ("", "", "")
        else:
            selection_index: int = index if index < 0 else index - 1 #时间序列中包含原始快照，因此其长度比选择列表大1（The time sequence contains the initial snapshot, so its length is greater than the selection list by 1）
            current_tier, current_anvilType_selected, anvilTypes_supplied = self.selections[selection_index]
        #构建文本（Construct the text and the run length array）
        ##标题和表头（Title and header）
        title_line: str = "<b>              属性锻造器数量统计表"
        header_line: str = "\r位阶\t属性锻造器类别\t数量</b>"
        ##表格主体（Table body）
        anvil_block: dict[str, dict[str, dict[str, Any]]] = self.organize_anvil_data(index = index, phase = phase) #当`phase`为“supply”时，当前选择的锻造器类型的总数会减1（When `phase` is "supply", the total number of the current anvil type will be reduced by 1）
        ###白银阶（Silver）
        silver_block: str = "<normal>" #normal标签为自定义标签，表示不添加任何格式（"normal" tag is a custom tag, which means no format is added）
        silver_append_counter: int = 0
        for (anvilType, anvilData) in anvil_block["Silver"].items():
            if "Silver" in skip_anvilTypes_norm and anvilType in skip_anvilTypes_norm["Silver"]:
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
            if "Gold" in skip_anvilTypes_norm and anvilType in skip_anvilTypes_norm["Gold"]:
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
            if "Prismatic" in skip_anvilTypes_norm and anvilType in skip_anvilTypes_norm["Prismatic"]:
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

def copy_stat_anvil_sequence_PR(seq: StatAnvilSequence, begIndex: int = 0) -> None:
    '''
    一个自制的将属性锻造器序列快照复制到Premiere Pro软件的文本框中的函数。<br>A DIY function that copies a stat anvil snapshot into a textbox in Premiere Pro.
    
    由于PR剪贴板的参数太过复杂，用户应当根据自身需求修改该函数的主体。可参考《属性锻造器时间序列处理》Jupyter笔记本。<br>Since parameters PR clipboard are way too complex, users should modify this function's body based on personal demands. Users may refer to "属性锻造器时间序列处理.ipynb".
    
    :param seq: 属性锻造器时间序列对象。<br>A `StatAnvilSequence` object.
    :type seq: StatAnvilSequence
    :param begIndex: 遍历快照的起始索引。默认为0。<br>The beginning index to traverse the snapshots. 0 by default.
    
        当程序因异常退出或者用户误操作时，这个参数能快速进展到最新的状态。<br>When the program exits due to an exception or the user has made a mistake, this parameter is very helpful to quickly progress to the latest status.
    :type begIndex: int
    '''
    anvilTypes_to_skip: list[tuple[int | str, str]] = [("Silver", "Random"), ("Gold", "Random"), ("Gold", "ShardBladeAnvils"), ("Prismatic", "Gold"), ("Prismatic", "GoldRoundLoss"), ("Prismatic", "Pristine"), ("Prismatic", "UpgradeShards")]
    print("本函数将遍历所有的序列节点，将其文本信息依次导出为适用于Adobe Premiere Pro软件的剪贴板。\nThis function will traverse all sequence nodes one by one and export the text into a clipboard window that can be pasted into Adobe Premiere Pro.\n\n在准备就绪后，按下回车键以复制初始状态的文本。\nWhen you're ready, press Enter to copy the text of the initial snapshot.")
    quit: bool = False #标记是否提前退出循环（Marks whether to exit the loop in advance）
    for i in range(begIndex, seq.snapshot_count): #遍历序列节点（Traverse sequence nodes）
        for phase in ["supply", "select"]: #遍历选择阶段（Traverse selection phases）
            if i == 0 and phase == "supply":
                continue #第一个快照的被提供的和已选择的属性锻造器快照数据完全相同，因为是初始化的，数据全都是0（The supplied and selected stat anvil snapshot data are the same, for all data in both of them have been initialized as 0）
            #获取文本和格式信息（Get text and encoding）
            anvilTable, formatArray, styleSheet_runLengthArray = seq.export(index = i, phase = phase, skip_anvilTypes = anvilTypes_to_skip)
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
            paragraphSheet_default: dict[str, dict[str, Any]] = {"ParagraphSheet": {"DefaultStyleSheet": 0, "Properties": {"Justification": 0}}, "Adjustments": {"Axis": [1.0, 0.0, 1.0], "XY": [0.0, 0.0]}}
            paragraphSheet_runArray: list[dict[str, dict[str, Any]]] = [copy.deepcopy(paragraphSheet_default) for _ in range(paragraph_count)] #36段（36 paragraphs）
            paragraphSheet_runLengthArray: list[int] = list(map(len, anvilTable.splitlines(keepends = True))) #段数和上面一致（The number of paragraphs is coincident with above）
            ###样式表单（Style sheet）
            styleSheet_default: dict[str, dict[str, Any]] = {"StyleSheet": {"StyleSheetData": {"Font": 0, "FontSize": 30.0, "FauxBold": False, "FauxItalic": False, "AutoLeading": False, "Leading": 36.0, "Tracking": 0, "AutoKerning": True, "Kerning": 0, "BaselineShift": 0.0, "FontCaps": 0, "FontBaseline": 0, "Underline": False, "Ligatures": True, "Tsume": 0.0, "FillColor": {"Type": 1, "Values": [1.0, 1.0, 1.0, 1.0]}, "StrokeColor": {"Type": 1, "Values": [1.0, 1.0, 1.0, 1.0]}, "FillFlag": True, "StrokeFlag": False, "FillFirst": False, "YUnderline": 1, "OutlineWidth": 4.0, "HindiNumbers": False}}}
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
                {"InternalName": "Photoshop6MojiKumiSet1"},
                {"InternalName": "Photoshop6MojiKumiSet2"},
                {"InternalName": "Photoshop6MojiKumiSet3"},
                {"InternalName": "Photoshop6MojiKumiSet4"}
            ]
            mojiKumiSet_encoded: list[dict[str, bytes]] = [{key: unicode2PSText(value) for (key, value) in elem.items()} for elem in mojiKumiSet]
            ###段落表单集合（Paragraph sheet set）
            paragraphSheetSet_element_default: dict[str, Any] = {"Name": unicode2PSText("Normal"), "DefaultStyleSheet": 0, "Properties": {"Justification": 0, "FirstLineIndent": 0.0, "StartIndent": 0.0, "EndIndent": 0.0, "SpaceBefore": 0.0, "SpaceAfter": 0.0, "AutoHyphenate": True, "HyphenatedWordSize": 6, "PreHyphen": 2, "PostHyphen": 2, "ConsecutiveHyphens": 8, "Zone": 36.0, "WordSpacing": [0.8, 1.0, 1.33], "LetterSpacing": [0.0, 0.0, 0.0], "GlyphSpacing": [1.0, 1.0, 1.0], "AutoLeading": 1.2, "LeadingType": 0, "Hanging": False, "Burasagari": False, "KinsokuOrder": 0, "EveryLineComposer": False}}
            paragraphSheetSet: list[dict[str, Any]] = [paragraphSheetSet_element_default]
            ###样式表单集合（Style sheet set）
            styleSheetSet_element_default: dict[str, Any] = {"Name": unicode2PSText("Normal"), "StyleSheetData": {"Font": 2, "FontSize": 12.0, "FauxBold": False, "FauxItalic": False, "AutoLeading": True, "Leading": 27.0, "HorizontalScale": 1.0, "VerticalScale": 1.0, "Tracking": 0, "AutoKerning": True, "Kerning": 0, "BaselineShift": 0.0, "FontCaps": 0, "FontBaseline": 0, "Underline": False, "Strikethrough": False, "Ligatures": True, "DLigatures": False, "BaselineDirection": 2, "Tsume": 0.0, "StyleRunAlignment": 2, "Language": 0, "NoBreak": False, "FillColor": {"Type": 1, "Values": [1.0, 0.0, 0.0, 0.0]}, "StrokeColor": {"Type": 1, "Values": [1.0, 0.0, 0.0, 0.0]}, "FillFlag": True, "StrokeFlag": False, "FillFirst": True, "YUnderline": 1, "OutlineWidth": 1.0, "CharacterDirection": 0, "HindiNumbers": False, "Kashida": 1, "DiacriticPos": 2}}
            styleSheetSet: list[dict[str, Any]] = [styleSheetSet_element_default]
            ###字体集（Font set）
            fontSet: list[dict[str, Any]] = [
                {"Name": "MicrosoftYaHei", "Script": 3, "FontType": 1, "Synthetic": 0},
                {"Name": "MicrosoftYaHei-Bold", "Script": 3, "FontType": 1, "Synthetic": 0},
                {"Name": "Myriad-Roman", "Script": 0, "FontType": 0, "Synthetic": 0},
                {"Name": "AdobeInvisFont", "Script": 0, "FontType": 0, "Synthetic": 0}
            ]
            fontSet_encoded: list[dict[str, Any]] = [{key: unicode2PSText(value) if key == "Name" else value for (key, value) in elem.items()} for elem in fontSet]
            ###资源字典（Resource dictionary）
            resourceDict: dict[str, Any] = {"KinsokuSet": kinsokuSet_encoded, "MojiKumiSet": mojiKumiSet_encoded, "TheNormalStyleSheet": 0, "TheNormalParagraphSheet": 0, "ParagraphSheetSet": paragraphSheetSet, "StyleSheetSet": styleSheetSet, "FontSet": fontSet_encoded, "SuperscriptSize": 0.583, "SuperscriptPosition": 0.333, "SubscriptSize": 0.583, "SubscriptPosition": 0.333, "SmallCapSize": 0.7}
            ###汇总赋值（Consolidated assignment）
            photoshopText_data: dict[str, Any] = {
                "ParagraphTextEditor": {
                    "Editor": {
                        "Text": editor_text
                    },
                    "ParagraphRun": {
                        "DefaultRunData": {"ParagraphSheet": {"DefaultStyleSheet": 0, "Properties": {}}, "Adjustments": {"Axis": [1.0, 0.0, 1.0], "XY": [0.0, 0.0]}},
                        "RunArray": paragraphSheet_runArray,
                        "RunLengthArray": paragraphSheet_runLengthArray,
                        "IsJoinable": 1
                    },
                    "StyleRun": {
                        "DefaultRunData": {"StyleSheet": {"StyleSheetData": {}}},
                        "RunArray": styleSheet_runArray,
                        "RunLengthArray": styleSheet_runLengthArray,
                        "IsJoinable": 2
                    },
                    "GridInfo": {"GridIsOn": False, "ShowGrid": False, "GridSize": 18.0, "GridLeading": 22.0, "GridColor": {"Type": 1, "Values": [0.0, 0.0, 0.0, 1.0]}, "GridLeadingFillColor": {"Type": 1, "Values": [0.0, 0.0, 0.0, 1.0]}, "AlignLineHeightToGridFlags": False},
                    "AntiAlias": 0,
                    "UseFractionalGlyphWidths": False,
                    "Rendered": {"Version": 1, "Shapes": {"WritingDirection": 0, "Children": []}}
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
                {"0": {"99": "CoolTypeFont", "0": {"0": unicode2PSText("MicrosoftYaHei"), "1": 3, "2": 1, "5": unicode2PSText("Version 6.31")}}},
                {"0": {"99": "CoolTypeFont", "0": {"0": unicode2PSText("MicrosoftYaHei-Bold"), "1": 3, "2": 1, "5": unicode2PSText("Version 6.31")}}},
                {"0": {"99": "CoolTypeFont", "0": {"0": unicode2PSText("Myriad-Roman"), "2": 0}}}
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
            styleSheetSet_element_engine_default: dict[str, dict[str, Any]] = {"0": {"0": unicode2PSText("Normal"), "6": {"0": 2, "1": 12.0, "2": False, "3": False, "4": True, "5": 27.0, "6": 1.0, "7": 1.0, "8": 0, "9": 0.0, "10": 0.0, "11": 1, "12": 0, "13": 0, "14": 0, "15": 0, "16": 0, "17": 0.0, "18": True, "19": False, "20": False, "21": False, "22": False, "23": False, "24": False, "25": False, "26": False, "27": False, "28": False, "29": False, "30": 0, "31": False, "32": False, "33": False, "34": False, "35": 2, "36": 0.0, "37": 2, "38": 0, "39": 0, "40": False, "41": 2, "42": 0, "43": {"0": 0.5}, "44": 2, "45": 2, "46": 7, "47": 0, "48": 0, "49": -1.0, "50": -1.0, "51": 0, "52": False, "53": {"99": "SimplePaint", "0": {"0": 1, "1": [1.0, 0.0, 0.0, 0.0]}}, "54": {"99": "SimplePaint", "0": {"0": 1, "1": [1.0, 0.0, 0.0, 0.0]}}, "55": {"99": "SimpleBlender"}, "56": True, "57": False, "58": True, "59": False, "60": False, "61": 0, "62": 0, "63": 1.0, "64": 4.0, "65": 0.0, "66": [], "67": [], "68": 0, "69": 0, "70": 0, "71": 4, "72": 0.0, "73": 0.0, "74": False, "75": False, "76": False, "77": True, "78": True, "79": {"99": "SimplePaint", "0": {"0": 1, "1": [1.0, 1.0, 1.0, 0.0]}}, "80": False, "81": 0, "82": 3.0, "83": 3.0, "84": False, "85": 0, "86": {"99": "SimpleCustomFeature"}, "87": 100.0, "88": True, "92": 0.0, "95": {"0": 0.0, "1": 0}, "96": True}}}
            styleSheetSet_engine: list[dict[str, dict[str, Any]]] = [styleSheetSet_element_engine_default]
            ###段落表单集合（Paragraph sheet set）
            paragraphSheetSet_element_engine_default: dict[str, dict[str, Any]] = {"0": {"0": unicode2PSText("Normal"), "5": {"0": 0, "1": 0.0, "2": 0.0, "3": 0.0, "4": 0.0, "5": 0.0, "6": 1, "7": 1.2, "8": 0, "9": True, "10": 6, "11": 2, "12": 2, "13": 0, "14": 36.0, "15": True, "16": 0.5, "17": [0.8, 1.0, 1.33], "18": [0.0, 0.0, 0.0], "19": [1.0, 1.0, 1.0], "20": 6, "21": False, "22": 0, "23": False, "24": 0, "25": 0, "27": "nil", "26": False, "28": "nil", "29": False, "30": {}, "31": 36.0, "32": {}, "33": 0, "34": 7, "35": 1, "36": "nil", "37": 0, "38": False, "39": 0, "40": 2, "41": 0}}}
            paragraphSheetSet_engine: list[dict[str, dict[str, Any]]] = [paragraphSheetSet_element_engine_default]
            ###段落表单（Paragraph sheet）
            paragraphSheet_engine_default: dict[str, dict[str, Any]] = {"0": {"0": unicode2PSText(""), "5": {"0": 0, "31": 160.0, "33": 0}, "6": 0}}
            paragraphSheet_runArray_engine: list[dict[str, dict[str, Any]]] = [copy.deepcopy(paragraphSheet_engine_default) for _ in range(paragraph_count)]
            paragraphSheet_runLengthArray_engine: list[int] = paragraphSheet_runLengthArray
            ###样式表单（Style sheet）
            serializedTextProperties: dict[str, str] = {
                "normal": "QAEAAAAAAABEMyIRDAAAAAAABgAKAAQABgAAAGQAAAAAAF4AHAAUABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADwAAAAgAAAAAABsABwBeAAAAAAAAARQAAAAAAAABHAAAADQAAAAAAAAAWP///1z///9g////ZP///wEAAAAEAAAADgAAAE1pY3Jvc29mdFlhSGVpAAABAAAADAAAAAgADAAEAAgACAAAAAgAAABAAAAAAQAAAGEANgAYAAAAFAAAAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAwAAAAIAAQANgAAAAIAAAAQAAAAEAAAAAAAgEAAAPBB9P////j////8////BAAEAAQAAAA=",
                "b": "RAEAAAAAAABEMyIRDAAAAAAABgAKAAQABgAAAGQAAAAAAF4AHAAUABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADwAAAAgAAAAAABsABwBeAAAAAAAAARQAAAAAAAABHAAAADgAAAAAAAAAVP///1j///9c////YP///wEAAAAEAAAAEwAAAE1pY3Jvc29mdFlhSGVpLUJvbGQAAQAAAAwAAAAIAAwABAAIAAgAAAAIAAAAQAAAAAEAAABhADYAGAAAABQAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAMAAAACAAEADYAAAACAAAAEAAAABAAAAAAAIBAAADwQfT////4/////P///wQABAAEAAAA",
                "green": "WAEAAAAAAABEMyIRDAAAAAAABgAKAAQABgAAAGQAAAAAAF4AHAAUABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADwAAAAgAAAAAABsABwBeAAAAAAAAARQAAAAAAAABHAAAADQAAAAAAAAAXP///2D///9k////aP///wEAAAAEAAAADgAAAE1pY3Jvc29mdFlhSGVpAAABAAAADAAAAAgADAAEAAgACAAAAAgAAABAAAAAAQAAAGEANgAcAAAAGAAUAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAwAAAAIAAQANgAAAAIAAAAUAAAAGAAAAAAAgEAoAAAAAADwQfz///8EAAQABAAAAAQABgAEAAAAAAAKAAgABgAAAAcACgAAAAAAAAA=",
                "yellow": "WAEAAAAAAABEMyIRDAAAAAAABgAKAAQABgAAAGQAAAAAAF4AHAAUABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADwAAAAgAAAAAABsABwBeAAAAAAAAARQAAAAAAAABHAAAADQAAAAAAAAAXP///2D///9k////aP///wEAAAAEAAAADgAAAE1pY3Jvc29mdFlhSGVpAAABAAAADAAAAAgADAAEAAgACAAAAAgAAABAAAAAAQAAAGEANgAcAAAAGAAUAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAwAAAAIAAQANgAAAAIAAAAUAAAAGAAAAAAAgEAoAAAAAADwQfz///8EAAQABAAAAAQABgAEAAAAAAAKAAgAAAAAAAcACgAAAAAAAAA=",
                "purple": "UAEAAAAAAABEMyIRDAAAAAAABgAKAAQABgAAAGQAAAAAAF4AHAAUABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADwAAAAgAAAAAABsABwBeAAAAAAAAARQAAAAAAAABHAAAADQAAAAAAAAAWP///1z///9g////ZP///wEAAAAEAAAADgAAAE1pY3Jvc29mdFlhSGVpAAABAAAADAAAAAgADAAEAAgACAAAAAgAAABAAAAAAQAAAGEANgAcAAAAGAAUAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAwAAAAIAAQANgAAAAIAAAAUAAAAFAAAAAAAgEAgAAAAAADwQfj////8////BAAEAAQAAAAIAAgAAAAHAAgAAAAAAAAA"
            } #预定义一些样式的序列化文本属性（Predefine some styles' serialized text properties）
            styleSheet_engine_default: dict[str, dict[str, Any]] = {"0": {"0": unicode2PSText(""), "5": 0, "6": {"0": 0, "1": 22.5, "2": False, "3": False, "4": False, "5": 27.0, "8": 0, "9": 0.0, "12": 0, "13": 0, "16": 0, "18": True, "36": 0.0, "53": {"99": "SimplePaint", "0": {"0": 1, "1": [1.0, 1.0, 1.0, 1.0]}}, "54": {"99": "SimplePaint", "0": {"0": 1, "1": [1.0, 1.0, 1.0, 1.0]}}, "56": True, "57": False, "58": False, "63": 4.0, "70": 1, "77": True, "78": False, "86": {"99": "ATEWrapperStyleParamFB", "0": b""}, "92": 0.0}}}
            styleSheet_engine_default["0"]["6"]["86"]["0"] = unicode2PSText(serializedTextProperties["normal"])
            styleSheet_runArray_engine: list[dict[str, dict[str, Any]]] = [copy.deepcopy(styleSheet_engine_default) for _ in range(nFormats)]
            for j in range(nFormats):
                textFormat: str = formatArray[j]
                if textFormat == "normal":
                    pass
                elif textFormat == "b":
                    styleSheet_runArray_engine[j]["0"]["6"]["0"] = 1 #微软雅黑粗体（MicrosoftYaHei bold）
                    styleSheet_runArray_engine[j]["0"]["6"]["86"]["0"] = unicode2PSText(serializedTextProperties["b"]) #该字符串无法推导得出。用户必须事先在Premiere Pro软件中先套用相关样式，再获取对应的字符串（This string can't be derivated for now. Users must apply the corresponding format in Premiere Pro app and then get this string）
                elif textFormat == "yellow":
                    styleSheet_runArray_engine[j]["0"]["6"]["53"]["0"]["1"] = [1.0, 1.0, 1.0, 0.0] #黄色（Yellow）
                    styleSheet_runArray_engine[j]["0"]["6"]["86"]["0"] = unicode2PSText(serializedTextProperties["yellow"])
                elif textFormat == "purple":
                    styleSheet_runArray_engine[j]["0"]["6"]["53"]["0"]["1"] = [1.0, 1.0, 0.0, 1.0] #紫色（Purple）
                    styleSheet_runArray_engine[j]["0"]["6"]["86"]["0"] = unicode2PSText(serializedTextProperties["purple"])
                elif textFormat == "green":
                    styleSheet_runArray_engine[j]["0"]["6"]["53"]["0"]["1"] = [1.0, 0.0, 1.0, 0.0] #绿色（Green）
                    styleSheet_runArray_engine[j]["0"]["6"]["86"]["0"] = unicode2PSText(serializedTextProperties["green"])
            ###汇总赋值（Consolidated assignment）
            adobeTextEngine_data: dict[str, Any] = {
                "98": {"0": 12},
                "0": {
                    "1": {"0": fontSet_engine},
                    "4": {"0": kinsokuSet_engine, "1": [{"0": 0}, {"0": 1}]},
                    "5": {"0": styleSheetSet_engine, "1": [{"0": 0}]},
                    "6": {"0": paragraphSheetSet_engine, "1": [{"0": 0}]},
                    "8": {}
                },
                "1": {
                    "0": editor_text,
                    "1": {"0": paragraphSheet_runArray_engine, "1": paragraphSheet_runLengthArray_engine},
                    "2": {"0": styleSheet_runArray_engine, "1": styleSheet_runLengthArray},
                    "3": {"0": [{}], "1": [635]},
                    "4": {"0": [{}], "1": [634]},
                    "6": {"0": [{}], "1": [634]}
                }
            }
            adobeTextEngine_text: bytes = restore_PRClipboard_Adobe_Text_Engine_v2(adobeTextEngine_data)
            win32clipboard.SetClipboardData(clipboard_formats["Adobe Text Engine 2.0"], adobeTextEngine_text)
            ##对象链接与嵌入私有数据（OLE Private Data）
            bOlePrivateData: bytes = b"\x00\x00\x00\x00\x08\x01\x00\x00\x01\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\r\x00\xf6\x80\x9b\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\xff\xff\xff\xff\x01\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00y\xc3\xf6\x80\x9b\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\xff\xff\xff\xff\x01\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00z\xc3\xf6\x80\x9b\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\xff\xff\xff\xff\x01\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            win32clipboard.SetClipboardData(clipboard_formats["Ole Private Data"], bOlePrivateData)
            ##区域设置（CF_LOCALE）
            win32clipboard.SetClipboardData(clipboard_formats["CF_LOCALE"], b"\x04\x08\x00\x00")
            ##ANSI文本（CF_TEXT）
            win32clipboard.SetClipboardData(clipboard_formats["CF_TEXT"], anvilTable.encode("ansi"))
            ##GBK文本（CF_OEMTEXT）
            win32clipboard.SetClipboardData(clipboard_formats["CF_OEMTEXT"], anvilTable.encode("gbk"))
            win32clipboard.CloseClipboard()
            
            #打印快照内容以便比对（Print snapshot content for the sake of comparison）
            print(anvilTable.replace("\r", "\n"))
            
            print("[%d/%d][%s]已复制快照。 | Snapshot copied." %(i + 1, seq.snapshot_count, phase))
            print("按回车键以继续，或者输入任意非空字符串以退出。\nPress Enter to continue, or submit any non-empty string to quit.")
            quit = bool(input())
            if quit:
                break
        if quit:
            break

def main() -> None:
    '''
    主函数。仅在运行此脚本时执行。<br>Main function. It's only called when this program is run.
    '''
    global clipboard_formats
    #初始化属性锻造器时间序列对象（Initialize a `StatAnvilSequence` object）
    anvilSequence: StatAnvilSequence = StatAnvilSequence()
    #初始化剪贴板格式数据（Initialize clipboard data format）
    clipboard_formats = get_clipboard_formats()
    expected_formats: list[str] = ["DataObject", "CF_UNICODETEXT", "Photoshop Text", "Adobe Text Engine 2.0", "Ole Private Data", "CF_LOCALE", "CF_TEXT", "CF_OEMTEXT"]
    if not all(key in clipboard_formats for key in expected_formats):
        print("剪贴板数据格式不符。请确保您在运行程序前复制了某个PR文本框中的一段文字。\nClipboard format mismatched. Please make sure you've copied some text in a PR textbox before running this program.")
        return
    #读取选择序列（Read the selection sequence）
    print("请输入一个属性锻造器选择序列文件的路径。\nPlease input the path of a stat anvil selection sequence file.")
    while True:
        file_path: str = input()
        if file_path == "":
            continue
        elif file_path == chr(4):
            return
        else:
            if not os.path.exists(file_path):
                print("文件不存在。请重新输入。\nFile not found. Please try again.")
            elif not os.path.isfile(file_path):
                print("请输入一个文件的路径。\nPlease input the path of a file.")
            else:
                try:
                    with open(file_path, "r", encoding = "utf-8") as fp:
                        tmp: Any = json.load(fp)
                except json.JSONDecodeError:
                    print("格式不合法。请更换文件。\nIllegal format. Please change a file.")
                else:
                    if isinstance(tmp, list) and all(map(lambda x: isinstance(x, dict) and "rarity" in x and "selection" in x and anvilSequence.verify_selection_record(x["rarity"], x["selection"]), tmp)):
                        selection_list: list[dict[str, Any]] = tmp
                        break
                    else:
                        print("选择序列文件格式错误。请重新输入。\nSelection sequence format mismatch. Please try again.")
    #导入选择序列（Import the selection sequence）
    selection_list_norm: list[tuple[int | str, dict[str, bool]]] = [(selection["rarity"], selection["selection"]) for selection in selection_list]
    status: int = anvilSequence.extend(selection_list_norm)
    if status == 0:
        #逐时间点复制（Timewise copy）
        copy_stat_anvil_sequence_PR(anvilSequence, begIndex = 280)

def test() -> None:
    '''
    主函数。仅在运行此脚本时执行。<br>Main function. It's only called when this program is run.
    '''
    anvilSequence: StatAnvilSequence = StatAnvilSequence()
    anvilTable, formatArray, style_runLengthArray = anvilSequence.export(phase = "select", highlight_change = True)
    print(anvilTable.replace("\r", "\n"))
    print(formatArray)
    print(style_runLengthArray)

if __name__ == "__main__":
    main()
    # test()
