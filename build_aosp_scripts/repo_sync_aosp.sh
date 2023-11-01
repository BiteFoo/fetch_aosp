#!/bin/bash
#不需要设置变量直接进入程序目录即可
mkdir android-13.0.0_r43
cd android-13.0.0_r43
export REPO_URL='https://mirrors.tuna.tsinghua.edu.cn/git/git-repo/'
PATH=~/bin:$PATH
# 
git config --global user.email "xiaoA666@gmail.com"
git config --global user.name "xiaoA666"
repo init -u https://mirrors.tuna.tsinghua.edu.cn/git/AOSP/platform/manifest  -b android-13.0.0_r43 --depth=1
#
echo "Syncing android-13.0.0_r43"
repo sync -qj20
