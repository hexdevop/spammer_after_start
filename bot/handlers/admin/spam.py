from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from fluent.runtime import FluentLocalization
from fluent.runtime.types import fluent_number
from sqlalchemy import select, update, case, delete

from bot.services import PostManager
from config import config
from database import get_session
from database.models import Post
from bot.keyboards.admin import inline
from bot.keyboards.admin.factory import SpamCallbackData
from bot.states import SpamState
from bot.utils import helper
from bot.enums import MediaType, Status

router = Router()


@router.message(F.text == "Спам 💬")
async def spam_list(
        event: types.Message | types.CallbackQuery,
        state: FSMContext,
        l10n: FluentLocalization,
        edit: bool = False,
        page: int = 1,
):
    await state.clear()
    message = event if isinstance(event, types.Message) else event.message
    method = message.edit_text if edit else message.answer
    async with get_session() as session:
        posts = (
            await session.scalars(select(Post).offset((page - 1) * 16).limit(16))
        ).all()
    await method(
        text=l10n.format_value(
            "spam-list",
            {
                "types": MediaType.types(),
                "username": config.bot.username,
                "user_id": fluent_number(event.from_user.id, useGrouping=False),
                "counter": config.counter,
            },
        ),
        reply_markup=inline.spam_list(posts, page=page),
    )


@router.callback_query(SpamCallbackData.filter(F.action == "main"))
async def main(
        call: types.CallbackQuery,
        callback_data: SpamCallbackData,
        state: FSMContext,
        l10n: FluentLocalization,
):
    await spam_list(call, state, l10n, edit=True, page=callback_data.page)


@router.callback_query(SpamCallbackData.filter(F.action == "add"))
async def add_spam_post(
        call: types.CallbackQuery,
        callback_data: SpamCallbackData,
        state: FSMContext,
        l10n: FluentLocalization,
):
    await state.clear()
    message_id = (
        await call.message.edit_text(
            text=l10n.format_value("get-new-post", {"types": MediaType.types()}),
            reply_markup=inline.cancel(callback_data, "main"),
        )
    ).message_id
    await state.update_data(message_id=message_id)
    await state.update_data(callback_data=callback_data.model_dump())
    await state.set_state(SpamState.post)


@router.message(SpamState.post)
async def get_post(
        message: types.Message,
        state: FSMContext,
        l10n: FluentLocalization,
):
    data = await state.get_data()
    await helper.delete_messages(message, data)
    callback_data = SpamCallbackData.model_validate(data.get("callback_data"))
    media_type = MediaType.get_type(message.content_type)
    if media_type is not None:
        if media_type is MediaType.TEXT:
            file_id = None
        else:
            if media_type is MediaType.PHOTO:
                file_id = message.photo[-1].file_id
            else:
                file_id = getattr(message, message.content_type).file_id
        post = Post(
            media_type=media_type,
            media=file_id,
            text=message.html_text,
            reply_markup=message.reply_markup.model_dump() if message.reply_markup else None,
        )
        async with get_session() as session:
            async with session.begin():
                session.add(post)
                await session.flush()
        await message.answer(
            text=l10n.format_value("post-successfully-added", {"id": post.id})
        )
        await state.clear()
        await spam_list(message, state, l10n, edit=False, page=callback_data.page)
    else:
        message_id = (
            await message.answer(
                text=l10n.format_value(
                    "unsupported-post-type", {"types": MediaType.types()}
                ),
                reply_markup=inline.cancel(callback_data, "main"),
            )
        ).message_id
        await state.update_data(message_id=message_id)


@router.callback_query(SpamCallbackData.filter(F.action == "settings"))
async def spam_settings(
        call: types.CallbackQuery,
        callback_data: SpamCallbackData,
        state: FSMContext,
        l10n: FluentLocalization,
):
    await state.clear()
    async with get_session() as session:
        post = await session.scalar(
            select(Post).where(Post.id == callback_data.id)
        )
    await call.message.edit_text(
        text=l10n.format_value(
            "spam-settings",
            {
                "id": post.id,
                "media_type": post.media_type.value,
                "text": post.text or l10n.format_value("null"),
                "keyboard": "✅" if post.reply_markup else l10n.format_value("null"),
                "sent": post.sent,
                "status": post.status.value,
            },
        ),
        reply_markup=inline.spam_settings(callback_data),
    )


