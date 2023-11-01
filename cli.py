# coding:utf8
'''
@File    :   cli.py
@Author  :   Loopher 
@Version :   1.0
@date    :    2023/10/12 17:28:39
@License :   (C)Copyright 2020-2021,Loopher
@Desc    :   cli应用 交互式下载源码，同时支持手动同步官方配置文档数据，
            程序支持推荐下载对应的设备分支执行和驱动文件，避免繁琐的去查阅官方文档，当然还是推荐去阅读官方文档        
'''

import cmd2
import click
import os
import sys
from build_wrapper import *
import readline
import subprocess
from libs import *
from fetch_aosp import sync_aosp_build_info


class Parser(cmd2.Cmd):
    """
    自定义命令行交互式应用
    """
    select_model = None  # 选择的源码构建的设备型号，例如Pixel3
    android_version = None  # 输入的源码版本，例如我们输入android10

    def __init__(self):
        super().__init__(allow_cli_args=False)
        self.prompt = '> '
        # self.intro = '欢迎使用cli应用，输入help查看帮助'
        self.doc_header = '命令列表'
        self.misc_header = '杂项命令'
        self.undoc_header = '未实现命令'

    def preloop(self):
        """
        在命令行交互式应用启动前执行的函数
        """
        print('欢迎使用同步Android官方编译源码配置同步应用，输入help查看帮助')

    # def do_scan_device(self, arg):
    #     """
    #     scan usb device
    #     """
    #     with subprocess.Popen("adb devices", shell=True, stdout=subprocess.PIPE) as proc:
    #         proc.wait()
    #         output = proc.stdout.read().decode('utf-8')
    #         # print(output)
    #         for line in output.splitlines():
    #             if line.find('device') >= 0:

    #                 device_name = line.split()[0]
    #                 if device_name == "List":
    #                     continue
    #                 print('设备名称：' + device_name)
    #                 self.device_list.append(device_name)

    def do_reload_build(self, line):
        """
        重新加载build.prop文件
        """
        #
        self.builds = json.loads(read_file(None, BUILD_CACHE_CONFIG))
        #
        generate_scripts(self.builds)

    def do_list_models(self, line):
        """
        列举出所有的设备信息
        """
        models = get_build_models()
        models = [k for k in models.keys()]
        print("官方支持的源码编译设备名称型号如下:")
        for i, model in enumerate(models):
            print("[%d]\t%s" % (i, model))

    def do_suggest(self, line):
        """
        select device model
        自动补全设备的型号 例如输入
        suggest p  回车可以实现选择
        """
        models = get_build_models()
        models = [k for k in models.keys()]
        print("官方支持的源码编译设备名称型号如下:")
        for i, model in enumerate(models):
            print("[%d]\t%s" % (i, model))

        self.select_model = models[int(
            Numeric("\n请输入要选择的设备型号:", lbound=0, ubound=len(models)).ask())]
        print("您选择的设备型号为: %s" % self.select_model)
        self.android_version = input(
            "请输入要编译的Android的源码版本，例如android10,默认是android10:")
        # self.android_version = input("输入要编译的源码版本:")
        if self.android_version == "":
            self.android_version = "android10"
        print("您选择的Android源码版本为: %s" % self.android_version)
        self.builds = suggestion_build(self.select_model, self.android_version)
        # 保存一下生成的配置信息
        save_file(BUILD_CACHE_CONFIG, json.dumps(self.builds))
        code_name = get_codename(self.select_model)
        print(f"设备的codename = {code_name}")
        # 记录好了这个机型信息，此时生成脚本
        generate_scripts(self.builds, code_name)

    # def do_select_device(self, arg):
    #     """
    #     select device
    #     """
    #     if len(self.device_list) == 0:
    #         print('请先扫描设备')
    #     else:
    #         # if len(self.device_list) == 1:
    #         for i in range(len(self.device_list)):
    #             print(str(i) + ': ' + self.device_list[i])
    #         self.select_devce_index = self.device_list[int(
    #             Numeric("\nEnter the index of the device to use:", lbound=0, ubound=len).ask())]
    #         print('选择设备：' + self.device_list[self.select_devce_index])

    def get_device_model(self, line):
        """
        获取设备型号，用于生成
        """

        pass

    def do_download_driver(self, line):
        """
        下载驱动
        这里我们需要获取 设备的Model 和aosp的分支
        例如 
        model = Pixel 3 这里要注意的是google提供的设备型号名称中Pixel3 实际是有空格的，因此我们要注意这个空格 
        aosp_branch = android-10.0.0_r41
        方便我们快速得到驱动信息
        """
        print("输入要下载的设备型号和源码分支，使用空格分开，例如Pixel 3,android-10.0.0_r41 进行下载驱动文件")
        raw = input("请输入: ")
        model, aosp_branch = raw.split(",")

        build_id = ""
        branches = get_all_branchs()
        for branch in branches:
            if branch['tag'] == aosp_branch:
                build_id = branch['build_id']
                break
        if build_id == "":
            print("没有找到源码相关的分支build id，尝试使用lsbranch查看")
        else:
            code_name = get_codename(model)
        show_drivre(code_name, build_id, True)

    def do_lsbranch(self, line):
        """
        列出所有的分支
        """
        branches = get_all_branchs()
        for branch in branches:
            print("branch:\t"+branch['tag'] +
                  '\tbuild_id:\t' + branch['build_id'])
    
    def do_sync_aosp_config(self, arg):
        """
       同步googl
       官方编译源码配置，默认存储在本地
       使用缓存： sync_aosp_config 如果已经存在配置，则使用默认，否则会同步
       强制同步：sync_aosp_config force 会重新下载编译源码配置信息
        """
        force = False
        if arg != "":
            force = True if arg == "force" else False
        sync_aosp_build_info(force)
        print('同步配置成功')

    def do_getfile(self, line):
        """
        下载指定url文件，通常用来下载driver文件
        使用 getfile url sha256  
        getfile url [sha256]
        """
        tmp = line.split(" ")
        url = ""
        sig = ""
        if len(tmp) == 1:
            url = tmp[0]
        else:
            url, sig = tmp
        getfile(url, sig)
    def do_get_image(self,line):
        """
        下载镜像
        get_image android_version,model,[build_id])
        android_version: android的版本，例如10 直接输入10即可
        model:手机信号，例如pixel 3 注意这个要用空格隔开
        
        """
        ins  = line.split(",")
        if len(ins) == 2:
            android_version = ins[0]
            model = ins[1]
            build_id = ""
        elif len(ins) == 3:
            android_version = ins[0]
            model = ins[1]
            build_id = ins[2]
        else:
            print("参数错误")
        get_images(android_version,model,build_id)
    def do_build_aosp_help(self,line):
        """_summary_

        编译AOSP帮助命令提示
        """
        text = """
        1、执行build_aosp_scripts下的脚本，这些脚本分别有
        repo_init.sh 初始化repo环境
        repo_sync_aosp.sh  执行代码下载
        repo_build.sh 执行编译
        如果有需要可以调整脚本内的参数，这些功能我都已经测试过没问题
        2、编译完成后，执行刷机命令为
        export ANDROID_PRODUCT_OUT=/path/to/aosp/out/target/product/phone_model
        如果是pixel3 android10 则为
        export ANDROID_PRODUCT_OUT=/path/to/aosp/out/target/product/blueline/
        执行刷机
        adb reboot bootloader
        fastboot flashall -w 
        如果想保留手机的数据，可以不加-w选项
        """
        print(text)
 
    def do_install_magisk_help(self,line):
        text ="""FLASHING MAGISK 

        安装magisk帮助
        首先我们将编译出来的aosp中的boot.img文件push到手机内，执行
        adb push boot.img /storage/emulated/0/Downloads
        然后使用magisk进行patch
        最后提取出来patch的文件，一般会带有关magisk_xxx.img
        接着尝试刷入测试，
        1、先尝试刷入启动能否启动
        adb reboot bootloader
        fastboot boot magisk_xxx.img
        如果确认没问题，再执行刷入
        adb reboot bootloader
        fastboot flash boot magisk_xx.img
        """
        print(text)
        
        
    def postloop(self):
        """
        在命令行交互式应用退出前执行的函数
        """
        print('退出cli应用')

    def precmd(self, line):
        """
        在命令行交互式应用执行命令前执行的函数
        """
        return line


if __name__ == '__main__':
    if readline.__doc__ is not None and "libedit" in readline.__doc__:
        readline.parse_and_bind("bind ^I rl_complete")
    else:
        readline.parse_and_bind("tab: complete")
    Parser().cmdloop()
