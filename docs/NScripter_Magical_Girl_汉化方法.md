## 魔法☆少女游戏整合方法

### 介绍
- **官方网站**: [魔法☆少女](http://www.magical-girl.jp/)
- **游戏引擎**: Nscripter

### 整合方法

1. **提取**:
    - 使用 SoraTranslator 的内置方法。
    - 将游戏定义文件放置在游戏文件夹中。
    - 确保文件中存在 `FIRST_BLOCK` 条目。如果提取失败，请打开原始文本，找到第一个块，并相应地更新 `FIRST_BLOCK` 条目。重新运行初始化过程。

2. **翻译**:
    - 按照 SoraTranslator 的标准翻译流程进行。
    - 注意: NScripter 不支持翻译文本中的英文字符或半角数字。

3. **整合**:
    - 在 SoraTranslator 中点击整合按钮。
    - SoraTranslator 会在 `game_folder/SoraTranslatorTemp` 下创建一个 `nscript` 文件夹。
    - 会出现一个目录选择器，选择此文件夹。
    - 在提示时保存 `nscript.dat` 文件。用这个新文件替换游戏文件夹中的原始 `nscript.dat` 文件。

4. **游戏可执行文件编码更改**:
    - 这一步比较复杂，需要使用 Ollydbg。
    - 为 `CreateFontA` 函数设置断点以定位字体设置。
    - 将所有相关情况下的值 `0x80` 更改为 `0x86`（角色名称、文本、选项等）。
    - 保存更改并运行游戏。
    - 详细指南请参考此 [视频教程](https://www.bilibili.com/video/BV1fy4y157im/)（中文）。
