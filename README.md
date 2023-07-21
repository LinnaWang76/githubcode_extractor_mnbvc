# githubcode_mnbvc
github code dataset from the mnbvc project

# Install the requirements
```
pip install -r requirements.txt
```
# Run Code
目前已有了针对googleSourceCode和GitHub仓库的代码语料提取脚本。

其中
- googleSourceCode代码的输入是仓库目录的父目录。相关参数需要在脚本内指定；
- GitHub代码的输入是仓库压缩包的父目录，相关参数以传参的形式确定，请通过运行`python converter_github.py --help`了解详情；
- 更多代码仓库预料提取可参照`converter.py`自行修改。

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
