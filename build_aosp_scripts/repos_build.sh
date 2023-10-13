#!/bin/bash
source build/envsetup.sh
lunch aosp_blueline-userdebug
# 使用
make -j16
