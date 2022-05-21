import random
import qqbot
import yaml
import os
import requests
from PIL import Image
from io import BytesIO
import cv2
import numpy 
import datetime
from utils.util import sketch
from qqbot.model.message import MessageEmbedField, MessageEmbed, MessageReference
from qqbot.model.api_permission import APIPermissionDemandIdentify, PermissionDemandToCreate

os.environ["QQBOT_LOG_PATH"] = os.path.join(os.getcwd(), "log", "%(name)s.log")

with open("./config/config.yaml", "r") as f:
    config = yaml.load(f.read(), Loader=yaml.FullLoader)
appId = config["token"]["appId"]
token = config["token"]["token"]
base_url = config["server"]["url"]
port = config["server"]["port"]
token = qqbot.Token(appId, token)
# 古诗词缓存表
poetry_dict = [
    ["陶渊明", "《饮酒·结庐在人境》", "结庐在人境", "而无车马喧", "问君何能尔", "心远地自偏", "采菊东篱下", "悠然见南山", "山气日夕佳", "飞鸟相与还", "此中有真意", "欲辨已忘言"],
    ["李白", "《望庐山瀑布》", "日照香炉生紫烟", "遥看瀑布挂前川", "飞流直下三千尺", "疑是银河落九天"],
    ["李白", "《早发白帝城》", "朝辞白帝彩云间", "千里江陵一日还", "两岸猿声啼不住", "轻舟已过万重山"],
    ["李白", "《望天门山》", "天门中断楚江开", "碧水东流至此回", "两岸青山相对出", "孤帆一片日边来"],
    ["杜甫", "《春望》", "国破山河在", "城春草木深", "感时花溅泪", "恨别鸟惊心", "烽火连三月", "家书抵万金", "白头搔更短", "浑欲不胜簪"],
    ["杜甫", "《望岳》", "岱宗夫如何", "齐鲁青未了", "造化钟神秀", "阴阳割昏晓", "荡胸生曾云", "决眦入归鸟", "会当凌绝顶", "一览众山小"],
    ["白居易", "《暮江吟》", "一道残阳铺水中", "半江瑟瑟半江红", "可怜九月初三夜", "露似真珠月似弓"],
    ["陆游", "《冬夜读书示子聿》", "古人学问无遗力", "少壮工夫老始成", "纸上得来终觉浅", "绝知此事要躬行"]
]
# 轮训方式获得古诗词
cur_poetry_idx = 0
# 用户状态缓存表
user_dict = {}

