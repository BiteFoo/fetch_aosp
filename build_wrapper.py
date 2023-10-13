# coding:utf8
'''
@File    :   build_wrapper.py
@Author  :   Loopher 
@Version :   1.0
@date    :    2023/10/13 09:21:23
@License :   (C)Copyright 2020-2021,Loopher
@Desc    :   编译脚本生成模块封装，提供查询和搜索功能
'''
import json
from file import *

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


def generate_scripts(builds):
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

    #
