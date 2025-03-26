import sys
import uuid
import asyncio
import astrbot.api.message_components as Comp

from astrbot.api.platform import (
    Platform,
    AstrBotMessage,
    MessageMember,
    PlatformMetadata,
    MessageType,
)
from astrbot.api.event import MessageChain
from astrbot.core.platform.astr_message_event import MessageSesion
from astrbot.api.platform import register_platform_adapter

from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, filters
from telegram.constants import ChatType
from telegram.ext import MessageHandler as TelegramMessageHandler
from .tg_event import TelegramPlatformEvent
from astrbot.api import logger
from telegram.ext import ExtBot

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override


@register_platform_adapter("telegram", "telegram 适配器")
class TelegramPlatformAdapter(Platform):
    def __init__(
        self, platform_config: dict, platform_settings: dict, event_queue: asyncio.Queue
    ) -> None:
        super().__init__(event_queue)
        self.config = platform_config
        self.settings = platform_settings
        self.client_self_id = uuid.uuid4().hex[:8]

        base_url = self.config.get(
            "telegram_api_base_url", "https://api.telegram.org/bot"
        )
        if not base_url:
            base_url = "https://api.telegram.org/bot"

        file_base_url = self.config.get(
            "telegram_file_base_url", "https://api.telegram.org/file/bot"
        )
        if not file_base_url:
            file_base_url = "https://api.telegram.org/file/bot"

        self.base_url = base_url

        self.application = (
            ApplicationBuilder()
            .token(self.config["telegram_token"])
            .base_url(base_url)
            .base_file_url(file_base_url)
            .build()
        )
        message_handler = TelegramMessageHandler(
            filters=filters.ALL,  # receive all messages
            callback=self.message_handler,
        )
        self.application.add_handler(message_handler)
        self.client = self.application.bot
        logger.debug(f"Telegram base url: {self.client.base_url}")

    @override
    async def send_by_session(
        self, session: MessageSesion, message_chain: MessageChain
    ):
        from_username = session.session_id
        await TelegramPlatformEvent.send_with_client(
            self.client, message_chain, from_username
        )
        await super().send_by_session(session, message_chain)

    @override
    def meta(self) -> PlatformMetadata:
        return PlatformMetadata(
            "telegram",
            "telegram 适配器",
        )

    @override
    async def run(self):
        await self.application.initialize()
        await self.application.start()
        queue = self.application.updater.start_polling()
        logger.info("Telegram Platform Adapter is running.")
        await queue

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=self.config["start_message"]
        )

    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        logger.debug(f"Telegram message: {update.message}")
        abm = await self.convert_message(update, context)
        if abm:
            await self.handle_msg(abm)

    async def convert_message(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, get_reply=True
    ) -> AstrBotMessage:
        """转换 Telegram 的消息对象为 AstrBotMessage 对象。

        @param update: Telegram 的 Update 对象。
        @param context: Telegram 的 Context 对象。
        @param get_reply: 是否获取回复消息。这个参数是为了防止多个回复嵌套。
        """
        message = AstrBotMessage()
        message.session_id = str(update.message.chat.id)
        # 获得是群聊还是私聊
        if update.message.chat.type == ChatType.PRIVATE:
            message.type = MessageType.FRIEND_MESSAGE
        else:
            message.type = MessageType.GROUP_MESSAGE
            message.group_id = str(update.message.chat.id)
            if update.message.message_thread_id:
                # Topic Group
                message.group_id += "#" + str(update.message.message_thread_id)
                message.session_id = message.group_id

        message.message_id = str(update.message.message_id)
        message.sender = MessageMember(
            str(update.message.from_user.id), update.message.from_user.username
        )
        message.self_id = str(context.bot.username)
        message.raw_message = update
        message.message_str = ""
        message.message = []

        if update.message.reply_to_message and not (
            update.message.is_topic_message
            and update.message.message_thread_id
            == update.message.reply_to_message.message_id
        ):
            # 获取回复消息
            reply_update = Update(
                update_id=1,
                message=update.message.reply_to_message,
            )
            reply_abm = await self.convert_message(reply_update, context, False)

            message.message.append(
                Comp.Reply(
                    id=reply_abm.message_id,
                    chain=reply_abm.message,
                    sender_id=reply_abm.sender.user_id,
                    sender_nickname=reply_abm.sender.nickname,
                    time=reply_abm.timestamp,
                    message_str=reply_abm.message_str,
                    text=reply_abm.message_str,
                    qq=reply_abm.sender.user_id,
                )
            )

        if update.message.text:
            # 处理文本消息
            plain_text = update.message.text

            if update.message.entities:
                for entity in update.message.entities:
                    if entity.type == "mention":
                        name = plain_text[
                            entity.offset + 1 : entity.offset + entity.length
                        ]
                        message.message.append(Comp.At(qq=name, name=name))
                        plain_text = (
                            plain_text[: entity.offset]
                            + plain_text[entity.offset + entity.length :]
                        )

            if plain_text:
                message.message.append(Comp.Plain(plain_text))
            message.message_str = plain_text

            if message.message_str.strip() == "/start":
                await self.start(update, context)
                return

        elif update.message.voice:
            file = await update.message.voice.get_file()
            message.message = [
                Comp.Record(file=file.file_path, url=file.file_path),
            ]

        elif update.message.photo:
            photo = update.message.photo[-1]  # get the largest photo
            file = await photo.get_file()
            message.message.append(Comp.Image(file=file.file_path, url=file.file_path))
            if update.message.caption:
                message.message_str = update.message.caption
                message.message.append(Comp.Plain(message.message_str))
            if update.message.caption_entities:
                for entity in update.message.caption_entities:
                    if entity.type == "mention":
                        name = message.message_str[
                            entity.offset + 1 : entity.offset + entity.length
                        ]
                        message.message.append(Comp.At(qq=name, name=name))

        elif update.message.sticker:
            # 将sticker当作图片处理
            file = await update.message.sticker.get_file()
            message.message.append(Comp.Image(file=file.file_path, url=file.file_path))
            if update.message.sticker.emoji:
                sticker_text = f"Sticker: {update.message.sticker.emoji}"
                message.message_str = sticker_text
                message.message.append(Comp.Plain(sticker_text))

        elif update.message.document:
            file = await update.message.document.get_file()
            message.message = [
                Comp.File(file=file.file_path, name=update.message.document.file_name),
            ]

        elif update.message.video:
            file = await update.message.video.get_file()
            message.message = [
                Comp.Video(file=file.file_path, path=file.file_path),
            ]

        return message

    async def handle_msg(self, message: AstrBotMessage):
        message_event = TelegramPlatformEvent(
            message_str=message.message_str,
            message_obj=message,
            platform_meta=self.meta(),
            session_id=message.session_id,
            client=self.client,
        )
        self.commit_event(message_event)

    def get_client(self) -> ExtBot:
        return self.client

    async def terminate(self):
        try:
            await self.application.stop()

            # 保险起见先判断是否存在updater对象
            if self.application.updater is not None:
                await self.application.updater.stop()

            logger.info("Telegram 适配器已被优雅地关闭")
        except Exception as e:
            logger.error(f"Telegram 适配器关闭时出错: {e}")
