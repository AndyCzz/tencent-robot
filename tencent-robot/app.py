import qqbot
import yaml
import os
from service.userService import showPersonalInfo, getAvatarSketch, getPermission, writePoetry, guessNum, calculate, reference, initUser
from utils.dbUtil import getRedisInstance
from qqbot.model.api_permission import APIPermissionDemandIdentify, PermissionDemandToCreate

os.environ["QQBOT_LOG_PATH"] = os.path.join(os.getcwd(), "log", "%(name)s.log")

with open("./config/config.yaml", "r") as f:
    config = yaml.load(f.read(), Loader=yaml.FullLoader)
appId = config["token"]["appId"]
token = config["token"]["token"]

# 应用服务器地址和端口，用来形成图片的http url
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


async def _message_handler(event, message):
    # 获得相应对象的操作api
    msg_api = qqbot.AsyncMessageAPI(token, False)
    api_permission_api = qqbot.AsyncAPIPermissionAPI(token, False)
    
    # 如果用户是第一次访问
    user = message.author
    # 用户初次访问时的初始化
    initUser(user)
    content = message.content
    # 打印返回信息
    qqbot.logger.info("event %s" % event + ",receive message: %s" % content)
    # 构造消息发送请求数据对象
    send = qqbot.MessageSendRequest("<@%s>,你好，我是您的专属机器人，请问有什么可以为您服务的？" % message.author.id, message.id)
    
    if "/个人信息" in content:
        send = showPersonalInfo(user, message)
       
    if "/头像素描" in content:
        send = getAvatarSketch(user, message, base_url, port)
        
    if "/请求权限" in content:
        # send = getPermission(message, api_permission_api)
        demand_identity = APIPermissionDemandIdentify("/guilds/{guild_id}/members/{user_id}", "GET")
        permission_demand_to_create = PermissionDemandToCreate(message.channel_id, demand_identity)
        demand = await api_permission_api.post_permission_demand(message.guild_id, permission_demand_to_create)
        qqbot.logger.info("api title: %s" % demand.title + ", desc: %s" % demand.desc)
        send = qqbot.MessageSendRequest("")
        
    if "/默写古诗词" in content:
        send = writePoetry(message, user, content, poetry_dict)
        
    if "/猜数字" in content:
        send = guessNum(message, user, content)
        
    if "/计算器" in content:
        send = calculate(message, user, content)
        
    if "谢谢" in content or "真棒" in content:
        send = reference(message)
        
    # 通过api发送回复消息
    await msg_api.post_message(message.channel_id, send)

if __name__ == '__main__':
    qqbot_handler = qqbot.Handler(qqbot.HandlerType.AT_MESSAGE_EVENT_HANDLER, _message_handler)
    qqbot.async_listen_events(token, False, qqbot_handler)