async def _message_handler(event, message):
    # 获得相应对象的操作api
    msg_api = qqbot.AsyncMessageAPI(token, False)
    api_permission_api = qqbot.AsyncAPIPermissionAPI(token, False)
    # 如果用户是第一次访问
    user = message.author
    if user.id not in user_dict:
        # 用户状态初始化
        user_dict[user.id] = {
                              "visit_date": datetime.datetime.now().strftime("%Y-%m-%d"),  # 第一次访问时间
                              "poetry_status": False,  # 默写诗歌状态
                              "target_poetry_line": "",  # 状态为true的话，正确的诗歌字符串
                              "poetry_score": 0,  # 用户默写诗歌的得分，默写正确得一分
                              "number_status": False,  # 猜数字的状态，为0表示还没开始猜数字
                              "target_number": -1, # 猜数字的目标分数
                              "number_score": 0
                            }
    content = message.content
    # 打印返回信息
    qqbot.logger.info("event %s" % event + ",receive message: %s" % content)
    # 构造消息发送请求数据对象
    send = qqbot.MessageSendRequest("<@%s>,你好，我是您的专属机器人，请问有什么可以为您服务的？" % message.author.id, message.id)
    
    if "/个人信息" in content:
        # user = user_api.me()
         # 构造消息发送请求数据对象
        embed = MessageEmbed()
        embed.title = "您的个人信息如下："
        embed.prompt = "腾生机器人"
        embed.fields = [
            MessageEmbedField(name=u'\U0001F3C2' + "用户名：" + user.username),
            MessageEmbedField(name=u'\U0001F317' + "当前的默写古诗词积分：" + str(user_dict[user.id]["poetry_score"])),
            MessageEmbedField(name=u'\U0001F384' + "当前的猜数字积分：" + str(user_dict[user.id]["number_score"])),
            MessageEmbedField(name=u'\U0001F60A' + "第一次访问腾生的时间：" + user_dict[user.id]["visit_date"]),
        ]
        # send = qqbot.MessageSendRequest(embed=embed, msg_id=message.id, content="<@!1234>hello world")
        send = qqbot.MessageSendRequest(embed=embed, msg_id=message.id)
    elif "/头像素描" in content:
        user_api = qqbot.UserAPI(token, False)
        user = message.author
        encoded_img = requests.get(user.avatar).content
        ori_img = Image.open(BytesIO(encoded_img))
        img = cv2.cvtColor(numpy.asarray(ori_img), cv2.COLOR_RGB2BGR)
        img = sketch(img)
        path = "../flask-robot/static/" + str(user.id) + ".jpg"
        cv2.imwrite(path, img)
        print(user.avatar)
        send = qqbot.MessageSendRequest("", message.id)
        print("http://" + base_url + ":" + str(port) + "/static/")
        send.image = "http://" + base_url + ":" + str(port) + "/static/" + str(user.id) + ".jpg"
    elif "/请求权限" in content:
        demand_identity = APIPermissionDemandIdentify("/guilds/{guild_id}/members/{user_id}", "GET")
        permission_demand_to_create = PermissionDemandToCreate(message.channel_id, demand_identity)
        demand = await api_permission_api.post_permission_demand(message.guild_id, permission_demand_to_create)
        send = qqbot.MessageSendRequest()
        qqbot.logger.info("api title: %s" % demand.title + ", desc: %s" % demand.desc)
    elif "/默写古诗词" in content:
        if not user_dict[user.id]["poetry_status"]:
            global cur_poetry_idx
            poetry_idx = cur_poetry_idx
            cur_poetry_idx = cur_poetry_idx + 1
            if cur_poetry_idx == len(poetry_dict):
                cur_poetry_idx == 0
            line_idx = random.randint(2, len(poetry_dict[poetry_idx]) - 1)
            suffix = ""
            if line_idx % 2 == 0:
                user_dict[user.id]["target_poetry_line"] = poetry_dict[poetry_idx][line_idx + 1]
                suffix = " 的下一句是？"
            else:
                user_dict[user.id]["target_poetry_line"] = poetry_dict[poetry_idx][line_idx - 1]
                suffix = " 的上一句是？"
            send = qqbot.MessageSendRequest("<@%s>" % message.author.id + " 请问" + poetry_dict[poetry_idx][0] + "创造的" + poetry_dict[poetry_idx][1] + "一诗中:"+ poetry_dict[poetry_idx][line_idx] + suffix
                                            + "\n---------------\n如果您不知道，可以输入\"/默写古诗词 提示\"来获得提示信息\n如果您想结束游戏，可以输入\"/默写古诗词 结束游戏\"来随时结束默写古诗词游戏", message.id)
            user_dict[user.id]["poetry_status"] = True
        elif "提示" in content:
            target_line = user_dict[user.id]["target_poetry_line"]
            target_line_list = list(target_line)
            target_line_list[0] = "__"
            target_line_list[len(target_line_list) - 1] = "__"
            target_line_list[random.randint(1, len(target_line_list) - 3)] = "__"
            prompt_str = "".join(target_line_list)
            send = qqbot.MessageSendRequest("<@%s>" % message.author.id + prompt_str, message.id)
        elif "结束游戏" in content:
            user_dict[user.id]["poetry_status"] = False
            send = qqbot.MessageSendRequest("<@%s>" % message.author.id + "，默写古诗词游戏已结束", message.id)
        else:
            user_line = content.split(" ")[-1]
            target_line = user_dict[user.id]["target_poetry_line"]
            if target_line == user_line:
                send = qqbot.MessageSendRequest("<@%s>" % message.author.id + "，真棒，回答正确，诗歌积分加1", message.id)
                qqbot.logger.info(user.id + "诗歌积分加1")
                user_dict[user.id]["poetry_score"] = user_dict[user.id]["poetry_score"] + 1
                user_dict[user.id]["poetry_status"] = False
            else:
                send = qqbot.MessageSendRequest("<@%s>" % message.author.id + "，对不起，回答错误，您可以输入\"/默写古诗词 提示\"来获得提示信息\n如果您想结束游戏，可以输入\"/默写古诗词 结束游戏\"来随时结束默写古诗词游戏", message.id)
    elif "/猜数字" in content:
        if not user_dict[user.id]["number_status"]:
            user_dict[user.id]["target_number"] = random.randint(0, 100)
            user_dict[user.id]["number_status"] = True
            qqbot.logger.info(user.id + "猜数字游戏中，生成的数字为：" + str(user_dict[user.id]["target_number"]))
            send = qqbot.MessageSendRequest("<@%s>" % message.author.id + "，随机数字已生成，请输入1-100之间的数字\n---------------\n如果您想结束游戏，可以输入\"/猜数字 结束\"来随时结束猜数字游戏", message.id)
        elif "结束" in content:
            user_dict[user.id]["number_status"] = False
            send = qqbot.MessageSendRequest("<@%s>" % message.author.id + "，猜数字游戏已结束", message.id)
        else:
            user_num = content.split(" ")[-1]
            target_num = user_dict[user.id]["target_number"]
            try:
                user_num = int(user_num)
                if user_num > target_num:
                    send = qqbot.MessageSendRequest("<@%s>" % message.author.id + "，您输入的数字比目标数字大！\n请重新输入1-100之间的数字\n---------------\n如果您想结束游戏，可以输入\"/猜数字 结束\"来随时结束猜数字游戏", message.id)
                elif user_num < target_num:
                    send = qqbot.MessageSendRequest("<@%s>" % message.author.id + "，您输入的数字比目标数字小！\n请重新输入1-100之间的数字\n---------------\n如果您想结束游戏，可以输入\"/猜数字 结束\"来随时结束猜数字游戏", message.id)
                else:
                    send = qqbot.MessageSendRequest("<@%s>" % message.author.id + "，太棒了！正确数字就是" + str(user_num) + "，您的猜数字积分加1", message.id)
                    user_dict[user.id]["number_status"] = False
                    user_dict[user.id]["number_score"] = user_dict[user.id]["number_score"] + 1
            except Exception as e:
                qqbot.logger.info(str(user.id) + "在猜数字游戏中输入的不是数字!")
                send = qqbot.MessageSendRequest("<@%s>" % message.author.id + "，不好意思，您输入的不是数字，请重新输入", message.id)
    elif "/计算器" in content:
        cal_str = content.split(" ", 2)[-1]
        qqbot.logger.info(str(user.id) + "在计算器中输入的表达式为：" + cal_str)
        try:
            num = eval(cal_str)
            send = qqbot.MessageSendRequest("<@%s>" % message.author.id + "，" + cal_str.replace(" ", "") + "的结果是：" + str(num), message.id)
        except Exception as e:
            if "（" in cal_str or "）" in cal_str:
                qqbot.logger.info(str(user.id) + "在计算器功能中输入的计算表达式不是英文括号!")
                send = qqbot.MessageSendRequest("<@%s>" % message.author.id + "，表达式需要英文括号", message.id)
            elif cal_str.count("(") != cal_str.count(")"):
                qqbot.logger.info(str(user.id) + "在计算器功能中输入的计算表达式左右括号数量不对!")
                send = qqbot.MessageSendRequest("<@%s>" % message.author.id + "，请检查表达式的左右括号数量", message.id)
            else:
                qqbot.logger.info(str(user.id) + "在计算器功能中输入的计算表达式有误!")
                send = qqbot.MessageSendRequest("<@%s>" % message.author.id + "，您输入的计算表达式有误，请重新输入!", message.id)
    if "谢谢" in content or "真棒" in content:
        message_reference = MessageReference()
        message_reference.message_id = message.id
        # 返回引用消息
        send = qqbot.MessageSendRequest(content="<emoji:74>没关系，这些都是腾生应该做的，如果满意的话，就发个offer吧", msg_id=message.id, message_reference=message_reference)
    # 通过api发送回复消息
    await msg_api.post_message(message.channel_id, send)


qqbot_handler = qqbot.Handler(qqbot.HandlerType.AT_MESSAGE_EVENT_HANDLER, _message_handler)
qqbot.async_listen_events(token, False, qqbot_handler)
