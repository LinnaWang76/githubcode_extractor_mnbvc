# githubcode_mnbvc
github code dataset from the mnbvc project

# Install the requirements
```
pip install -r requirements.txt
```


### 输出的jsonl格式说明

1. 每个jsonl文件，其大小略大于500MB。每行是一个文本的数据，对应一个代码仓库里的文本文件。
2. 对于每一行数据，其最高层次结构如下。
```json
{
    "来源":"github",
    "仓库名":"esbatmop/MNBVC",
    "path":"/main/README.md",
    "文件名":"README.md",
    "ext": "md",
    "size":123456,
    "原始编码":"GBK",
    "md5":"文件的md5值",
    "text": "文件的内容，utf8格式"
}

```
