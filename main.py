import sys
import json
from login import login
import time
import threading
import copy
import os
import base64
import ddddocr



# 这是一个示例 Python 脚本。

# 按 Shift+F10 执行或将其替换为您的代码。
# 按 双击 Shift 在所有地方搜索类、文件、工具窗口、操作和设置。

def across_vcode(ss):
    timestamp = int(round(time.time() * 1000))
    vcode_url = "http://ehall.seu.edu.cn/gsapp/sys/jzxxtjapp/hdyy/vcode.do?_="+str(timestamp)
    res = ss.get(vcode_url)
    r = json.loads(res.text)
    code = r['result'].replace('data:image/jpeg;base64,','')
    img_bytes = base64.b64decode(code)
    #with open('verification_code.jpeg','wb') as f:
    #    f.write(img_bytes)
    #ocr = ddddocr.DdddOcr()
    #with open('verification_code.jpeg', 'rb') as f:
    #    img_bytes = f.read()
    ocr = ddddocr.DdddOcr()
    vcode = ocr.classification(img_bytes)
    if len(vcode) != 4:
        print("验证码识别错误，重试一次")
        return across_vcode(ss)
    #print(f"verification_code: {vcode}")
    return vcode

def fetch_lecture(hd_wid: str, ss,number: int):
    vcode = across_vcode(ss)
    print(f"probably the verification_code is: {vcode}")
    url = "http://ehall.seu.edu.cn/gsapp/sys/jzxxtjapp/hdyy/yySave.do"
    data_json = {'HD_WID': hd_wid,'vcode':vcode}
    form = {"paramJson": json.dumps(data_json)}
    #print(f"form: {form}")
    r = ss.post(url, data=form)
    result = r.json()
    if result['success'] is not False:
        print(result)
        print(f"预约成功！Happy lecture!")
        sys.exit(0)
    else:
        print(f"失败：{result['msg']}")

        flag = get_current_member(number, ss)
        if flag is False:
            print("该讲座暂时满员了，等待名额空缺中...")
            while flag is False:
                time.sleep(0.8)
                flag = get_current_member(number, ss)
                
    return result['code'], result['msg'], result['success']


def multi_threads(ss, threads_id, hd_wid: str, number: int):
    i = 1
    while True:
        code, msg, success = fetch_lecture(hd_wid, ss,number)
        print('线程{},第{}次请求,code：{},msg：{},success:{}'.format(threads_id, i, code, msg, success))
        if msg == '请求过于频繁，请稍后重试':
            time.sleep(60)
        if success is True or msg == '已经预约过该活动，无需重新预约！':
            sys.exit(0)
        i += 1
        time.sleep(1.8)


def get_lecture_list(ss):
    url = "http://ehall.seu.edu.cn/gsapp/sys/jzxxtjapp/*default/index.do#/hdyy"
    ss.get(url)
    url = "http://ehall.seu.edu.cn/gsapp/sys/jzxxtjapp/modules/hdyy/hdxxxs.do"
    form = {"pageSize": 15, "pageNumber": 1}
    r = ss.post(url, data=form)
    response = r.json()
    #print(response)
    rows = response['datas']['hdxxxs']['rows']
    return rows


def get_lecture_info(w_id, ss):
    url = "http://ehall.seu.edu.cn/gsapp/sys/jzxxtjapp/modules/hdyy/hdxxxq_cx.do"
    data_json = {'WID': w_id}
    r = ss.post(url, data=data_json)
    try:
        result = r.json()['datas']['hdxxxq_cx']['rows'][0]
        return result
    except Exception:
        print("课程信息获取失败")
        return False

