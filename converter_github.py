#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os
import sys
import glob
import argparse
import json
import shutil
import logging
import time
import zipfile
import argparse
import hashlib as hs

from typing import List
from pathlib import PurePosixPath, Path
from charset_mnbvc import api

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

class CodeFileInstance:
    def __init__(self, repo_path: Path, file_path: Path, target_encoding="utf-8"):
        assert repo_path.exists(), f"{repo_path} is not exists."
        assert file_path.exists(), f"{file_path} is not exists."
        self.file_path = file_path
        file_bytes = file_path.read_bytes()
        relate_file_path = file_path.relative_to(repo_path)
        self._name = relate_file_path.stem
        self._ext = relate_file_path.suffix
        self._path = str(relate_file_path)
        self._encoding = api.from_data(file_bytes, mode=2)
        self.target_encoding = target_encoding
        text = None
        if self._encoding is not None:
            try:
                data = file_bytes.decode(encoding=self.target_encoding)
                text = data.encode(encoding=target_encoding).decode(encoding=target_encoding)
            except Exception as err:
                sys.stderr.write(f"Error: {str(err)}\n")
            # text = charset_mnbvc.api.convert_encoding(file_bytes, self._encoding, self.target_encoding)
            # text可能会转码失败，输出的还是原编码文本
        self._text = text
        self._size = file_path.stat().st_size
        self._md5 = self.__get_content_md5(file_bytes)

    @property
    def encoding(self):
        return self._encoding

    @property
    def size(self):
        return self._size

    @property
    def text(self):
        return self._text

    @property
    def name(self):
        return self._name

    @property
    def ext(self):
        return self._ext

    @property
    def path(self):
        return self._path

    @property
    def md5(self):
        return self._md5

    def __get_content_md5(self, content: bytes):
        m = hs.md5()
        m.update(content)
        return m.hexdigest()

    def get_dict(self):
        return {
            "plateform": "",
            "repo_name": "",
            "name": self.name+self.ext,
            "ext": self.ext,
            "path": self.path,
            "size": self.size,
            "source_encoding": self.encoding,
            "md5": self.md5,
            "text": self.text
        }


class Zipfile2JsonL:
    def __init__(self, output_root, target_encoding="utf-8", clean_src_file=False, plateform="github", author=""):
        if not os.path.exists(output_root): os.makedirs(output_root)
        self.output = Path(output_root)
        self.target_encoding = target_encoding
        self.max_jsonl_size = 500 * 1024 * 1024
        self.repo_list = list()
        self.chunk_counter = 0
        self.clean_src_file = clean_src_file
        self.plateform = plateform
        self.author = author

    def get_zipfile(self, file_path):
        '''如果是目录，直接当做仓库来处理。如果是zip文件，先解压再当做仓库处理。'''
        # 因为仓库压缩包的文件名不一定是仓库的文件名，所以专门指定一个路径
        repo_root = file_path.parent / ('zipout-' + file_path.stem)
        try:
            with zipfile.ZipFile(file_path, "r") as zf:
                zf.extractall(repo_root)
        except (FileExistsError, IsADirectoryError):  # 有的压缩包解压会报错。
            pass
        # 记录写入的文件，防止在某个仓库处理过程中停止后导致该仓库前面写过的文件重复写入
        temp_done_set = set()
        if os.path.exists(".temp_done"):
            with open(".temp_done","r",encoding="utf-8")as r:
                temp_done_set.update([i.strip() for i in r.readlines()])
        file_list = repo_root.rglob("**/*.*")
        for file in file_list:
            if not file.is_file(): continue
            if str(file) in temp_done_set:
                continue
            code = CodeFileInstance(repo_root, file, self.target_encoding)
            if code.encoding is None or not isinstance(code.text, str): continue
            dic = code.get_dict()
            dic["plateform"] = self.plateform
            dic["repo_name"] = self.author + "/" + file.relative_to(repo_root).parts[0]
            with open(self.get_jsonl_file(), "a", encoding="utf-8") as a1, open(".temp_done", "a", encoding="utf-8")as a2:
                a1.write(json.dumps(dic, ensure_ascii=False) + "\n")
                a2.write(str(file)+"\n")
            if os.path.getsize(self.get_jsonl_file()) > self.max_jsonl_size:
                self.chunk_counter += 1
        shutil.rmtree(repo_root)  # 删除解压出来的目录
        open(".temp_done","w",encoding="utf-8").close()

    def get_jsonl_file(self):
        return self.output / f"githubcode.{self.chunk_counter}.jsonl"

    def __call__(self, zip_path):
        #zip_path = Path(zip_path)
        assert zip_path.exists(), FileNotFoundError(str(root_dir))
        self.get_zipfile(zip_path)
        if self.clean_src_file is True:
            zip_path.unlink()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-z", "--zips", type=str, required=True, help="存放zip文件的目录")
    parser.add_argument("-j", "--jsonl", type=str, required=True, help="保存jsonl文件的目录")
    parser.add_argument("-t", "--tfile", type=str, default="./T", help="爬取时使用的T文件目录")
    parser.add_argument("-p", "--plateform", type=str, default="github", help="仓库来自哪个平台")
    parser.add_argument("--clean", action="store_true", default=False, help="是否删除源文件")

    args = parser.parse_args()
    zipfile_folder = args.zips
    jsonlfile_folder = args.jsonl
    Tfile_path = args.tfile
    plateform = args.plateform
    clean_src_file = args.clean

    print(args)

    ########################################################
    #zipfile_folder = "./zips"  # 存放zip文件的目录
    #jsonlfile_folder = "./out" # 保存jsonl文件的目录
    #Tfile_path = "./T"         # 那个T文件的地址
    #plateform = 'github'       # 仓库来自哪个平台
    #clean_src_file = False     # 是否删除源文件
    ########################################################

    p = Path(zipfile_folder)
    fs = p.glob("**/*.zip")
    id2author = dict()  # id（压缩包名）和作者对应
    with open(Tfile_path,"r",encoding="utf-8")as r: data=r.readlines()
    for line in data:
        k,v = line.split(", ")
        v = v.split("/")[3]
        id2author[k] = v
    for f in fs:
        # 已经下载好的仓库没有作者信息，以仓库id信息代替
        rid = f.stem
        print(rid, type(rid), type(f))
        #author = id2author[rid]
        #h = Zipfile2JsonL(jsonlfile_folder, clean_src_file=clean_src_file, plateform=plateform, author=author) 
        #h(f)
