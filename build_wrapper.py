# coding:utf8
'''
@File    :   build_wrapper.py
@Author  :   Loopher 
@Version :   1.0
@date    :    2023/10/13 09:21:23
@License :   (C)Copyright 2020-2021,Loopher
@Desc    :   编译脚本生成模块封装，提供查询和搜索功能
'''
import progressbar
import json
import requests
import hashlib
import sys
from urllib.parse import urlparse
from file import *
from config import *


# 初始化repo工具使用
init_repo_script = """#!/bin/bash
echo "创建repo工具"
mkdir ~/bin
PATH=~/bin:$PATH
curl https://mirrors.tuna.tsinghua.edu.cn/git/git-repo -o repo
chmod +x repo
"""

# 同步分支脚本 使用清华源生成
repo_sync_branch_script = """#!/bin/bash
#不需要设置变量直接进入程序目录即可
mkdir {branch}
cd {branch}
export REPO_URL='https://mirrors.tuna.tsinghua.edu.cn/git/git-repo/'
PATH=~/bin:$PATH
# 
git config --global user.email "xiaoA666@gmail.com"
git config --global user.name "xiaoA666"
repo init -u https://mirrors.tuna.tsinghua.edu.cn/git/AOSP/platform/manifest  -b {branch} --depth=1
#
echo "Syncing {branch}"
repo sync -qj20
"""
# 编译配置 包括了 source build
build_script = """#!/bin/bash
source build/envsetup.sh
lunch {build_id}
# 使用
make -j16
"""


def get_sha256(file_path):
    """
    获取文件的sha256
    """
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def get_build_models():
    """
    返回所有的设备型号，例如Pixel Pixel3
    """
    # print
    contents = read_file("build_configs", BUILD_CONFIG)
    configs = json.loads(contents)
    return configs


def get_all_branchs():
    """
    返回所有的分支，例如11.0.0
    """
    # print
    contents = read_file("build_configs", BUILD_BRANCH)
    configs = json.loads(contents)
    # 由于爬虫提取了页面的所有内容，因此需要过滤出不能存在补丁日期的条目，这里就是我们要的结果
    # 每一个item都是一个dict 格式为  {"build_id": "Pie", "tag": "9", "version": "API \u7ea7\u522b 28", "supported_devices": "", "patch_date": ""}
    return [item for _, item in configs.items() if item['patch_date'] != ""]


def get_codename(model):
    config = json.loads(read_file("build_configs", BUILD_CONFIG))
    return config[model]['code_name']


def suggestion_build(model, android_version):
    """
    model: 设备的型号信息 例如Pixel3 
    android_version: android源码的版本，例如android10 即可不用输入全称
    推荐的设备编译配置和分支代码
    例如我们输入了 Pixel3 则根据pixel3的支持列表进行过滤出来结果，在进行一次优化选择出结果
    """
    android_version = android_version.lower()  # 注意转换一下大小写
    # 先根据设备选择 选出现有的列表信息
    build_configs = get_build_models()

    model_list = [item for item in build_configs.keys() if model in item]

    # 提取分支
    branchs = get_all_branchs()
    # 我们处理一下输入的android_version
    if "-" not in android_version:
        android_version = android_version[:-2]+"-"+android_version[-2:]
    print("源码版本 ", android_version)
    # 在根据输入的源码版本选择
    suggestion_versions = []
    for branch in branchs:
        interaction = set(model_list).intersection(
            set(branch['supported_devices'].split('、')))
        if android_version in branch['tag'] and len(interaction):
            tmp = [build_configs[k]
                   for k in interaction if k == model]  # 取出对应的设备
            # for i in interaction:
            # 我们在这里增加build_config便于我们选择生成lunch aosp的选项
            branch['build_config'] = tmp
            suggestion_versions.append(branch)
    # 到这里基本列举完成
    return suggestion_versions


