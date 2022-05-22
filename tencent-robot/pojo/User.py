class User:
    def __init__(self, id, poetry_score, num_score, visit_time) -> None:
        self.id = id
        self.poetry_score = poetry_score
        self.num_score = num_score
        self.visit_time = visit_time
    
    def __str__(self) -> str:
        return "用户id为:%s, 用户诗歌诗歌游戏得分为:%s, 用户猜数字得分为:%s, 用户第一次访问系统时间为:%s" % (self.id, self.poetry_score, self.num_score, self.visit.time)