# githubcode_mnbvc
github code dataset from the mnbvc project

# Install the requirements
```
pip install -r requirements.txt
```


### 输出的jsonl格式说明

对于每一个仓库，他的json结构层次如下：

```python
{
    'name': '仓库名称',
    'files': ['文件的json'],
}
```

将每一行为一个文件，文件的json结构层次如下：

```python
{
    "name": "文件名称",
    "ext": "文件后缀",
    "path": "文件在仓库的相对路径",
    "size": "文件大小",
    "source_encoding": "文件的原始编码",
    "md5": "文件的md5值",
    "text": "文件的内容，utf8格式"
}
```
