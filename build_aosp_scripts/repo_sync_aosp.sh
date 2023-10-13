#!/bin/bash
#不需要设置变量直接进入程序目录即可
mkdir android-10.0.0_r41
cd android-10.0.0_r41
export REPO_URL='https://mirrors.tuna.tsinghua.edu.cn/git/git-repo/'
PATH=~/bin:$PATH
# 
git config --global user.email "xiaoA666@gmail.com"
git config --global user.name "xiaoA666"
repo init -u https://mirrors.tuna.tsinghua.edu.cn/git/AOSP/platform/manifest  -b android-10.0.0_r41 --depth=1
#
echo "Syncing android-10.0.0_r41"
repo sync -qj20
