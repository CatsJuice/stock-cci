# stock-cci
计算股票的cci， 判断cci指标的可行性


## 概念

> 顺势指标又叫CCI指标，CCI指标是美国股市技术分析 家唐纳德·蓝伯特(Donald Lambert)于20世纪80年代提出的，专门测量股价、外汇或者贵金属交易是否已超出常态分布范围。属于超买超卖类指标中较特殊的一种。波动于正无穷大和负无穷大之间。但是，又不需要以0为中轴线，这一点也和波动于正无穷大和负无穷大的指标不同。

## 指标用法

> **1.** 当`CCI`指标曲线在`+100`线～`-100`线的常态区间里运行时,`CCI`指标参考意义不大，可以用KDJ等其它技术指标进行研判。
> 
> **2.** 当`CCI`指标曲线从上向下突破`+100`线而重新进入常态区间时，表明市场价格的上涨阶段可能结束，将进入一个比较长时间的震荡整理阶段，应及时平多做空。
>
> **3.** 当`CCI`指标曲线从上向下突破`-100`线而进入另一个非常态区间（超卖区）时，表明市场价格的弱势状态已经形成，将进入一个比较长的寻底过程，可以持有空单等待更高利润。如果`CCI`指标曲线在超卖区运行了相当长的一段时间后开始掉头向上，表明价格的短期底部初步探明，可以少量建仓。`CCI`指标曲线在超卖区运行的时间越长，确认短期的底部的准确度越高。
>
> **4.** `CCI`指标曲线从下向上突破`-100`线而重新进入常态区间时，表明市场价格的探底阶段可能结束，有可能进入一个盘整阶段，可以逢低少量做多。
>
> **5.** `CCI`指标曲线从下向上突破`+100`线而进入非常态区间(超买区)时，表明市场价格已经脱离常态而进入强势状态，如果伴随较大的市场交投，应及时介入成功率将很大。
>
> **6.** `CCI`指标曲线从下向上突破`+100`线而进入非常态区间(超买区)后，只要`CCI`指标曲线一直朝上运行，表明价格依然保持强势可以继续持有待涨。但是，如果在远离`+100`线的地方开始掉头向下时，则表明市场价格的强势状态将可能难以维持，涨势可能转弱，应考虑卖出。如果前期的短期涨幅过高同时价格回落时交投活跃，则应该果断逢高卖出或做空。

## 公式

关于公式有两种：

**公式一：**
```
TYP:=(HIGH+LOW+CLOSE)/3;
CCI:(TYP-MA(TYP,N))/(0.015*AVEDEV(TYP,N));
```
该公式来自`通达信`， 含义如下：
```
TYP赋值:(最高价+最低价+收盘价)/3
输出CCI:(TYP-TYP的N日简单移动平均)/(0.015*TYP的N日平均绝对偏差)
```
**公式二：**


![cci公式](https://catsjuice.cn/index/src/markdown/stock/201905022239.png?20190504 "cci")

该公式摘录于[https://www.joinquant.com/view/community/detail/219](https://www.joinquant.com/view/community/detail/219)

程序中我采用的是**公式二**， 生成的CCI单独写入`.csv`文件



# 文件说明

- README.md
- CCI.py       //  主程序

**参数说明**
id | param | type | default | mean | demo | necessary
:--: | :--: | :--: | :--: | :--: |:--: | :--:
1 | `file_path_prefix` | `str` | `None` | 日线数据文件目录前缀 | `'F:\\files\\sharesDatas\\kline\\'` | `True`
2 | `cci_path_prefix` | `str` | `None` | CCI数据将要保存的目录前缀 | `'F:\\files\\sharesDatas\\cci\\'` | `True`
3 | `code` | `str` / `int` | `None` | 股票代码  | `000001` | `False`
4 | `end_date` | `str` | `'0000-00-00'` | 最早的日期（截止日期） | `'2009-01-01'` | `False`

调用 `analyze_all()`来计算所有股票的cci；

调用 `analyze_one()`来计算传入`code`的股票


# **总共设计了4个类如下：**

- `CCIAnalyze(object)` &emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&ensp;//&ensp;&ensp;CCI分析类
    - `analyze_all(self)` &emsp;&emsp;&emsp;&emsp;//&ensp;&ensp;分析所有股票
    - `analyze_one(self)` &emsp;&emsp;&emsp;&emsp;//&ensp;&ensp;分析一只股票
    - `test_buy(self)` &emsp;&emsp;&emsp;&emsp;&emsp;&ensp;//&ensp;&ensp;测试购买（策略一：在下文说明）
    - `test_buy_2(self)` &emsp;&emsp;&emsp;&emsp;&ensp;//&ensp;&ensp;测试购买（策略二：在下文说明）
- `CCICalculate(object)` &emsp;&emsp;&emsp;&emsp;&emsp;//&ensp;&ensp;根据公式二计算CCI
- `CCICalculate_2(object)`&emsp;&emsp;&emsp;&emsp;//&ensp;&ensp;根据公式一计算CCI
- `BuyInfo(object)`&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;//&ensp;&ensp;购买辅助类

# **测试结果**

在进行测试购买时， 采用的策略有2种，如下：

**策略一：**

对应`CCIAnalyze(object)`中的`test_buy(self)`方法， 当`CCI`向下突破`-100`时， 后一交易日**买入**， 等到`CCI`向上突破`100`时， 后一交易日**卖出**(由于计算出当日的CCI， 当日已不可**买入/卖出**，所以计算后一交易日**买入/卖出**)

**策略二：**

对应`CCIAnalyze(object)`中的`test_buy_2(self)`方法, 当`CCI`向下突破`-100`时， 继续观察， 等到向下达到第一个峰值时， 后一交易日**买入**，等到`CCI`向上突破`100`时， 继续观察， 等到向上达到第一个峰值时， 后一交易日**卖出**（和策略一一样， 计算出`CCI`后只能后一日买入， 而策略二不同的是， 要判断达到第一个峰值， 必须确定峰值后一日CCI降低， 所以测试时， 购买的是峰值的后`第2个`交易日）

经过若干次测试，分别使用的数据是`2019-01-01 ~ 2019-04-26`, `2018-01-01 ~ 2019-04-26`, `2017-01-01 ~ 2019-04-26`, 测试的结果, 购买策略一的收益率大概为`56%`, 可见这个指标有一定依据， 但是盈利的几率不够高; 而策略二的收益率大概为`57%`, 较策略一高一点， 但是依旧无法将其作为购买的唯一指标， 以下是某次运行结果的部分截图：

![CCI指标测试截图](https://catsjuice.cn/index/src/markdown/stock/201905031521.png "CCI指标测试截图")