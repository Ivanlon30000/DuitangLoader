# 堆糖图片批量下载 DuitangLoader
## 使用方法
### 控制台:  
`python DuitangLoader -s <关键词> -o <输出路径> [-a <最大图片数>] [-r <从某个位置开始>] [-l]`
  
参数解释:
```
-s --search: 关键词
-o --out_path: 输出路径
-a --max_amount: 张数限制, 缺省值 500
-l --log_out: 不打印 log, 默认打印
-t --max_workers: 线程数, 缺省值 8
-b --batch_size: 每次循环下载的图片数量, 缺省值 50 
-r --resume: 从某个图片指针开始, 缺省值 0 
-h --help: 帮助信息
```
  
### 函数调用
```python
from DuitangLoader import DuitangDownloader

# 以下列出的是缺省值
label = ...         # 标签/关键词
out_path = ...      # 输出路径
log = True          # 打印 log
amount = 500        # 最多爬取数量
max_workers = 8     # 线程数
batch_size = 50     # 每个循环的大小
resume = 0          # 从哪里开始

downer = DuitangDownloader(label, out_path,
              max_amount=amount,
              max_workers=max_workers,
              log_out=log,
              batch_size=batch_size,
              resume=resume)
ptr = downer.run()  # 跑!
print(ptr)          # 保存 ptr
```

> 其实只是想用来爬辉夜大小姐的图片的  
> 我永远喜欢辉夜大小姐.jpg  

![avatar](pics/kaguya-sama.jpeg)
