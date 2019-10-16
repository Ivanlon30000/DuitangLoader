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
    def __init__(self, label, save_path, max_amount, max_workers=8, epoch=50, log_out=False):
        """
        :param label: 批量下载的标签
        :param save_path: 保存图片的路径
        :param max_amount: 最大张数
        """
        self.label = label
        self.save_path = save_path
        self.max_amount = max_amount
        self.max_workers = max_workers
        self.epoch = epoch
        self.log_out = log_out

        self.file_lock = Lock()
        self.count = 1
        self.ptr = 0

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
        while self.count < self.max_amount:
            # get 请求, 返回一个 json 字符串, 包含了图片的地址
            res = get(url.format(label, self.ptr, self.epoch))
            # json 转 dict
            data_dict = loads(res.text)
            # 处理 dict, 提取有用信息
            objs = data_dict['data']['object_list']
            info = [(
                '{}_{}_{}'.format(obj['msg'], obj['id'], obj['add_datetime_pretty']),
                obj['photo']['path']
            ) for obj in objs]  # 数据结构: list[(相关信息, 图片路径)*N]

            self.count = self.count + len(info)
            self.ptr = self.ptr + self.epoch
            yield info
        else:
            return

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
        for info_list in self.gen_urls_by_label():
            for info in info_list:
                file_name, img_url = info
                # 命名文件
                file_name = DuitangDownloader.normalize_file_name(file_name) + img_url[img_url.rindex('.'):]
                # 创建线程
                t = pool.submit(self.__down_pic, img_url, file_name)
                ts.append(t)

    def run(self):
        """
        启动下载
        :return:
        """
        self.__loop()
        wait(self.ts)

if __name__ == '__main__':
    c = DuitangDownloader('四宫辉夜', 'D:\\workdir\\kaguya-sama_tmp', 250, log_out=True)
    c.run()