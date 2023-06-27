#!/usr/bin/env python
# -*- coding:utf-8 -*-
import argparse
import json
import logging
import time
import zipfile
import charset_mnbvc
import hashlib as hs

from typing import List
from pathlib import PurePosixPath, Path


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
        self._encoding = charset_mnbvc.api.from_data(file_bytes, mode=2)
        self.target_encoding = target_encoding
        text = None
        if self._encoding is not None:
            text = charset_mnbvc.api.convert_encoding(file_bytes, self._encoding, self.target_encoding)
        self._text = text
        self._size = file_path.stat()
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
            "name": self.name,
            "ext": self.ext,
            "path": self.path,
            "size": self.size,
            "source_encoding": self.encoding,
            "md5": self.md5,
            "text": self.text
        }


class RepoInstance:
    def __init__(self, name: str):
        super(RepoInstance, self).__init__()
        self._name = name
        self._files: List[CodeFileInstance] = list()

    @property
    def name(self):
        return self._name

    @property
    def files(self):
        return self._files

    def files_append(self, file_obj: CodeFileInstance):
        if file_obj.encoding is not None:
            self._files.append(file_obj)

    def get_dict(self):
        return {
            "repo": self.name,
            "files": [f.get_dict() for f in self.files]
        }


class Zipfile2JsonL:
    def __init__(self, output_root, target_encoding="utf-8", clean_src_file=False):
        self.output = Path(output_root)
        self.target_encoding = target_encoding
        self.max_jsonl_size = 500 * 1024 * 1024
        self.repo_list = list()
        self.chunk_counter = 0
        self.jsonl_file_handler = open(self.get_jsonl_file, "w")
        self.clean_src_file = clean_src_file

    def get_zipfile(self, file_path):
        with zipfile.ZipFile(file_path, "r") as zf:
            zf.extractall(file_path.parent)
        repo_root = file_path.parent / file_path.stem
        file_list = repo_root.rglob("**/*.*")
        repo = RepoInstance(name=repo_root.name)
        for file in file_list:
            repo.files_append(
                CodeFileInstance(repo_root, file, self.target_encoding)
            )
        repo_root.unlink(missing_ok=True)
        if self.clean_src_file:
            file_path.unlink(missing_ok=True)
        return repo.get_dict()

    def get_jsonl_file(self):
        return self.output / f"githubcode.{self.chunk_counter}.jsonl"

    def dump_to_jsonl(self, repo_info):
        print(json.dumps(repo_info, ensure_ascii=False), file=self.jsonl_file_handler)
        self.jsonl_file_handler.write('\n')
        if self.jsonl_file_handler.tell() > self.max_jsonl_size:
            self.jsonl_file_handler.close()
            self.jsonl_file_handler = open(self.get_jsonl_file(), "w")

    def __call__(self, root_dir):
        root_dir = Path(root_dir)
        assert root_dir.exists(), FileNotFoundError(str(root_dir))
        file_list = root_dir.rglob("**/*.zip")
        for file in file_list:
            start_time = time.perf_counter()
            repo_info = self.get_zipfile(file)
            self.dump_to_jsonl(repo_info)
            exec_time = time.perf_counter() - start_time
            logger.info(f'zip文件 {file} 处理完成，耗时 {exec_time:.2f} 秒')

def process_zips(zip_root, output, clean_src_file):
    handler = Zipfile2JsonL(output_root=output, target_encoding="utf-8", clean_src_file=clean_src_file)
    handler(root_dir=zip_root)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True, help="输入压缩包的父路径")
    parser.add_argument("-o", "--output", required=True, help="输出 文件信息JSONL文件夹路径")
    parser.add_argument("-c", "--clean_src_file", required=False, action="store_true", help="是否删除源文件，默认为否")
    args = parser.parse_args()
    process_zips(args.input, args.output, args.clean_src_file)