def get_current_member(number,ss):
    url = "http://ehall.seu.edu.cn/gsapp/sys/jzxxtjapp/modules/hdyy/hdxxxs.do"
    form = {"pageSize": 15, "pageNumber": 1}
    r = ss.post(url, data=form)
    response = r.json()
    max_member = response['datas']['hdxxxs']['rows'][number]['HDZRS']
    current_member = response['datas']['hdxxxs']['rows'][number]['YYRS']
    if int(current_member) == int(max_member):
        #print("该讲座暂时满员了，等待名额空缺")
        #print(f"该讲座暂时满员了，等待名额空缺，当前名额：{current_member}，最大名额：{max_member}")
        return False
    print(f"该讲座，当前预约人数：{current_member}，最大人数：{max_member}")
    return True


# 按间距中的绿色按钮以运行脚本。
if __name__ == '__main__':
    with open("./config.json", "r", encoding="utf-8") as f:
        configs = f.read()
        configs = json.loads(configs)

    #print("请输入帐号:")
    #user_name = input()
    #print("请输入密码:")
    #password = input()
    print("开始登陆")
    s = login(configs['user']['cardnum'], configs['user']['password'])
    while s is False or s is None:
        print("请重新登陆")
        print("请输入帐号:")
        user_name = input()
        print("请输入密码:")
        password = input()
        print("开始登陆")
        s = login(user_name, password)
    print("登陆成功")
    #test function
    #across_vcode(s)
    print("----------------讲座列表----------------")
    lecture_list = get_lecture_list(s)
    map_of_lecture = {}
    i = 0
    for lecture in lecture_list:
        map_of_lecture[i] = lecture['WID']
        print("讲座编号:",end=" ")
        print(i)
        i += 1
        print("讲座wid：", end=" ")
        print(lecture['WID'])
        print("讲座名称：", end=" ")
        print(lecture['JZMC'])
        print("预约开始时间：", end=" ")
        print(lecture['YYKSSJ'])
        print("预约结束时间：", end=" ")
        print(lecture['YYJSSJ'])
        print("活动时间："+lecture['JZSJ'])
        print("活动地点："+lecture['JZDD'])
        #print(lecture)
        print("-----------------------------------------------------------------")
    print("----------------讲座列表end----------------")
    lecture_info = False
    while True:
        print("请输入讲座编号")
        number = input()
        #lecture_info = get_lecture_info(wid, s)
        get_current_member(int(number),s)
        wid = map_of_lecture[int(number)]
        lecture_info = get_lecture_info(wid, s)
        if lecture_info is not False:
            print("确认讲座名称：{}. y/n".format(lecture_info['JZMC']))
            confirm = input()
            if confirm == 'y' or confirm == 'Y':
                break
            else:
                pass
    print("请输入提前几秒开始抢（现版本建议填写'0',请保证本地时间准确）：")
    advance_time = int(input())
    current_time = int(time.time())
    begin_time = int(time.mktime(time.strptime(lecture_info['YYKSSJ'], "%Y-%m-%d %H:%M:%S")))
    end_time = int(time.mktime(time.strptime(lecture_info['YYJSSJ'], "%Y-%m-%d %H:%M:%S")))
    if current_time > end_time:
        print("抢讲座时间已结束，大侠请重新来过")
        sys.exit(0)
    while current_time < begin_time - advance_time:
        current_time = int(time.time())
        print('等待{}秒'.format(begin_time - advance_time - current_time))
        time.sleep(1)
    print('开始抢讲座')
    t1 = threading.Thread(target=multi_threads, args=(copy.deepcopy(s), 't1', wid,int(number)))
    #t2 = threading.Thread(target=multi_threads, args=(copy.deepcopy(s), 't2', wid))
    #t3 = threading.Thread(target=multi_threads, args=(copy.deepcopy(s), 't3', wid))
    t1.start()
    time.sleep(0.1)
    #t2.start()
    #time.sleep(0.1)
    #t3.start()

    #input("please input any key to exit!")
    os.system("pause")


# print(s)

# 119fbac8e9a146e2b0d73b59def1bc85
# 访问 https://www.jetbrains.com/help/pycharm/ 获取 PyCharm 帮助
