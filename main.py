import qqbot
import os
from check_members import update_db, check_members_change, execute_sql
from apscheduler.schedulers.asyncio import AsyncIOScheduler


async def _message_handler(event, message: qqbot.Message):
    """
    判断是否为check_members_change指令，若是，则构造消息并返回
    """
    msg_api = qqbot.AsyncMessageAPI(token, False)
    # 日志打印@机器人的信息
    qqbot.logger.info("event %s" % event + ",receive message %s" % message.content)
    guild_id = message.guild_id
	# 识别change/指令
    # start_index为消息正文起始位置
    start_index = message.content.find('> ') + 2
    if "change/" == message.content[start_index:]:
        new_members, quit_members = await check_members_change(guild_id, token)
        nums_new = len(new_members)
        nums_quit = len(quit_members)
        # 构造消息发送请求数据对象
        reply = f"本频道当前相比昨日，新增成员：{nums_new}，退出成员：{nums_quit}"
        send = qqbot.MessageSendRequest(f"<@{message.author.id}> {reply}", message.id)
        # 通过api发送回复消息
        await msg_api.post_message(message.channel_id, send)


if __name__ == "__main__":
    # 数据库不存在，需要新建数据库
    if not os.path.exists("testsqlite.db"):
        create_db_sql = "CREATE TABLE member(member_id VARCHAR(40), guild_id VARCHAR(40) not null, joined_at DATETIME not null, PRIMARY KEY(member_id, guild_id));"
        execute_sql(create_db_sql)
    token = qqbot.Token("102006239", "qdW15z6VhVv9EARny0GPsNIGf0pzJt8b")
	# 定时更新成员列表数据库
    scheduler = AsyncIOScheduler()
    scheduler.add_job(update_db, "cron", (token,), hour=0, minute=0)
    # scheduler.add_job(update_db, "cron", (token,), hour=10, minute=34)
    scheduler.start()

    qqbot_handler = qqbot.Handler(
        qqbot.HandlerType.AT_MESSAGE_EVENT_HANDLER, _message_handler
    )
    qqbot.async_listen_events(token, False, qqbot_handler)
