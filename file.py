# coding:utf8
'''
@File    :   file.py
@Author  :   Loopher 
@Version :   1.0
@date    :    2023/10/12 17:31:48
@License :   (C)Copyright 2020-2021,Loopher
@Desc    :   保存文件
'''
import codecs
import os

# 下载到本地的文件
BUILD_CONFIG = "build_config.json"
BUILD_BRANCH = "build_branch.json"
BUILD_DRIVER = "build_driver.json"
PIXEL_IMAGES="pixel_images.json"
# 每次重新使用suggest生成的配置信息
BUILD_CACHE_CONFIG = "build.pro"
# 编译shell脚本名称
REPO_INIT_SHELL = "repo_init.sh"
REPO_SYNC_AOSP_SHELL = "repo_sync_aosp.sh"
REPOS_BUILD_SHELL = "repos_build.sh"


def make_sure_path_exists(name):
    try:
        path = os.path.join(os.path.dirname(__file__), name)
        os.makedirs(path)
    except OSError:
        if not os.path.isdir(path):
            raise


def save_with_dir(directory, filename, content):
    file_path = os.path.join(os.path.dirname(__file__), directory, filename)
    with codecs.open(file_path, 'w', 'utf-8') as f:
        f.write(content)
    print("已经保存文件: "+file_path)


def save_file(file_name, content):
    file_path = os.path.join(os.path.dirname(__file__), file_name)
    with codecs.open(file_path, 'w', 'utf-8') as f:
        f.write(content)
    print("已经保存文件: "+file_path)


def read_file(directory, file_name):
    if directory is None:
        file_path = os.path.join(os.path.dirname(__file__), file_name)
    else:
        file_path = os.path.join(os.path.dirname(
            __file__), directory, file_name)
    with codecs.open(file_path, 'r', 'utf-8') as f:
        return f.read()


# def read_build_config

def check_file_exists(directory, file_name):
    if directory is None:
        file_path = os.path.join(os.path.dirname(__file__), file_name)
    else:
        file_path = os.path.join(os.path.dirname(
            __file__), directory, file_name)
    return os.path.exists(file_path)
