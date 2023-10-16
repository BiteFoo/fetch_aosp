# coding:utf8
'''
@File    :   fetch_aosp.py
@Author  :   Loopher 
@Version :   1.0
@date    :    2023/10/11 15:06:20
@License :   (C)Copyright 2020-2023,Loopher
@Desc    :   下载源码程序
'''
import json
import requests
from file import *
from bs4 import BeautifulSoup
from config import *


def fetch_remote(url, proxy=None):
    #
    if proxy:
        return requests.get(url, proxies=proxy)
    else:
        return requests.get(url)


def fetch_build_config():
    if check_file_exists("build_configs", BUILD_CONFIG):
        print("build_config.json exists")
        return
    url = "https://source.android.com/docs/setup/build/running?hl=zh-cn#selecting-device-build"
    res = fetch_remote(url, proxy)
    if res.status_code != 200:
        raise Exception("fetch_build_config error ")
    # print(res.text)
    # with open("build_config.html", "w", encoding="utf-8") as f:
    #     f.write(res.text)
    app = BeautifulSoup(res.text, "html.parser")
    # devsite-table-wrapper

    table = app.find_all("tr")
    device_tables_lines = []
    found = False
    item = []
    for tb in table:

        if tb.text.strip() == "":
            continue
        # print(tb.text, "build 配置 in ? ", "build 配置" in tb.text)
        if "build 配置" in tb.text:
            found = True
            continue
        if not found:
            continue
        if len(item) == 3:

            device_tables_lines.append([i for i in item])
            item.clear()
        else:
            item.append(tb.text.strip())
    device_config = {}
    for devices in device_tables_lines:
        for device in devices:
            deivce_name, code_name, build_config = device.split("\n")
            device_config[deivce_name] = {
                "code_name": code_name, "build_config": build_config}
    # print(json.dumps(device_config, indent=4))
    save_with_dir("build_configs", BUILD_CONFIG, json.dumps(device_config))


def fetch_build_branch():

    if check_file_exists("build_configs", BUILD_BRANCH):
        print("build branch 文件已存在")
        return
    # 下载设备分支版本
    url = "https://source.android.com/docs/setup/about/build-numbers?hl=zh-cn"
    res = fetch_remote(url, proxy)
    if res.status_code != 200:
        raise Exception("fetch build branch error")
    app = BeautifulSoup(res.text, "html.parser")
    build_list_lines = app.find_all("tr")
    build_branch_map = {}  # 构建分支map

    for line in build_list_lines:
        tds = line.find_all("td")
        if len(tds) == 0:
            continue
        if "HRI39" in line.text.strip():  # 我们不需要Honeycomb GPL模块后续的内容
            break
        if "android-5.0.0_r1.0.1" in line.text.strip():
            # 越往下的低版本都不需要了
            break
        branch_info = [td.text for td in tds if td.text.strip()]
        if len(branch_info) < 5:
            diff = 5 - len(branch_info)
            branch_info.extend(["" for _ in range(diff)])
        build_id, tag, version, supported_devices, patch_date = branch_info
        build_branch_map[build_id] = {
            "build_id": build_id,
            "tag": tag, "version": version, "supported_devices": supported_devices,
            "patch_date": patch_date}

    save_with_dir("build_configs", BUILD_BRANCH, json.dumps(build_branch_map))


def parse_driver_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    # 查找div class="devsite-article-body clearfix"
    div = soup.find('div', class_="devsite-article-body clearfix")
    # print(div)
    h3s = div.find_all('h3')
    tables = div.find_all('table')
    driver_map = {}
    for h3, table in zip(h3s, tables):

        description = h3.get_text()
        description_id = h3.get("id")

        # print("decription: ", description)
        # print("decription_id: ", description_id)
        driver_map[description_id] = {
            "description": description,
            "description_id": description_id,
            "downloads": []  # 下载信息
        }
        trs = table.find_all('tr')
        # 去掉第一个
        trs.pop(0)

        for tr in trs:
            # 读取
            a = tr.find("a")
            link = a.get("href")
            sha256_s = a.parent.find_next_sibling('td').get_text()
            # print("link ", link)
            # print("sha256_s ", sha256_s)
            driver_map[description_id]["downloads"].append({
                "link": link,
                "sha256_s": sha256_s
            })

    # print(json.dumps(driver_map, indent=4))
    # 保存结果
    save_with_dir("build_configs", BUILD_DRIVER, json.dumps(driver_map))


def fetch_driver():
    # 根据设备的名称和源码的id进行下载驱动文件
    # https://dl.google.com/dl/android/aosp/google_devices-panther-td1a.221105.001.a1-4ba7e08e.tgz?hl=zh-cn
    # https://dl.google.com/dl/android/aosp/google_devices-panther-tq1a.221205.011-229ee18c.tgz?hl=zh-cn
    # 下载驱动
    if check_file_exists("build_configs", BUILD_DRIVER):
        # 已经同步过文件
        # 否则我们删除这个配置即可重新同步
        return
    url = "https://developers.google.com/android/drivers?hl=zh-cn"
    res = fetch_remote(url, proxy)
    if res.status_code != 200:
        raise Exception("fetch driver failed")
    parse_driver_html(res.text)
    print("同步驱动完成")


def sync_aosp_build_info():
    make_sure_path_exists("build_configs")
    fetch_build_config()
    fetch_build_branch()
    fetch_driver()
    print("同步所有支持设备分支信息完成")
