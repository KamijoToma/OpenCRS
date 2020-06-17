# OpenCRS
> 为什么不录制一点m3u8呢？A very simple m3u8 live stream saver.

⚠Chinese language only

## 简介

`OpenCRS`是根据我个人开发的闭源`CRSPlus`软件进行脱敏和删节形成的开源软件，

它能够每天在规定的时间段内**保存**`m3u8`直播流文件，并在本地进行分段和索引文件重建，

从而实现直播流录制的功能。

## 技术原理

### 架构原理
通过`TaskManager`管理若干个`Worker`来运行解决队列中的`Task`对象。

`M3U8Downloader`类通过调用`TaskManager`对象的`queue.put()`方法添加任务对象，并随事件循环分配到

`Worker`中处理。

### M3U8分片解析原理
`M3U8Downloader`通过使用`m3u8`库循环解析目标m3u8索引文件从而获取分片列表，将其与上下文字典对比去重并

将新分片加入任务队列中下载。

### 定时保存原理
每个任务在下载完分片到内存之后都会立即将其保存到存储介质上；`M3U8Downloader`会定时添加`DumpM3U8FileTask`任务，

从而将内存中的M3U8列表文件转储到存储介质上。另外，在重置下载器时，也会添加此任务以强制保存列表文件。

### 定时下载原理
调用者通过向`M3U8Downloader`构造函数传入若干个`RecordLimitData`对象来限制录制时间。在`M3U8Downloader`线程主循环里，

程序会逐个判断该`RecordLimitData`对象是否允许在当前时间录制直播，只要在这若干个对象中有一个返回`True`即继续录制，

若全部返回`False`则停止录制，并另外执行转储m3u8索引文件的逻辑代码，由于篇幅所限不再赘述。

### 日志系统
日志系统使用Python3`logging`标准库，采用简单的函数包装（这可能会对性能产生一定影响），默认提供命令行Info输出以及日志文件Debug输出。

⚠经实际测试日志文件单日最大大小可达5MB，请注意及时归档日志文件。

## 后记
`CRSPlus`本身是在一年前写的小程序，当时的功能就是简单的调用`ffmpeg`录制直播流，慢慢的，单纯使用`ffmpeg`的一些弊病就显示出来了，

比如CPU占用率高，贸然CTRL-C可能会导致视频掉数据等等。在寒假的时候决定对这个程序进行大修，到现在位为止已经初具雏形了，

已经实现了定时录制和分段的功能，内存占用率降到大约10MB，CPU占用率降到20%（树莓派3B Plus），可以说是堪用的。以后想把它和QQ机器人

TG机器人结合起来，实现自动裁切录像，发送录像等功能。

### Thanks
谢谢你，帮我挺过了危机。 To the girl who helped me whenever and wherever.

感谢你们的支持。  To boys and girls who are proud of me.

Thanks.

## 开放源代码声明
本程序（`OpenCRS`）采用Apache License 2.0协议开源，请在遵守开源协议的前提下使用本软件。

## 关于本项目更改部分词汇的说明
鉴于Github即将更换掉`master` `slave`等词，本项目决定更改所有`brother`和`father`词汇到`sister`和`mother`词汇。

> 貌似只有生物有一个“姐妹染色单体”这种女性色彩的词汇吧