def download_file(save, url):
    # 发送HTTP GET请求获取文件
    if os.path.isfile(save):
        os.remove(save)
    # name = os.path.basename(save)
    with requests.get(url, proxies=proxy, stream=True) as response:
        if response.status_code == 200:
            total = response.headers.get('content-length')
            widgets = ['Downloading: ', progressbar.Percentage(), ' ',
            progressbar.Bar(marker='#', left='[', right=']'),
            ' ', progressbar.ETA(), ' ', progressbar.FileTransferSpeed()]
            pbar = progressbar.ProgressBar(widgets=widgets, maxval=int(total)).start()
                # 打开文件用于写入二进制数据
            with open(save, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
                        file.flush()
                        pbar.update(len(chunk) +1)
            pbar.finish()
        else:
            print(f"下载失败，HTTP状态码: {response.status_code}")
    # 校验一下md5的值


def get_path(fname):
    return os.getcwd()+os.sep+"build_aosp_scripts"+os.sep+fname


def show_drivre(code_name, build_id, download=False):
    lines = read_file("build_configs", BUILD_DRIVER)
    # print("驱动信息如下:", lines)
    drive_tag = code_name+build_id.lower()
    drivers = json.loads(lines)
    for key, driver in drivers.items():
        if key == drive_tag:
            for link in driver['downloads']:
                print("驱动下载地址 :", link['link'],
                      "\tsha256:", link['sha256_s'])
                if download:
                    parse = urlparse(link['link'])
                    fname = os.path.basename(parse.path)
                    save = get_path(fname)
                    download_file(save, link['link'])
                    # print("校验文件:", save)
                    n = get_sha256(save)
                    if n != link['sha256_s']:
                        print("校验失败，文件可能下载不全的原因是网络可能链接出现问题，可以使用 getfile 命令进行下载")


def getfile(url, sig: str = ""):
    # 下载文件使用
    parse = urlparse(url)
    fname = os.path.basename(parse.path)
    save = get_path(fname)
    download_file(save, url)
    n = get_sha256(save)
    print(f"下载文件完成：{save} sha256: {sig} new_sha256: {n}")
    if sig != "" and n != sig:
        print("校验失败，文件可能下载不全的原因是网络可能链接出现问题，可以使用 getfile 命令进行下载")
    else:
        print("下载成功")


def generate_scripts(builds, code_name):
    print("生成的编译分支列表为: ")
    for i, build in enumerate(builds):
        msg = "\tbuildId: "+build['build_id'] + "\ttag: "+build['tag'] + "\t\tversion: " + \
            build['version'] + \
            "\t支持设备列表数: %d" % (len(build['supported_devices'].split("、")))
        print("[%d]: %s" % (i, msg))
    select_result = input("请选择要构建的版本信息，也可以回车默认使用推荐模式，推荐会根据支持的设备列表大小来计算推荐结果: ")
    if select_result == "":
        recommand = builds[0]
        recommand_devices = recommand['supported_devices'].split("、")
        for build in builds[1:]:
            supported_devices = build['supported_devices'].split("、")
            if len(supported_devices) > len(recommand_devices):
                recommand = build
    else:
        recommand = builds[int(select_result)]
    print("编译分支选择结果为：")
    print()
    msg = "buildId:\t\t"+recommand['build_id'] + "\nbranch:\t\t\t"+recommand['tag'] + "\nversion:\t\t" + \
        recommand['version'] + \
        "\nsupported_devices:\t%s" % (
        " ".join(recommand['supported_devices'].split("、"))) + "\nbuild_config:\t\t"+build['build_config'][0]['build_config']
    print(msg)
    print()
    print("开始构建脚本，文件保存在build_asop_scripts目录下")
    print("正在生成编译脚本...")

    make_sure_path_exists("build_aosp_scripts")

    init_repo_script_s = init_repo_script.format(branch=recommand['tag'])

    save_with_dir("build_aosp_scripts", REPO_INIT_SHELL, init_repo_script_s)
    # print("初始化源码repo脚本内容如下:\n"+init_repo_script_s)

    repo_sync_branch_script_s = repo_sync_branch_script.format(
        branch=recommand['tag'])
    save_with_dir("build_aosp_scripts", REPO_SYNC_AOSP_SHELL,
                  repo_sync_branch_script_s)
    # print("同步源码脚本内容如下:\n"+repo_sync_branch_script_s)

    build_script_s = build_script.format(
        build_id=build['build_config'][0]['build_config'])
    save_with_dir("build_aosp_scripts", REPOS_BUILD_SHELL, build_script_s)
    # print("编译脚本内容如下:\n"+build_script_s)
    print("生成脚本完成,文件保存在 build_aosp_scripts目录下")
    # 输出对应的驱动信息
    #
    show_drivre(code_name, recommand['build_id'], True)

    #
def get_images(android_version,model,build_id):
    """_summary_

    Args:
        android_version (str): android版本，例如10
        build_id (str): 编译id 可能为空
        model (str): 设备型号
    """
    image_infos = json.loads(read_file("build_configs",PIXEL_IMAGES))
    # 列举出符合的设备列表，在根据os进行输出
    matched = [item for item in image_infos if model in  item['description'] and android_version in item['android_version']]
    if build_id != "":
        matched = [item for item in matched if build_id  ==  item['build_id']]
    if len(matched) == 0:
        print(f"未找到对应的设备信息 {model}")
        return 
    for i,m in enumerate(matched):
        print("[%d]: %s\t\tbuild_id: %s"%(i,m['description'],m['build_id']))
    select = input("请输入要选择下载的镜像文件:")
    select = matched[int(select)]
    print("开始下载进行文件: ",select['description'])
    print("版本信息: ",select['version']),
    print("下载链接: ",select['link'])
    print("sha256: ",select['sha256'])
    print("")
    make_sure_path_exists("downloads")
    parse = urlparse(select['link'])
    fname = os.path.basename(parse.path)
    save = os.getcwd()+os.sep+"downloads"+os.sep+fname
    download_file(save,select['link'])
    n = get_sha256(save)
    if n != select['sha256']:
        print("下载文件失败，请使用getfile命令重试")
    else:
        print("文件下载完成，保存在 "+save)
        
        
    
    