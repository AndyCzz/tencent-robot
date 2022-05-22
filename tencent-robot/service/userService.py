import qqbot
from qqbot.model.message import MessageEmbedField, MessageEmbed, MessageReference
from qqbot.model.api_permission import APIPermissionDemandIdentify, PermissionDemandToCreate
import qqbot
import cv2
import requests
import requests
from PIL import Image
from io import BytesIO
from utils.util import sketch
import numpy
import random
from utils.dbUtil import getRedisInstance, getDB, closeDB
import datetime
from dao.userDao import insertUser, updateUser, selectById
from pojo.User import User
'''
    用户第一次访问机器人进行的初始化
'''
def initUser(user):
    r = getRedisInstance()
    if not r.exists(str(user.id)):
        qqbot.logger.info("id:%s第一次访问" % str(user.id))
        visit_time = datetime.datetime.now().strftime("%Y-%m-%d")
        # 写入缓存
        r.hset(str(user.id), "visit_date", visit_time)
        r.hset(str(user.id), "poetry_status", 0)
        r.hset(str(user.id), "target_poetry_line", "")
        r.hset(str(user.id), "poetry_score", 0)
        r.hset(str(user.id), "number_status", 0)
        r.hset(str(user.id), "target_number", -1)
        r.hset(str(user.id), "number_score", 0)
        r.hset(str(user.id), "cur_poetry_idx", 0)
    if selectById(user.id) == None:
        # 写入数据库
        db_user = User(user.id, 0, 0, visit_time)
        insertUser(db_user)

'''
    展示用户信息
    para1: user表示用户
    para2: message表示消息
    return: 表示得到的响应对象
'''
def showPersonalInfo(user, message):
    r = getRedisInstance()
     # 构造消息发送请求数据对象
    embed = MessageEmbed()
    embed.title = "您的个人信息如下："
    embed.prompt = "腾生机器人"
    
    embed.fields = [
        MessageEmbedField(name=u'\U0001F3C2' + "用户名：" + user.username),
        MessageEmbedField(name=u'\U0001F317' + "当前的默写古诗词积分：" + str(r.hget(str(user.id), "poetry_score"))),
        MessageEmbedField(name=u'\U0001F384' + "当前的猜数字积分：" + str(r.hget(str(user.id), "number_score"))),
        MessageEmbedField(name=u'\U0001F60A' + "第一次访问腾生的时间：" + r.hget(str(user.id), "visit_date")),
    ]
    # send = qqbot.MessageSendRequest(embed=embed, msg_id=message.id, content="<@!1234>hello world")
    return qqbot.MessageSendRequest(embed=embed, msg_id=message.id)

'''
    用户头像素描渲染
'''
def getAvatarSketch(user, message, base_url, port):
    encoded_img = requests.get(user.avatar).content
    ori_img = Image.open(BytesIO(encoded_img))
    img = cv2.cvtColor(numpy.asarray(ori_img), cv2.COLOR_RGB2BGR)
    img = sketch(img)
    path = "../flask-robot/static/" + str(user.id) + ".jpg"
    cv2.imwrite(path, img)
    send = qqbot.MessageSendRequest("", message.id)
    send.image = "http://" + base_url + ":" + str(port) + "/static/" + str(user.id) + ".jpg"
    return send

async def getPermission(message, api_permission_api):
    demand_identity = APIPermissionDemandIdentify("/guilds/{guild_id}/members/{user_id}", "GET")
    permission_demand_to_create = PermissionDemandToCreate(message.channel_id, demand_identity)
    demand = await api_permission_api.post_permission_demand(message.guild_id, permission_demand_to_create)
    qqbot.logger.info("api title: %s" % demand.title + ", desc: %s" % demand.desc)
    send = qqbot.MessageSendRequest()
    return send
    