@router.callback_query(SpamCallbackData.filter(F.action == "check-post"))
async def check_post(
        call: types.CallbackQuery,
        callback_data: SpamCallbackData,
):
    async with get_session() as session:
        post = await session.scalar(select(Post).where(Post.id == callback_data.id))
        pass


@router.callback_query(SpamCallbackData.filter(F.action == "change-status"))
async def change_working_status(
        call: types.CallbackQuery,
        callback_data: SpamCallbackData,
        state: FSMContext,
        l10n: FluentLocalization,
):
    async with get_session() as session:
        async with session.begin():
            await session.execute(
                update(Post)
                .where(Post.id == callback_data.id)
                .values(
                    status=case(
                        (Post.status == Status.STOPPED, Status.WORKING.name),
                        (Post.status == Status.WORKING, Status.STOPPED.name),
                        else_=Post.status,
                    )
                )
            )
    await spam_settings(call, callback_data, state, l10n)


@router.callback_query(SpamCallbackData.filter(F.action == "delete"))
async def delete_spam(
        call: types.CallbackQuery,
        callback_data: SpamCallbackData,
        l10n: FluentLocalization,
):
    await call.message.edit_text(
        text=l10n.format_value("confirm-deleting"),
        reply_markup=inline.confirm(callback_data, cancel_value="settings"),
    )


@router.callback_query(SpamCallbackData.filter(F.action == "confirm"))
async def confirm_deleting(
        call: types.CallbackQuery,
        callback_data: SpamCallbackData,
        state: FSMContext,
        l10n: FluentLocalization,
):
    async with get_session() as session:
        async with session.begin():
            await session.execute(delete(Post).where(Post.id == callback_data.id))
    await call.message.edit_text(text=l10n.format_value("successfully-deleted"))
    await spam_list(call, state, l10n, edit=False, page=callback_data.page)


@router.callback_query(SpamCallbackData.filter(F.action == "interval"))
async def change_interval(
        call: types.CallbackQuery,
        callback_data: SpamCallbackData,
        state: FSMContext,
        l10n: FluentLocalization,
):
    message_id = (
        await call.message.edit_text(
            text=l10n.format_value('get-new-spam-interval'),
            reply_markup=inline.cancel(callback_data, 'main')
        )
    ).message_id
    await state.update_data(message_id=message_id, callback_data=callback_data.model_dump())
    await state.set_state(SpamState.interval)


@router.message(SpamState.interval, F.text)
async def get_new_interval(
        message: types.Message,
        state: FSMContext,
        l10n: FluentLocalization,
        post_manager: PostManager,
):
    data = await state.get_data()
    await helper.delete_messages(message, data)
    callback_data = SpamCallbackData.model_validate(data.get('callback_data'))
    if message.text.isdigit():
        config.interval = int(message.text)
        await spam_list(message, state, l10n, edit=False, page=callback_data.page)
        await post_manager.update_all_intervals(config.interval)
    else:
        message_id = (
            await message.answer(
                text=l10n.format_value('get-new-spam-interval'),
                reply_markup=inline.cancel(callback_data, 'main')
            )
        ).message_id
        await state.update_data(message_id=message_id)


@router.callback_query(SpamCallbackData.filter(F.action == "page"))
async def pagination(
        call: types.CallbackQuery,
        callback_data: SpamCallbackData,
        state: FSMContext,
        l10n: FluentLocalization,
):
    await spam_list(call, state, l10n, edit=True, page=callback_data.page)
    await call.answer(text=l10n.format_value("page", {"page": callback_data.page}))


@router.callback_query(SpamCallbackData.filter(F.action == "length"))
async def length_of_list(
        call: types.CallbackQuery,
        l10n: FluentLocalization,
):
    await call.answer(text=l10n.format_value("length-of-list"), show_alert=True)
