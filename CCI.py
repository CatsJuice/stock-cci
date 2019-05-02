import os
from tqdm import tqdm
import pandas as pd
from pandas import Series, DataFrame

# 单只股票的CCI类
class StockCCI(object):

    def __init__(self):
        pass

# TYP:=(HIGH+LOW+CLOSE)/3;
# CCI:(TYP-MA(TYP,N))/(0.015*AVEDEV(TYP,N));
# 这个公式可能有点毛病， 或许是我理解有问题吧， 这个公式计算值基本超过 1000
class CCICalculate_2(object):

    def __init__(self, high, low, close, typs):
        self.high = high
        self.low = low 
        self.close = close
        self.typs = typs

    def get_typ(self):
        return (self.high + self.low + self.close) / 3
    
    def get_ma(self):
        i = 1
        sum = 0
        for typ in self.typs:
            sum += (typ-i)
            i += 1
        return sum / i
    
    def get_avedev(self):
        average = 0
        for typ in self.typs:
            average += typ
        average /= len(self.typs)
        sum = 0
        for typ in self.typs:
            delta = typ-average if typ > average else average-typ
            sum += delta
        return sum / len(self.typs)

    def get_cci(self):
        return (self.get_typ() - self.get_ma()) / (0.015 * self.get_avedev())

class CCICalculate(object):

    def __init__(self, datas):
        self.datas = datas

    # TPi= (Highi+Lowi+Closei3) / 3
    def get_tpi(self, i):
        return (self.datas[i]['high'] + self.datas[i]['low'] + self.datas[i]['close']) / 3

    # MA=∑n(i=1)TPi / n
    def get_ma(self):
        ma = 0
        for i in range(len(self.datas)):
            ma += self.get_tpi(i)
        return ma / len(self.datas)
    
    # MD=∑n(i=1)|TPi−MA| / n
    def get_md(self):
        md = 0
        for i in range(len(self.datas)):
            md += (self.get_tpi(i) - self.get_ma()) if self.get_tpi(i) > self.get_ma() else (self.get_ma() - self.get_tpi(i))
        return md / len(self.datas)

    # CCI=TPn−MA / 0.015 * MD
    def get_cci(self):
        return (self.get_tpi(0) - self.get_ma()) / (0.015 * self.get_md())
    
# 分析类
class CCIAnalyze(object):

    def __init__(self, file_path_prefix, cci_path_prefix, code=None, n=14, end_date='0000-00-00'):
        self.file_path_prefix = file_path_prefix        # 日线数据文件目录前缀
        self.cci_path_prefix = cci_path_prefix          # cci数据文件前缀
        self.code = code                                # 股票代码 （可选）
        self.n = n                                      # 公式中的天数， 默认14
        self.end_date = end_date                        # 最早的日期， 默认无下限
        self.all_cci = {}                               # 保存每只股票的 cci
    
    def analyze_all(self):
        file_list = os.listdir(self.file_path_prefix)
        for index in tqdm(range(len(file_list))):
            filename = file_list[index]     # 取出文件名
            self.code = filename[0:6]
            self.analyze_one()
        self.save_to_txt()

    def analyze_one(self):
        try:
            df = pd.read_csv(self.file_path_prefix + str(self.code) + '.csv', encoding='gbk')
        except:
            print('文件'+str(self.code) + '.csv 打开失败')
            return False
        
        # 截取 self.n 行, 默认从第0行开始
        start = 0

        stock_cci = []
        
        col = {
            'date': [],
            'code': [],
            'CCI': [],
            'close': []
        }

        # 每 n 行为一个块， 每次进一行
        while True:
            # 截取 start ~ start + n
            rows = df[start:start+self.n]
            # 数据不足  或  日期已小于截止日期
            if len(rows) < self.n or rows.values[0][0] < self.end_date:
                break

            # 遍历截取的块 计算typs
            datas = []
            flag = True     # 标记数据是否完整
            for index, row in rows.iterrows():
                if row['最高价'] == 'None' or row['最高价'] == 0 or row['最低价'] == 'None' \
                    or row['最低价'] == 0 or row['收盘价'] == 'None' or row['收盘价'] == 0:
                    flag = False
                datas.append({'high':row['最高价'], 'low': row['最低价'], 'close': row['收盘价']})
            if flag:
                cci_calculate = CCICalculate(datas)
                cci = cci_calculate.get_cci()
            else:
                cci = 0
            col['CCI'].append(cci)
            col['date'].append(rows.values[0][0])
            col['code'].append(self.code)
            col['close'].append(rows.values[0][3])
            stock_cci.append({'date':rows.iloc[0]['日期'], 'cci': cci, 'close': rows.iloc[0]['收盘价']})
            start += 1


        self.all_cci[str(self.code)] = stock_cci
        df_new_col = DataFrame(col, columns=['date','code','CCI','close'])
        df_new_col.to_csv(self.cci_path_prefix + str(self.code) + '.csv', mode='w', index=False)    # 存储至csv
    
    def save_to_txt(self):
        file_handle=open('cci.txt',mode='w', encoding="utf-8")
        file_handle.write(str(self.all_cci))

    def test_buy(self):
        print("正在测试购买")
        file_list = os.listdir(self.cci_path_prefix)
        for index in tqdm(range(len(file_list))):
            filename = file_list[index]     # 取出文件名
            code = filename[0:6]
            try:
                df = pd.read_csv(self.cci_path_prefix + filename, encoding='gbk')
            except:
                print('文件'+str(code) + '.csv 打开失败')
                return False
            rows = df.values[::-1]  # 倒转数组
            
            flag = False    # 标记是否已找到 < -100 的， 
            for row in rows:
                if not flag:
                    if row[2] < -100:
                        pass



if __name__ == '__main__':
    file_path_prefix = 'F:\\files\\sharesDatas\\kline\\'
    cci_path_prefix = 'F:\\files\\sharesDatas\\cci\\'
    code = '000001'
    end_date = '2018-01-01'
    cci_analyze = CCIAnalyze(file_path_prefix, cci_path_prefix=cci_path_prefix, end_date=end_date, code=code)

    # cci_analyze.analyze_all()
    # for cci in ccis['ccis'][::-1]:
    #     print(cci)
    # cci_analyze.analyze_all()

    cci_analyze.test_buy()
    