import os
from tqdm import tqdm
import pandas as pd
from pandas import Series, DataFrame
import pymysql

class BuyInfo(object):

    def __init__(self, code, buy_arr, sold_arr):
        self.code = code
        self.buy_date = buy_arr[0]
        self.buy_close = buy_arr[2]
        self.sold_date = sold_arr[0]
        self.sold_close = sold_arr[2]
        self.diff = self.sold_close - self.buy_close

    def to_string(self):
        buy_close_ = " "*(6-len(str(self.buy_close))) + str(self.buy_close)
        sold_close_ = " "*(6-len(str(self.sold_close))) + str(self.sold_close)
        diff_ = format(self.diff, '.2f')
        diff_ = " "*(6 - len(diff_)) + diff_
        return "[%s]在%s日买入, 收盘价为%s, %s日卖出, 收盘价为%s, 差价为%s" % (self.code, \
            self.buy_date, buy_close_, self.sold_date, sold_close_, diff_)

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

    def __init__(self, file_path_prefix, code=None, n=14, end_date='0000-00-00'):
        self.file_path_prefix = file_path_prefix        # 日线数据文件目录前缀
        self.code = code                                # 股票代码 （可选）
        self.n = n                                      # 公式中的天数， 默认14
        self.end_date = end_date                        # 最早的日期， 默认无下限
        self.all_cci = {}                               # 保存每只股票的 cci
        self.all_buy_res = []                           # 保存购买的结果
    
    def analyze_all(self):
        file_list = os.listdir(self.file_path_prefix)
        for index in tqdm(range(len(file_list))):
            filename = file_list[index]     # 取出文件名
            self.code = filename[0:6]
            self.analyze_one()
        # self.save_to_txt()
        # self.save_to_mysql()

    def analyze_one(self):
        try:
            df = pd.read_csv(self.file_path_prefix + str(self.code) + '.csv', encoding='gbk')
        except:
            print('文件'+str(self.code) + '.csv 打开失败')
            return False
        df['cci'] = ''
        # 截取 self.n 行, 默认从第0行开始
        start = 0

        # 截取第一个数据块， 保存 data 数组
        # datas = [{}]
        # rows = rows = df[0:self.n-1]
        # # 数据不足  或  日期已小于截止日期
        # if len(rows) < self.n or rows.values[0][0] < self.end_date:
        #     return None
        # flag = True     # 标记数据是否完整
        # for index, row in rows.iterrows():
        #     if row['最高价'] == 'None' or row['最高价'] == 0 or row['最低价'] == 'None' \
        #         or row['最低价'] == 0 or row['收盘价'] == 'None' or row['收盘价'] == 0:
        #         flag = False
        #     datas.append({'high':row['最高价'], 'low': row['最低价'], 'close': row['收盘价']})
        # if not flag:
        #     return None
        # while True:
        #     flag = True
        #     datas.pop(0)
        #     try:
        #         high, low, close = df.loc[start, '最高价'], df.loc[start, '最低价'], df.loc[start, '收盘价']
        #     except:
        #         break
        #     if high == 'None' or high == '0' \
        #         or low == 'None' or low == '0' \
        #         or close == 'None' or close == '0':
        #         flag = False
        #     new_line = {
        #         'high':  high,
        #         'low': low,
        #         'close': close
        #     }
        #     if flag:
        #         datas.append(new_line)
        #         cci_calculate = CCICalculate(datas)
        #         cci = cci_calculate.get_cci()
        #     else:
        #         cci = 0
        #     df.loc[start, 'cci'] = cci
        #     start += 1

        
        # 每 n 行为一个块， 每次进一行
        while True:
            # 截取 start ~ start + n
            rows = df[start:start+self.n]
            # 数据不足  或  日期已小于截止日期
            if len(rows) < self.n or rows.values[0][0] < self.end_date:
                break

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
            df.loc[start, 'cci'] = cci
            start += 1
        df.to_csv(self.file_path_prefix + str(self.code) + '.csv', index=False, encoding='gbk')
        

    def save_to_mysql(self):
        # 连接数据库
        name = "root"
        passsword = ""
        db = pymysql.connect('localhost', name, passsword, charset='utf8')
        cursor = db.cursor()
        cursor.execute('use shares')

        file_list = os.listdir(self.file_path_prefix)
        # 遍历保存的csv文件
        print('正在储存至mysql')
        for index in tqdm(range(len(file_list))):
            filename = file_list[index]     # 取出文件名
            code = filename[0:6]
            try:
                df = pd.read_csv(self.file_path_prefix + filename, encoding='gbk')
            except:
                print('文件'+str(code) + '.csv 打开失败')
                return False
            tb_name = "_" + str(code)
            try:
                cursor.execute("alter table %s add `cci` varchar(20)" % tb_name)
            except:
                pass
            for index, row in df.iterrows():
                try:
                    sqltxt = "UPDATE %s SET `cci` = %s WHERE `日期` = '%s'" % (tb_name, row['cci'], row['日期'])
                    cursor.execute(sqltxt)
                except:
                    pass

    def save_to_txt(self):
        file_handle=open('cci.txt',mode='w', encoding="utf-8")
        file_handle.write(str(self.all_cci))

    def test_buy(self):
        '''
            < -100 ， 后一天买入， > 100 后一天卖出
        '''
        print("正在测试购买")
        file_list = os.listdir(self.file_path_prefix)
        for index in tqdm(range(len(file_list))):
            filename = file_list[index]     # 取出文件名
            code = filename[0:6]
            try:
                df = pd.read_csv(self.file_path_prefix + filename, encoding='gbk')
            except:
                print('文件'+str(code) + '.csv 打开失败')
                return False
            rows = df.values[::-1]  # 倒转数组
            
            flag = False    # 标记是否已找到 < -100 的， 
            buy = False
            sold = False
            buy_arr = []
            sold_arr = []
            for row in rows:
                # 判断前一天是否满足 <-100可以买入
                if buy:
                    buy_arr = [row[0], row[2], row[3]]
                    if row[2] == 0 or row[3] == 0:      # 为缺失数据
                        flag = False
                    buy = False
                if sold:    
                    # do Sold
                    sold_arr = [row[0], row[2], row[3]]
                    if row[2] != 0 and row[3] != 0:
                        buy_info = BuyInfo(code, buy_arr, sold_arr)
                        self.all_buy_res.append(buy_info)
                    # print(buy_info.to_string())
                    sold = False
                    buy_arr = []
                    sold_arr = []
                if not flag:        # 没找到 < -100 的， 寻找
                    if row[2] < -100:
                        buy = True
                        flag = True
                else:               # 已经找到 < -100的， 找 > 100的来卖出
                    if row[2] > 100:
                        sold = True
                        flag = False
        self.show_buy_res()

    def test_buy_2(self):
        '''
        # 在达到 <-100 的峰值的后一天买入， > 100 峰值的后一天卖出
        '''
        file_list = os.listdir(self.file_path_prefix)
        for index in tqdm(range(len(file_list))):
            filename = file_list[index]     # 取出文件名
            code = filename[0:6]
            try:
                df = pd.read_csv(self.file_path_prefix + filename, encoding='gbk')
            except:
                print('文件'+str(code) + '.csv 打开失败')
                return False
            rows = df.values[::-1]  # 倒转数组

            flag = False    # 是否已经找到 < -100的
            buy = False
            sold = False
            buy_arr = []
            sold_arr = []
            yesterday_cci = 0
            for row in rows:
                if buy:
                    buy_arr = [row[0], row[2], row[3]]
                    if row[2] == 0 or row[3] == 0:      # 为缺失数据
                        flag = False
                    buy = False
                if sold:    
                    # do Sold
                    sold_arr = [row[0], row[2], row[3]]
                    if row[2] != 0 and row[3] != 0:
                        buy_info = BuyInfo(code, buy_arr, sold_arr)
                        self.all_buy_res.append(buy_info)
                    # print(buy_info.to_string())
                    sold = False
                    buy_arr = []
                    sold_arr = []
                if flag:
                    if row[2] > 100 and row[2] < yesterday_cci:
                        sold = True
                        flag = False
                else:
                    if row[2] < -100 and row[2] > yesterday_cci:
                        buy = True
                        flag = True
                yesterday_cci = row[2]
        self.show_buy_res()

    def show_buy_res(self):
        rate = 0
        for item in self.all_buy_res:
            if item.diff > 0:
                rate += 1
            print(item.to_string())
        rate /= len(self.all_buy_res)
        rate = format(rate*100, '.4f') + '%'
        print("总共有%s种满足条件的情况， 盈利的几率为%s" % (len(self.all_buy_res), rate))


if __name__ == '__main__':
    file_path_prefix = 'H:\\sharesDatas\\kline\\'
    # file_path_prefix = 'F:\\files\\sharesDatas\\kline\\'
    code = '000001'
    end_date = '2017-01-01'
    cci_analyze = CCIAnalyze(file_path_prefix, end_date=end_date, code=code)

    cci_analyze.analyze_all()
    # for cci in ccis['ccis'][::-1]:
    #     print(cci)
    # cci_analyze.analyze_all()
    # cci_analyze.save_to_mysql()
    # cci_analyze.test_buy_2()
    