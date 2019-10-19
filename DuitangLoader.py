# -*- coding:utf-8 -*-
# Author: Ivanlon
# E-mail: ivanlon@foxmail.com

import os
from threading import Lock
from json import loads
import re
from concurrent.futures import ThreadPoolExecutor, wait

from requests import get
from urllib.parse import quote


class DuitangDownloader():
    def __init__(self, label, save_path, max_amount=500, max_workers=8, batch_size=50, log_out=False, resume=0):
        """
        :param label: 批量下载的标签
        :param save_path: 保存图片的路径
        :param max_amount: 最大张数
        """
        self.label = label
        self.save_path = save_path
        self.max_amount = max_amount
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.log_out = log_out

        self.file_lock = Lock()
        self.count = 0
        self.ptr = resume

        # 创建文件夹
        if not os.path.exists(save_path):
            os.makedirs(save_path)

        # 多线程
        self.pool = ThreadPoolExecutor(max_workers)
        self.ts = []

    def __down_pic(self, img_url, file_name, index):
        """
        下载图片
        :param img_url: 图片链接
        :param file_name: 文件名
        :return:
        """
        log_out = self.log_out
        if log_out:
            print('**\t[{}] {} 正在下载...'.format(index, file_name))
        r = get(img_url)
        with open(os.path.join(self.save_path, file_name), 'wb') as f:
            self.file_lock.acquire()
            f.write(r.content)
            self.file_lock.release()
        if log_out:
            print('**\t[{}] {} 下载完成.'.format(index, file_name))

    def gen_urls_by_label(self):
        """
        列出 label 相关的图片链接
        :return:
        """
        label = quote(self.label)
        url = 'https://www.duitang.com/napi/blog/list/by_search/?kw={}&start={}&limit={}'
        while True:
            # get 请求, 返回一个 json 字符串, 包含了图片的地址
            res = get(url.format(label, self.ptr, self.batch_size))
            # json 转 dict
            data_dict = loads(res.text)
            # 处理 dict, 提取有用信息
            objs = data_dict['data']['object_list']
            info = [(
                '{}_{}_{}'.format(obj['msg'], obj['id'], obj['add_datetime_pretty']),
                obj['photo']['path']
            ) for obj in objs]  # 数据结构: list[(相关信息, 图片路径)*N]
            # self.ptr = self.ptr + self.batch_size
            yield info

    @staticmethod
    def normalize_file_name(file_name):
        """
        处理异常文件名
        :param file_name:
        :return:
        """
        return re.sub(r'[\\/*?"<>|\s]', '_', file_name)

    def __loop(self):
        """
        循环控制
        :return:
        """
        ts = self.ts
        pool = self.pool
        gener = self.gen_urls_by_label()
        while gener is not None:
            info_list = gener.send(None)
            # 非空判断
            if info_list:
                for info in info_list:
                    file_name, img_url = info
                    # 命名文件
                    file_name = DuitangDownloader.normalize_file_name(file_name) + img_url[img_url.rindex('.'):]
                    # 创建线程
                    t = pool.submit(self.__down_pic, img_url, file_name, self.count)
                    ts.append(t)
                    self.count = self.count + 1
                    if self.count >= self.max_amount:
                        gener = None
                        break
            else:
                print('**\t没有关于 "{}" 的搜索结果, 请检查关键词是否有误.'.format(self.label))
                break

    def run(self):
        """
        启动下载
        :return:
        """
        self.__loop()
        wait(self.ts)
        self.ptr = self.ptr + self.count
        return self.ptr

if __name__ == '__main__':
    import sys
    import getopt

    try:
        opts, args = getopt.getopt(
            sys.argv[1:],
            'hs:o:a:lt:b:r:', ['help', 'search', 'out_path', 'max_amout', 'log_out', 'max_workers', 'batch_size', 'resume']
        )
    except getopt.GetoptError:
        print("语法错误:\n"
              "\tpython DuitangLoader -s <关键词> -o <输出路径> [-a <最大图片数>] [-l]\n"
              "\t输入 python DuitangLoader -h 获取帮助")
        sys.exit(2)

    label = None
    out_path = None
    log = True
    amount = 500
    max_workers = 8
    batch_size = 50
    resume = 0
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            help = """
用法 python DuitangLoader -s <关键词> -o <输出路径> [-a <最大图片数>] [-r <从某个位置开始>] [-l]
    -s --search: 关键词
    -o --out_path: 输出路径
    -a --max_amount: 张数限制, 缺省值 500
    -l --log_out: 不打印 log, 默认打印
    -t --max_workers: 线程数, 缺省值 8
    -b --batch_size: 每次循环下载的图片数量, 缺省值 50 
    -r --resume: 从某个图片指针开始, 缺省值 0 
    -h --help: 帮助信息"""
            print(help)
            sys.exit()
        elif opt in ('-s', '--search'):
            label = arg
            if not label:
                print('ERROR\t关键词输入有误')
        elif opt in ('-o', '--out_put'):
            out_path = arg
        elif opt in ('-a', '--max_amout'):
            amount = int(arg)
            if amount <= 0:
                print('ERROR\t张数限制必须大于 0')
        elif opt in ('-l', '--log_out'):
            log = False
        elif opt in ('-t', '--max_workers'):
            max_workers = int(arg)
            if max_workers <= 0:
                print('ERROR\t线程数必须大于 0')
        elif opt in ('-b', '--batch_size'):
            batch_size = int(arg)
            if batch_size <= 0:
                print('ERROR\tbatch_size 必须大于 0')
        elif opt in ('-r', '--resume'):
            resume = int(arg)
            if resume <= 0:
                print('ERROR\tresume 必须大于 0')

    if label is None or out_path is None:
        print("语法错误:\n"
              "\tpython DuitangLoader -s <关键词> -o <输出路径> [-a <最大图片数>] [-l]\n"
              "\t输入 python DuitangLoader -h 获取帮助")
        sys.exit(2)

    c = DuitangDownloader(label, out_path,
                          max_amount=amount,
                          max_workers=max_workers,
                          log_out=log,
                          batch_size=batch_size,
                          resume=resume
                          )
    ptr = c.run()
    print('**\t图片指针: {}'.format(ptr))