'''
    默写古诗词游戏
'''
def writePoetry(message, user, content, poetry_dict):
    r = getRedisInstance()
    # 为0表示新一轮的游戏
    if not int(r.hget(str(user.id), "poetry_status")):
        cur_poetry_idx = int(r.hget(str(user.id), "cur_poetry_idx"))
        if cur_poetry_idx == len(poetry_dict):
            cur_poetry_idx = 0
            r.hset(str(user.id), "cur_poetry_idx", 0)
        r.hincrby(str(user.id), "cur_poetry_idx", amount=1)

        line_idx = random.randint(2, len(poetry_dict[cur_poetry_idx]) - 1)
        suffix = ""
        if line_idx % 2 == 0:
            r.hset(str(user.id), "target_poetry_line", poetry_dict[cur_poetry_idx][line_idx + 1])
            suffix = " 的下一句是？"
        else:
            r.hset(str(user.id), "target_poetry_line", poetry_dict[cur_poetry_idx][line_idx - 1])
            suffix = " 的上一句是？"
        send = qqbot.MessageSendRequest("<@%s>" % message.author.id + " 请问" + poetry_dict[cur_poetry_idx][0] + "创造的" + poetry_dict[cur_poetry_idx][1] + "一诗中:"+ poetry_dict[cur_poetry_idx][line_idx] + suffix
                                        + "\n---------------\n如果您不知道，可以输入\"/默写古诗词 提示\"来获得提示信息\n如果您想结束游戏，可以输入\"/默写古诗词 结束游戏\"来随时结束默写古诗词游戏", message.id)
        r.hset(str(user.id), "poetry_status", 1)
    elif "提示" in content:
        target_line = r.hget(str(user.id), "target_poetry_line")
        target_line_list = list(target_line)
        target_line_list[0] = "__"
        target_line_list[len(target_line_list) - 1] = "__"
        target_line_list[random.randint(1, len(target_line_list) - 3)] = "__"
        prompt_str = "".join(target_line_list)
        send = qqbot.MessageSendRequest("<@%s>" % message.author.id + prompt_str, message.id)
    elif "结束游戏" in content:
        r.hset(str(user.id), "poetry_status", 0)
        send = qqbot.MessageSendRequest("<@%s>" % message.author.id + "，默写古诗词游戏已结束", message.id)
    else:
        user_line = content.split(" ")[-1]
        target_line = r.hget(str(user.id), "target_poetry_line")
        if target_line == user_line:
            send = qqbot.MessageSendRequest("<@%s>" % message.author.id + "，真棒，回答正确，诗歌积分加1", message.id)
            qqbot.logger.info(user.id + "诗歌积分加1")
            # 更新redis
            r.hincrby(str(user.id), "poetry_score", amount=1)
            r.hset(str(user.id), "poetry_status", 0)
            # 更新数据库
            updateUser(User(user.id, int(r.hget(str(user.id), "poetry_score")), int(r.hget(str(user.id), "number_score")), None))
        else:
            send = qqbot.MessageSendRequest("<@%s>" % message.author.id + "，对不起，回答错误，您可以输入\"/默写古诗词 提示\"来获得提示信息\n如果您想结束游戏，可以输入\"/默写古诗词 结束游戏\"来随时结束默写古诗词游戏", message.id)
    return send

'''
    猜数字游戏
'''
def guessNum(message, user, content):
    r = getRedisInstance()
    if not int(r.hget(str(user.id), "number_status")):
        r.hset(str(user.id), "target_number", random.randint(0, 100))
        r.hset(str(user.id), "number_status", 1)
        
        qqbot.logger.info(user.id + "猜数字游戏中，生成的数字为：" + str(r.hget(str(user.id), "target_number")))
        send = qqbot.MessageSendRequest("<@%s>" % message.author.id + "，随机数字已生成，请输入1-100之间的数字\n---------------\n如果您想结束游戏，可以输入\"/猜数字 结束\"来随时结束猜数字游戏", message.id)
    elif "结束" in content:
        r.hset(str(user.id), "number_status", 0)
        send = qqbot.MessageSendRequest("<@%s>" % message.author.id + "，猜数字游戏已结束", message.id)
    else:
        user_num = content.split(" ")[-1]
        target_num = int(r.hget(str(user.id), "target_number"))
        try:
            user_num = int(user_num)
            if user_num > target_num:
                send = qqbot.MessageSendRequest("<@%s>" % message.author.id + "，您输入的数字比目标数字大！\n请重新输入1-100之间的数字\n---------------\n如果您想结束游戏，可以输入\"/猜数字 结束\"来随时结束猜数字游戏", message.id)
            elif user_num < target_num:
                send = qqbot.MessageSendRequest("<@%s>" % message.author.id + "，您输入的数字比目标数字小！\n请重新输入1-100之间的数字\n---------------\n如果您想结束游戏，可以输入\"/猜数字 结束\"来随时结束猜数字游戏", message.id)
            else:
                send = qqbot.MessageSendRequest("<@%s>" % message.author.id + "，太棒了！正确数字就是" + str(user_num) + "，您的猜数字积分加1", message.id)
                # 更新redis
                r.hset(str(user.id), "number_status", 0)
                r.hincrby(str(user.id), "number_score", amount=1)
                # 更新数据库
                updateUser(User(user.id, int(r.hget(str(user.id), "poetry_score")), int(r.hget(str(user.id), "number_score")), None))
        except Exception as e:
            qqbot.logger.info(str(user.id) + "在猜数字游戏中输入的不是数字!")
            send = qqbot.MessageSendRequest("<@%s>" % message.author.id + "，不好意思，您输入的不是数字，请重新输入", message.id)
    return send
'''
    计算器功能
'''
def calculate(message, user, content):
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
    return send

'''
    回复功能
''' 
def reference(message):
    message_reference = MessageReference()
    message_reference.message_id = message.id
    # 返回引用消息
    send = qqbot.MessageSendRequest(content="<emoji:74>没关系，这些都是腾生应该做的，如果满意的话，就发个offer吧", msg_id=message.id, message_reference=message_reference)
    return send