#!/bin/bash
source build/envsetup.sh
lunch aosp_oriole-userdebug
# 使用
make -j16
