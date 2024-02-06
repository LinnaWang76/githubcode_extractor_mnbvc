#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os
import sys
import argparse
import json
import shutil
import logging
import time
import glob
import zipfile
import hashlib as hs

from typing import List
from pathlib import PurePosixPath, Path
from charset_mnbvc import api
from datetime import datetime

#######################################################
# 其他变量
repos_folder = '/Users/washing/Downloads/google'    # 存放仓库们的目录，目录下是一个个仓库
output_folder = './out'    # jsonl输出的目录
clean_src_file = False     # 是否删除源文件
#######################################################

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
            "来源": "",
            "仓库名": "",
            "文件名": self.name,
            "ext": self.ext,
            "path": self.path,
            "size": self.size,
            "原始编码": self.encoding,
            "md5": self.md5,
            "text": self.text,
            "时间": datetime.now().strftime('%Y%m%d')
        }


#class RepoInstance:
#    def __init__(self, folder_name: str, plateform: str):
#        super(RepoInstance, self).__init__()
#        self.folder_name = folder_name
#        self._plateform = plateform
#        self._files: List[CodeFileInstance] = list()
#
#    @property
#    def name(self):
#        return self.folder_name
#
#    @property
#    def files(self):
#        return self._files
#
#    def files_append(self, file_obj: CodeFileInstance):
#        if file_obj.encoding is None:
#            return
#        if not isinstance(file_obj.text, str):
#            return
#        self._files.append(file_obj)
#
#    def get_dict_list(self):
#        ret = list()
#        for f in self.files:
#            dic = f.get_dict()
#            dic['plateform'] = self._plateform
#            dic['repo_name'] = self.name
#            # yield dic
#            ret.append(dic)
#        return ret
#        # return {
#        #     "repo": self.name,
#        #     "files": [f.get_dict() for f in self.files]
#        # }
#

class Zipfile2JsonL:
    def __init__(self, output_root, target_encoding="utf-8", clean_src_file=False, plateform="github"):
        if not os.path.exists(output_root): os.makedirs(output_root)
        self.output = Path(output_root)
        self.target_encoding = target_encoding
        self.max_jsonl_size = 500 * 1024 * 1024
        self.repo_list = list()
        self.chunk_counter = 0
        self.clean_src_file = clean_src_file
        self.plateform = plateform

    def parse_and_save(self, folder):
        repo_root = Path(folder)
        file_list = repo_root.rglob("**/*.*")
        for file in file_list:
            if file.is_file():
                code = CodeFileInstance(repo_root, file, self.target_encoding)
                if code.encoding is not None and isinstance(code.text, str):
                    dic = code.get_dict()
                    dic['来源'] = 'google'
                    dic['仓库名'] = repo_root.parts[-1]
                    with open(self.get_jsonl_file(), "a", encoding="utf-8")as a:
                        a.write(json.dumps(dic, ensure_ascii=False) + "\n")
                    if os.path.getsize(self.get_jsonl_file()) > self.max_jsonl_size:
                        self.chunk_counter += 1
        if self.clean_src_file:  # 删除源文件
            shutil.rmtree(folder)

    def get_jsonl_file(self):
        return self.output / f"googleSourceCode.{self.chunk_counter}.jsonl"

    #def get_zipfile(self, file_path):
    #    repo_root = Path(file_path)
    #    file_list = repo_root.rglob("**/*.*")
    #    repo = None
    #    for file in file_list:
    #        if not file.is_file(): continue
    #        if repo is None:
    #            repo = RepoInstance(folder_name=repo_root.parts[-1], plateform=self.plateform)
    #        repo.files_append(
    #            CodeFileInstance(repo_root, file, self.target_encoding)
    #        )
    #    if self.clean_src_file: # 删除源文件
    #        if file_path.is_file(): file_path.unlink(missing_ok=True)
    #        else: shutil.rmtree(file_path)
    #    return repo.get_dict_list()

    #def dump_to_jsonl(self, repo_file_info_list):
    #    for line in repo_file_info_list:
    #        with open(self.get_jsonl_file(), "a", encoding='utf-8')as a:
    #            a.write(json.dumps(line, ensure_ascii=False) + "\n")
    #        if os.path.getsize(self.get_jsonl_file()) > self.max_jsonl_size:
    #            self.chunk_counter += 1

    def __call__(self, root_dir):
        folder_list = glob.glob(root_dir+"/*")
        print(root_dir, len(folder_list))
        for folder in folder_list:
            if os.path.isdir(folder):
                logger.info(f'仓库 {folder} 开始处理')
                start_time = time.perf_counter()
                #repo_file_info_list = self.get_zipfile(folder)
                #print("repo: ",folder,"repo_file_info_list:", len(list(repo_file_info_list)))
                #self.dump_to_jsonl(repo_file_info_list)
                self.parse_and_save(folder)
                exec_time = time.perf_counter() - start_time
                logger.info(f'仓库 {folder} 处理完成，耗时 {exec_time:.2f} 秒')


def process_zips(zip_root, output, clean_src_file):
    handler = Zipfile2JsonL(output_root=output, target_encoding="utf-8", clean_src_file=clean_src_file)
    handler(root_dir=zip_root)


if __name__ == '__main__':
    # parser = argparse.ArgumentParser()
    # parser.add_argument("-i", "--input", required=True, help="输入压缩包的父路径")
    # parser.add_argument("-o", "--output", required=True, help="输出文件信息JSONL文件夹路径")
    # parser.add_argument("-c", "--clean_src_file", required=False, action="store_true", help="是否删除源文件，默认为否")
    # args = parser.parse_args()
    # process_zips(args.input, args.output, args.clean_src_file, plateform)
    process_zips(repos_folder, output_folder, clean_src_file)
