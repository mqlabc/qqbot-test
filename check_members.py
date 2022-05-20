import sqlite3
import qqbot
import os


def execute_sql(sql):
    """
    在./testsqlite.db中执行sql的工具方法
    """
    # 第一步，链接数据，括号里放的是要连接的数据库的名称
    connect = sqlite3.connect("testsqlite.db")
    # 第二步，获取数据库游标，并用变量接收
    cursor = connect.cursor()
    # 第四步，执行sql语句，用游标的execute()方法,把写好的sql语句放进去执行：
    res = cursor.execute(sql).fetchall()
    # 第五步，关闭游标
    cursor.close()
    # 第六步，提交事务
    connect.commit()
    # 第七步，关闭数据库
    connect.close()
    return res


def get_yestoday(guild_id):
    """
    从数据库中查询昨天及其之前进入频道guild的成员列表
    """
    yestoday_sql = f"SELECT * FROM member WHERE  guild_id = '{guild_id}' AND julianday(CURRENT_TIMESTAMP) - julianday(joined_at) > 0"
    return execute_sql(yestoday_sql)


def get_member_tuples(member, guild_id):
    """
    将成员对象转换为元组
    """
    return (member.user.id, guild_id, member.joined_at)


def get_members(guild_id, token):
    """
    调用API查询频道guild目前的成员列表
    """
    api = qqbot.GuildMemberAPI(token, False)
    max_id = 0
    query_params = qqbot.QueryParams(max_id, 1000)
    members_query_result = api.get_guild_members(guild_id, query_params)
    # 解包
    members = list(
        map(
            get_member_tuples,
            members_query_result,
            [guild_id] * len(members_query_result),
        )
    )
    # 找到当前的最大成员id
    max_id = max([int(member[0]) for member in members])
    while True:
        query_params = qqbot.QueryParams(str(max_id), 1000)
        members_query_result = api.get_guild_members(guild_id, query_params)
        # max_id更新后仍然可以查到机器人，因此可以认为当返回的成员全部是机器人时，成员列表已经获取完毕
        new_members = []
        is_bot = []
        for member in members_query_result:
            new_members.append(get_member_tuples(member, guild_id))
            if "2" in member.roles:
                is_bot.append(True)
            else:
                is_bot.append(False)
        if all(is_bot):
            break
        members.extend(new_members)
    return members


async def check_members_change(guild_id, token):
    """
    通过检查当前成员列表与数据库中成员列表的差异，得到当前成员列表相对昨日的变化
    """
    # 目前的所有成员
    now_members = get_members(guild_id, token)
    now_set = set(now_members)
    # 昨天之前加入的
    pre_members = get_yestoday(guild_id)
    pre_set = set(pre_members)
    # 计算新增用户
    new_members = now_set - pre_set
    # nums_new = len(new_members)
    # 计算退出用户
    quit_members = pre_set - now_set
    # nums_quit = len(quit_members)
    return new_members, quit_members

async def update_db(token):
    """
    在每天凌晨定时执行，检查所有频道的成员变化，以更新数据库
    """
    # 获取所有频道
    api = qqbot.UserAPI(token, False)
    guilds = api.me_guilds()
    for guild in guilds:
        new_members, quit_members = await check_members_change(guild.id, token)
        for nm in new_members:
            # 插入或者更新
            insert_or_update_sql = f"replace into member values {nm}"
            execute_sql(insert_or_update_sql)
            pass
        for qm in quit_members:
            # 删除
            delete_sql = (
                f"delete from member where member_id = '{qm[0]}' and guild_id = '{qm[1]}'"
            )
            execute_sql(delete_sql)

if __name__ == "__main__":
    # 数据库不存在，需要新建数据库
    if not os.path.exists("testsqlite.db"):
        create_db_sql = "CREATE TABLE member(member_id VARCHAR(40), guild_id VARCHAR(40) not null, joined_at DATETIME not null, PRIMARY KEY(member_id, guild_id));"
        execute_sql(create_db_sql)

    token = qqbot.Token("102006239", "qdW15z6VhVv9EARny0GPsNIGf0pzJt8b")
    api = qqbot.GuildMemberAPI(token, False)
    guild_id = "17978458913365220461"

    update_db(token)
