import ast
import asyncio
import random
import re
import string
import time
from datetime import datetime
from math import ceil
from typing import List

import validators
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.media_group import MediaGroupBuilder
from aiogram_media_group import media_group_handler

from Bot import keyboard, states, sheets
from Bot.filters import StatesGroupHandle
from Bot.utils import pointWords, formatts, formatedtotts, getuserstats, checkrole
from config import FORMSSHEET, FORMURL, FRACTIONS, ROLES, SUPPORT_ROLES, ADMIN
from db import Chats, Users, Settings_s, Settings_l, Settings_a, Inactives, Removed, Forms, \
    InactiveRequests, Sheets, SpecialAccesses, Objectives

router: Router = Router()


@router.message(Command('id'), F.chat.type == "private")
async def id(message: Message, state: FSMContext):
    await message.delete()
    msg = await message.bot.send_message(chat_id=message.chat.id,
                                         text=f'🆔 <b>UserID:</b> <code>{message.from_user.id}</code>')
    await state.clear()
    await state.update_data(msg=msg)


@router.message(CommandStart(), F.chat.type == "private")
async def start(message: Message, state: FSMContext):
    await message.delete()
    user = Users.get_or_none(Users.telegram_id == message.from_user.id)
    if not user:
        await message.bot.send_message(chat_id=message.chat.id, text='У вас нет доступа к этому боту.')
    else:
        isswatcher = SpecialAccesses.get_or_none(SpecialAccesses.telegram_id == user.telegram_id,
                                                 SpecialAccesses.role == 'swatcher') is not None
        text = 'Список коротких команд:\n'
        if user.telegram_id in ADMIN:
            text += '/fill - Вручную заполнить таблицы.\n'
        # if user.role == 'Главный администратор':
        #     text += '/zov <TEXT> - Отправит всем администраторам уведомление с указанным текстом.\n'
        #     text += '/send <TEXT> - Отправит всем, кто имеет доступ к боту “АП, Лидеры, Админы”.\n'
        if user.role in ('главный администратор', 'куратор администрации'):
            text += '/check <NICK> - Покажет список неактивов пользователя.\n'
        if user.role in ('Главный администратор', 'Основной ЗГА', 'Заместитель ГА', 'Куратор администрации',
                         'Главный за лидерами', 'Главный следящий ГОСС', 'Главный следящий ОПГ', 'Заместитель ГС ГОСС',
                         'Заместитель ГС ОПГ', 'Главный АП', 'Главный следящий АП', 'Заместитель ГС АП') or isswatcher:
            text += '/stats <NICK> - Покажет информацию о пользователе и возможные с ним действия.\n'
        if user.role in ROLES:
            text += '/form - Создать форму.\n'
        if user.role in (
                'Главный за лидерами', 'Главный следящий ГОСС', 'Главный следящий ОПГ', 'Заместитель ГС ГОСС',
                'Заместитель ГС ОПГ', 'Главный администратор', 'Основной ЗГА', 'Заместитель ГА'):
            text += '/ld - Управление ЛД.\n'
            text += '/addld - Назначить лидера.\n'
            text += '/ball - Управление баллами.\n'
            text += '/ld_p - Наказать лидера.\n'
        if user.role in ('Куратор администрации', 'Главный администратор', 'Основной ЗГА', 'Заместитель ГА'):
            text += '/adm - Управление АДМ.\n'
            text += '/addadm - Назначить администратора.\n'
            text += '/rep - Управление ответами.\n'
            text += '/adm_p - Наказать администратора.\n'
        if user.role in ('Главный АП', 'Главный следящий АП', 'Заместитель ГС АП', 'Главный администратор',
                         'Основной ЗГА', 'Заместитель ГА') or isswatcher:
            text += '/ap - Управление АП.\n'
            text += '/addap - Назначить агента поддержки.\n'
            text += '/ask - Управление асками.\n'
            text += '/ap_p - Наказать агента поддержки.\n'
        if user.role in ('Главный администратор', 'Основной ЗГА', 'Заместитель ГА'):
            text += '/sc - Управление сервером.\n'

        msg = await message.bot.send_message(chat_id=message.chat.id, reply_markup=keyboard.start(), text=text,
                                             parse_mode=None)
        await msg.pin()
    await state.clear()


@router.callback_query(keyboard.Callback.filter(F.type == 'panel'))
async def panel(query: CallbackQuery, state: FSMContext):
    await query.answer()
    user = Users.get_or_none(Users.telegram_id == query.from_user.id)
    if not user:
        await query.bot.send_message(chat_id=query.from_user.id, text='У вас нет доступа к этому боту.')
    else:
        msg = await query.bot.send_message(
            chat_id=query.from_user.id, text='Добро пожаловать в главное меню.',
            reply_markup=keyboard.panel(
                user.role, SpecialAccesses.get_or_none(SpecialAccesses.telegram_id == user.telegram_id,
                                                       SpecialAccesses.role == 'swatcher') is not None))
        await state.clear()
        await state.update_data(msg=msg)


@router.message(Command('fill'), F.chat.type == "private")
async def fill(message: Message, state: FSMContext):  # noqa
    if message.from_user.id not in ADMIN:
        return
    sheets.main(True, True, True)
    msg = await message.bot.send_message(chat_id=message.from_user.id, text='✅ Обновление запущено.')
    await state.clear()
    await state.update_data(msg=msg)


@router.message(Command('zov', 'send'), F.chat.type == "private")
async def zov(message: Message, state: FSMContext):
    user = Users.get_or_none(Users.telegram_id == message.from_user.id)
    if not user or user.role.lower() != 'главный администратор':
        return
    k = 0
    if 'zov' in message.text.split()[0]:
        users = Users.select().where(Users.role.not_in(SUPPORT_ROLES), Users.fraction.is_null(True))
        un = ("администратору", "администраторам", "администраторам")
    else:
        users = Users.select()
        un = ("пользователю", "пользователям", "пользователям")
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    for i in users:
        try:
            await message.bot.send_message(chat_id=i.telegram_id, text=' '.join(message.text.split()[1:]))
            k += 1
        except:
            pass
        await asyncio.sleep(0.1)
    await message.delete()
    msg = await message.bot.send_message(
        chat_id=message.chat.id, text=f'✅ Сообщение было доставлено {k} {pointWords(k, un)}.')
    await state.clear()
    await state.update_data(msg=msg)


@router.message(Command('check'), F.chat.type == "private")
async def check(message: Message, state: FSMContext):
    await message.delete()
    user = Users.get_or_none(Users.telegram_id == message.from_user.id)
    if not user or user.role.lower() not in ('главный администратор', 'куратор администрации'):
        return
    if message.text.strip().split()[-1].isdigit():
        n = 'ID'
        user: Users = Users.get_or_none(Users.telegram_id == message.text.strip().split()[-1])
    else:
        n = 'ником'
        user: Users = Users.get_or_none(Users.nickname == message.text.strip().split()[-1])
    if not user or not checkrole(Users.get_or_none(Users.telegram_id == message.from_user.id), user):
        msg = await message.bot.send_message(
            chat_id=message.chat.id,
            text=f'⚠️ Пользователя с {n} "<code>{message.text.strip().split()[-1]}</code>'
                 f'" не существует.')
        await state.update_data(msg=msg)
        return
    text = f'🌐 Список неактивов пользователя - <a href="tg://user?id={user.telegram_id}">{user.nickname}</a>\n'
    inactives = Inactives.select().where(Inactives.nickname == user.nickname)
    for k, i in enumerate(inactives):
        text += f'\n[{k + 1}]. <code>{i.start} - {i.end}</code> | {i.status}' + (f' | {i.reason}' if i.reason else '')
    msg = await message.bot.send_message(chat_id=message.from_user.id, text=text)
    await state.clear()
    await state.update_data(msg=msg)


@router.message(Command('stats'), F.chat.type == "private")
async def stats(message: Message, state: FSMContext):
    await message.delete()
    admin = Users.get_or_none(Users.telegram_id == message.from_user.id)
    if message.text.strip().split()[-1].isdigit():
        user: Users = Users.get_or_none(Users.telegram_id == int(message.text.strip().split()[-1]))
    else:
        user: Users = Users.get_or_none(Users.nickname == message.text.strip().split()[-1])
    if not user or not admin or not checkrole(admin, user):
        msg = await message.bot.send_message(
            chat_id=message.chat.id,
            text=f'⚠️ Пользователя не существует или вы не имеете доступа к этому пользователю.')
        await state.update_data(msg=msg)
        return
    text = getuserstats(user)
    msg = await message.bot.send_message(chat_id=message.chat.id, text=text,
                                         reply_markup=keyboard.stats(user.role, user.get_id()))
    await state.clear()
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type.startswith('removereason_')))
async def removereason_(query: CallbackQuery, state: FSMContext):
    msg = await query.bot.send_message(chat_id=query.from_user.id, text=f'Введите причину:')
    await state.clear()
    await state.set_state(states.Stats.remove.state)
    await state.update_data(msg=msg, user=int(query.data.split(':')[-1].split('_')[-1]))


@router.callback_query(keyboard.Callback.filter(F.type == 'swatchers'))
async def swatchers(query: CallbackQuery, state: FSMContext):
    msg = await query.bot.send_message(chat_id=query.from_user.id, reply_markup=keyboard.swatchers(),
                                       text='Управление следящими за АП')
    await state.clear()
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type.in_(('addswatcher', 'remswatcher'))))
async def addremswatcher(query: CallbackQuery, state: FSMContext):
    msg = await query.bot.send_message(chat_id=query.from_user.id, text=f'Введите никнейм:')
    await state.clear()
    if 'rem' in query.data:
        await state.set_state(states.Swatchers.rem.state)
    else:
        await state.set_state(states.Swatchers.add.state)
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type == 'listswatcher'))
async def listswatcher(query: CallbackQuery, state: FSMContext):
    swatchers = SpecialAccesses.select().where(SpecialAccesses.role == 'swatcher')
    text = f'❇️ Список пользователей с доступом к управлению АП - {len(swatchers)}\n\n'
    for k, i in enumerate(swatchers):
        if not (user := Users.get_or_none(Users.telegram_id == i.telegram_id)):
            continue
        text += f'[{k + 1}]. <a href="tg://user?id={user.telegram_id}">{user.nickname}</a> | <code>{user.role}</code>\n'
    msg = await query.bot.send_message(chat_id=query.from_user.id, text=text)
    await state.clear()
    await state.update_data(msg=msg)


@router.message(states.Swatchers.add)
async def swatchersadd(message: Message, state: FSMContext):
    await message.delete()
    if not (user := Users.get_or_none(Users.nickname == message.text.strip())):
        msg = await message.bot.send_message(chat_id=message.from_user.id,
                                             text='⚠️ Пользователя нет в списке следящих за АП.\nВведите никнейм:')
        await state.update_data(msg=msg)
        return
    SpecialAccesses.create(telegram_id=user.telegram_id, role='swatcher')
    msg = await message.bot.send_message(
        chat_id=message.from_user.id,
        text=f'✅ Вы успешно дали доступ пользователю <a href="tg://user?id={user.telegram_id}">{user.nickname}</a> '
             f'к управлению АП.')
    await state.clear()
    await state.update_data(msg=msg, nickname=message.text.strip())


@router.message(states.Swatchers.rem)
async def swatchersadd(message: Message, state: FSMContext):
    await message.delete()
    user = Users.get_or_none(Users.nickname == message.text.strip())
    if not user or not (suser := SpecialAccesses.get_or_none(SpecialAccesses.telegram_id == user.telegram_id)):
        msg = await message.bot.send_message(chat_id=message.from_user.id,
                                             text='⚠️ Пользователя нет в списке следящих за АП.\nВведите никнейм:')
        await state.update_data(msg=msg)
        return
    suser.delete_instance()
    msg = await message.bot.send_message(
        chat_id=message.from_user.id,
        text=f'✅ Вы успешно убрали права пользователя <a href="tg://user?id={user.telegram_id}">{user.nickname}</a> '
             f'к управлению АП.')
    await state.clear()
    await state.update_data(msg=msg, nickname=message.text.strip())


@router.callback_query(keyboard.Callback.filter(F.type.startswith('transfer_')))
async def transfer_(query: CallbackQuery, state: FSMContext):
    user: Users = Users.get_by_id(int(query.data.split(':')[-1].split('_')[-1]))
    if not (Settings_s.get(Settings_s.setting == 'transferamnt_d').val <= ceil((time.time() - user.appointed) / 86400)
            and Settings_s.get(Settings_s.setting == 'transferamnt_a').val <= user.apa):
        await query.bot.send_message(
            chat_id=query.from_user.id, text=f'Данный агент поддержки не подходит под минимальные требования перевода.')
        await state.clear()
        return
    user.role = 'Кандидат'
    user.save()
    msg = await query.bot.send_message(
        chat_id=query.from_user.id,
        text=f'✅ Вы успешно установили должность "<code>Кандидат</code>" для агента поддержки '
             f'<a href="tg://user?id={user.telegram_id}">{user.nickname}</a>.')
    await state.clear()
    await state.update_data(msg=msg)
    sheets.main(composition=True)


@router.callback_query(keyboard.Callback.filter(F.type == 'mystats'))
async def mystats(query: CallbackQuery, state: FSMContext):
    user: Users = Users.get_or_none(Users.telegram_id == query.from_user.id)
    text = getuserstats(user)
    msg = await query.bot.send_message(chat_id=query.from_user.id, text=text)
    await state.clear()
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type == 'myinactives'))
async def myinactives(query: CallbackQuery, state: FSMContext):
    msg = await query.bot.send_message(chat_id=query.from_user.id, text='Управление неактивами:',
                                       reply_markup=keyboard.myinactives())
    await state.clear()
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type == 'takeinactive'))
async def takeinactive(query: CallbackQuery, state: FSMContext):
    msg = await query.bot.send_message(
        chat_id=query.from_user.id, text='Введите дату неактива (формат: "15.12.2024 - 18.12.2024"):')
    await state.clear()
    await state.set_state(states.Inactives.take.state)
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type == 'cancelinactive'))
async def cancelinactive(query: CallbackQuery, state: FSMContext):
    user: Users = Users.get_or_none(Users.telegram_id == query.from_user.id)
    if not user or not user.inactiveend or user.inactiveend < time.time():
        msg = await query.bot.send_message(chat_id=query.from_user.id, text='⚠️ У вас нет активного неактива.')
        await state.update_data(msg=msg)
        return
    msg = await query.bot.send_message(chat_id=query.from_user.id, text='Вы уверены, что хотите снять неактив?',
                                       reply_markup=keyboard.cancelinactive())
    await state.clear()
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type == 'cancelinactive_y'))
async def cancelinactive_y(query: CallbackQuery, state: FSMContext):
    user: Users = Users.get_or_none(Users.telegram_id == query.from_user.id)
    user.inactivestart = None
    user.inactiveend = None
    user.save()
    msg = await query.bot.send_message(chat_id=query.from_user.id, text='Вы успешно сняли текущий неактив.')
    await state.clear()
    await state.update_data(msg=msg)
    sheets.main(composition=True)


@router.callback_query(keyboard.Callback.filter(F.type == 'inactive_take_y'))
async def inactive_take_y(query: CallbackQuery, state: FSMContext):
    msg = await query.bot.send_message(chat_id=query.from_user.id, text='Введите причину:')
    await state.set_state(states.Inactives.reason.state)
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type.in_(
    ('cancelinactive_n', 'inactive_take_n', 'usersinactiveset_n'))))
async def nobuttons(query: CallbackQuery, state: FSMContext):  # noqa
    await state.clear()


@router.callback_query(keyboard.Callback.filter(F.type == 'listinactive'))
async def listinactive(query: CallbackQuery, state: FSMContext):
    user: Users = Users.get_or_none(Users.telegram_id == query.from_user.id)
    text = f'🌐 Список неактивов пользователя - <a href="tg://user?id={user.telegram_id}">{user.nickname}</a>\n'
    inactives = Inactives.select().where(Inactives.nickname == user.nickname)
    for k, i in enumerate(inactives):
        text += (f'\n[{k + 1}]. <code>{i.start} - {i.end}</code> | {i.status}' +
                 (f' | {i.reason}' if i.reason else ''))
    msg = await query.bot.send_message(chat_id=query.from_user.id, text=text)
    await state.clear()
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type == 'reports'))
async def reports(query: CallbackQuery, state: FSMContext):
    msg = await query.bot.send_message(chat_id=query.from_user.id, text='Управление отчётами:',
                                       reply_markup=keyboard.reports())
    await state.clear()
    await state.update_data(msg=msg)


@router.message(Command('ld'), F.chat.type == "private")
@router.callback_query(keyboard.Callback.filter(F.type == 'leaderscontrol'))
async def leaderscontrol(query: CallbackQuery, state: FSMContext):
    user = Users.get_or_none(Users.telegram_id == query.from_user.id)
    if not user or user.role not in (
            'Главный за лидерами', 'Главный следящий ГОСС', 'Главный следящий ОПГ', 'Заместитель ГС ГОСС',
            'Заместитель ГС ОПГ', 'Главный администратор', 'Основной ЗГА', 'Заместитель ГА'):
        return
    msg = await query.bot.send_message(chat_id=query.from_user.id, text='Управление ЛД:',
                                       reply_markup=keyboard.leaderscontrol())
    await state.clear()
    await state.update_data(msg=msg)


@router.message(Command('adm'), F.chat.type == "private")
@router.callback_query(keyboard.Callback.filter(F.type == 'adminscontrol'))
async def adminscontrol(query: CallbackQuery, state: FSMContext):
    user = Users.get_or_none(Users.telegram_id == query.from_user.id)
    if not user or user.role not in (
            'Куратор администрации', 'Главный администратор', 'Основной ЗГА', 'Заместитель ГА'):
        return
    msg = await query.bot.send_message(chat_id=query.from_user.id, text='Управление АДМ:',
                                       reply_markup=keyboard.adminscontrol())
    await state.clear()
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type == 'sendobjective'))
async def sendobjective(query: CallbackQuery, state: FSMContext):
    msg = await query.bot.send_message(chat_id=query.from_user.id, text='Отправьте скриншот из "<code>/astats</code>":')
    await state.clear()
    await state.set_state(states.Reports.sendobjective.state)
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type == 'sendadditionalreply'))
async def sendadditionalreply(query: CallbackQuery, state: FSMContext):
    msg = await query.bot.send_message(chat_id=query.from_user.id, text='Отправьте скриншоты:')
    await state.clear()
    await state.set_state(states.Reports.sendadditionalreply.state)
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type == 'forms'))
async def forms(query: CallbackQuery, state: FSMContext):
    msg = await query.bot.send_message(chat_id=query.from_user.id, text='Управление формами:',
                                       reply_markup=keyboard.forms())
    await state.clear()
    await state.update_data(msg=msg)


@router.message(Command('form'), F.chat.type == "private")
@router.callback_query(keyboard.Callback.filter(F.type == 'createform'))
async def createform(query: CallbackQuery, state: FSMContext):
    user = Users.get_or_none(Users.telegram_id == query.from_user.id)
    if not user or user.role not in ROLES:
        return
    msg = await query.bot.send_message(chat_id=query.from_user.id,
                                       text='Введите форму(пример "/permban Test test"):')
    await state.clear()
    await state.set_state(states.Forms.create.state)
    await state.update_data(msg=msg)


@router.message(Command('ap'), F.chat.type == "private")
@router.callback_query(keyboard.Callback.filter(F.type == 'supportcontrol'))
async def supportcontrol(query: CallbackQuery, state: FSMContext):
    user = Users.get_or_none(Users.telegram_id == query.from_user.id)
    if not user or (user.role not in (
            'Главный АП', 'Главный следящий АП', 'Заместитель ГС АП', 'Главный администратор', 'Основной ЗГА',
            'Заместитель ГА') and not SpecialAccesses.get_or_none(SpecialAccesses.role == 'swatcher',
                                                                  SpecialAccesses.telegram_id == query.from_user.id)):
        return
    msg = await query.bot.send_message(chat_id=query.from_user.id, text='Управление АП:',
                                       reply_markup=keyboard.supportcontrol())
    await state.clear()
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type.contains('supportlist_')))
async def supportlist(query: CallbackQuery, state: FSMContext):
    page = int(query.data.split(':')[-1].split('_')[1])
    sup = (sorted(Users.select().where(Users.role == SUPPORT_ROLES[1]), key=lambda x: x.appointed) +
           sorted(Users.select().where(Users.role == SUPPORT_ROLES[0]), key=lambda x: x.appointed))
    text = f'📚 Список агентов поддержки - {len(sup)} {pointWords(len(sup), ("человек", "человека", "человек"))}.\n\n'
    for k, i in enumerate(sup[page * 15: (page + 1) * 15]):
        i: Users
        text += (f'[{(15 * page) + 1 + k}]. <a href="tg://user?id={i.telegram_id}">{i.nickname}</a> | '
                 f'<a href="{i.vk}">VK</a> | '
                 f'{i.telegram_id} | <a href="{i.forum}">FA</a> | '
                 f'<code>{i.role}</code>\n')
    msg = await query.bot.send_message(chat_id=query.from_user.id, text=text,
                                       reply_markup=keyboard.supportlist(page, len(sup)))
    await state.clear()
    await state.update_data(msg=msg)


@router.message(Command('addap'), F.chat.type == "private")
@router.callback_query(keyboard.Callback.filter(F.type == 'appoint'))
async def appoint(query: CallbackQuery, state: FSMContext):
    user = Users.get_or_none(Users.telegram_id == query.from_user.id)
    if not user or (user.role not in (
            'Главный АП', 'Главный следящий АП', 'Заместитель ГС АП', 'Главный администратор', 'Основной ЗГА',
            'Заместитель ГА') and not SpecialAccesses.get_or_none(SpecialAccesses.role == 'swatcher',
                                                                  SpecialAccesses.telegram_id == query.from_user.id)):
        return
    msg = await query.bot.send_message(chat_id=query.from_user.id, text=f'Введите никнейм:',)
    await state.clear()
    await state.set_state(states.Appoint.s.state)
    await state.update_data(msg=msg)


@router.message(states.Appoint.s)
async def appoints(message: Message, state: FSMContext):
    await message.delete()
    if '_' not in message.text or ' ' in message.text:
        msg = await message.bot.send_message(chat_id=message.from_user.id,
                                             text='⚠️ Неверный никнейм.\nВведите никнейм:')
        await state.update_data(msg=msg)
        return
    code = ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(8)])
    msg = await message.bot.send_message(
        chat_id=message.from_user.id, reply_markup=keyboard.appointcheck(),
        text=f'Заполните <a href="{FORMURL}">форму</a>.\nПроверочный код: <code>{code}</code>',)
    await state.clear()
    await state.update_data(msg=msg, code=code, nickname=message.text)


@router.callback_query(keyboard.Callback.filter(F.type == 'appointcheck'))
async def appointcheck(query: CallbackQuery, state: FSMContext):
    await query.bot.send_chat_action(chat_id=query.from_user.id, action="typing")
    sdata = sheets.getappointformbycode(FORMSSHEET, (await state.get_data())['code'],
                                        (await state.get_data())['nickname'])
    if sdata is None:
        msg = await query.bot.send_message(
            chat_id=query.from_user.id, reply_markup=keyboard.appointcheck(),
            text=f'⚠️ Форма не найдена.\nЗаполните <a href="{FORMURL}">форму</a>.\nПроверочный код: '
                 f'<code>{(await state.get_data())["code"]}</code>')
        await state.update_data(msg=msg)
        return
    user: Users = Users.get_or_create(telegram_id=int(sdata[7]), defaults={
        'nickname': sdata[0], 'role': SUPPORT_ROLES[0], 'fraction': None, 'appointed': int(time.time()),
        'promoted': None, 'objective_completed': 0, 'apa': 0, 'rebuke': 0, 'warn': 0, 'verbal': 0,
        'inactivestart': None, 'inactiveend': None, 'name': sdata[1], 'age': int(sdata[2]), 'city': sdata[3],
        'discord_id': int(sdata[4]), 'telegram_id': int(sdata[7]), 'forum': sdata[6], 'vk': sdata[5]})
    if user[1]:
        user = user[0]
        user.nickname = sdata[0]
        user.role = SUPPORT_ROLES[0]
        user.fraction = user.promoted = user.inactivestart = user.inactiveend = None
        user.appointed = int(time.time())
        user.objective_completed = user.apa = user.rebuke = user.warn = user.verbal = 0
        user.name = sdata[1]
        user.age = int(sdata[2])
        user.city = sdata[3]
        user.discord_id = int(sdata[4])
        user.telegram_id = int(sdata[7])
        user.forum = sdata[6]
        user.vk = sdata[5]
        user.save()
    else:
        msg = await query.bot.send_message(
            chat_id=query.from_user.id,
            text=f'❌ Пользователь с таким Telegram ID уже существует.')
        await state.clear()
        await state.update_data(msg=msg)
        return
    msg = await query.bot.send_message(
        chat_id=query.from_user.id,
        text=f'✅ Вы успешно назначили нового агента поддержки - <a href="tg://user?id={user.telegram_id}">'
             f'{user.nickname}</a>')
    await state.clear()
    await state.update_data(msg=msg)
    sheets.main(composition=True)


@router.message(Command('addld'), F.chat.type == "private")
@router.callback_query(keyboard.Callback.filter(F.type == 'appointleader'))
async def appointleader(query: CallbackQuery, state: FSMContext):
    user = Users.get_or_none(Users.telegram_id == query.from_user.id)
    if not user or user.role not in (
            'Главный за лидерами', 'Главный следящий ГОСС', 'Главный следящий ОПГ', 'Заместитель ГС ГОСС',
            'Заместитель ГС ОПГ', 'Главный администратор', 'Основной ЗГА', 'Заместитель ГА'):
        return
    msg = await query.bot.send_message(chat_id=query.from_user.id, text=f'Введите никнейм:',)
    await state.set_state(states.Appoint.l.state)
    await state.update_data(msg=msg)


@router.message(states.Appoint.l)
async def appointl(message: Message, state: FSMContext):
    await message.delete()
    if '_' not in message.text or ' ' in message.text:
        msg = await message.bot.send_message(chat_id=message.from_user.id,
                                             text='⚠️ Неверный никнейм.\nВведите никнейм:')
        await state.update_data(msg=msg)
        return
    fracs = list(FRACTIONS)
    for i in Users.select().where(Users.fraction.is_null(False)):
        fracs.remove(i.fraction)
    if len(fracs) == 0:
        msg = await message.bot.send_message(chat_id=message.chat.id, text='❌ Сейчас нет свободных фракций.')
        await state.clear()
        await state.update_data(msg=msg)
        return
    msg = await message.bot.send_message(
        chat_id=message.from_user.id, reply_markup=keyboard.appointl(fracs),
        text='Выберите одну из доступных фракций:',)
    await state.clear()
    await state.update_data(msg=msg, nickname=message.text.strip())


@router.callback_query(keyboard.Callback.filter(F.type.startswith('appointl_')))
async def appointl_(query: CallbackQuery, state: FSMContext):
    code = ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(8)])
    msg = await query.bot.send_message(
        chat_id=query.from_user.id, reply_markup=keyboard.appointleadercheck(),
        text=f'Заполните <a href="{FORMURL}">форму</a>\nПроверочный код: <code>{code}</code>',)
    await state.update_data(msg=msg, code=code, fraction=int(query.data.split(':')[-1].split('_')[-1]))


@router.callback_query(keyboard.Callback.filter(F.type == 'appointleadercheck'))
async def appointleadercheck(query: CallbackQuery, state: FSMContext):
    await query.bot.send_chat_action(chat_id=query.from_user.id, action="typing")
    sdata = sheets.getappointformbycode(FORMSSHEET, (await state.get_data())['code'],
                                        (await state.get_data())['nickname'])
    if sdata is None:
        msg = await query.bot.send_message(
            chat_id=query.from_user.id, reply_markup=keyboard.appointcheck(),
            text=f'⚠️ Форма не найдена.\nЗаполните <a href="{FORMURL}">форму</a>.\nПроверочный код: '
                 f'<code>{(await state.get_data())["code"]}</code>')
        await state.update_data(msg=msg)
        return

    user: Users = Users.get_or_create(telegram_id=int(sdata[7]), defaults={
        'nickname': sdata[0], 'role': None, 'fraction': FRACTIONS[(await state.get_data())['fraction']],
        'appointed': int(time.time()), 'promoted': None, 'objective_completed': 0, 'apa': 0, 'rebuke': 0, 'warn': 0,
        'verbal': 0, 'inactivestart': None, 'inactiveend': None, 'name': sdata[1], 'age': int(sdata[2]),
        'city': sdata[3], 'discord_id': int(sdata[4]), 'forum': sdata[6], 'vk': sdata[5]})
    if user[1]:
        user = user[0]
        user.nickname = sdata[0]
        user.role = user.promoted = user.inactivestart = user.inactiveend = None
        user.fraction = FRACTIONS[(await state.get_data())['fraction']]
        user.appointed = int(time.time())
        user.objective_completed = user.apa = user.rebuke = user.warn = user.verbal = 0
        user.name = sdata[1]
        user.age = int(sdata[2])
        user.city = sdata[3]
        user.discord_id = int(sdata[4])
        user.forum = sdata[6]
        user.vk = sdata[5]
        user.save()
    else:
        msg = await query.bot.send_message(
            chat_id=query.from_user.id,
            text=f'❌ Пользователь с таким Telegram ID уже существует.')
        await state.clear()
        await state.update_data(msg=msg)
        return
    msg = await query.bot.send_message(
        chat_id=query.from_user.id,
        text=f'✅ Вы успешно назначили нового лидера фракции "<code>{user.fraction}</code>" - '
             f'<a href="tg://user?id={user.telegram_id}">{user.nickname}</a>')
    await state.clear()
    await state.update_data(msg=msg)
    sheets.main(composition=True)


@router.message(Command('addadm'), F.chat.type == "private")
@router.callback_query(keyboard.Callback.filter(F.type == 'appoint_a'))
async def appoint_a(query: CallbackQuery, state: FSMContext):
    user = Users.get_or_none(Users.telegram_id == query.from_user.id)
    if not user or user.role not in (
            'Куратор администрации', 'Главный администратор', 'Основной ЗГА', 'Заместитель ГА'):
        return
    msg = await query.bot.send_message(chat_id=query.from_user.id, text=f'Введите никнейм:',)
    await state.set_state(states.Appoint.a.state)
    await state.update_data(msg=msg)


@router.message(states.Appoint.a)
async def appointa(message: Message, state: FSMContext):
    await message.delete()
    if '_' not in message.text or ' ' in message.text:
        msg = await message.bot.send_message(chat_id=message.from_user.id,
                                             text='⚠️ Неверный никнейм.\nВведите никнейм:')
        await state.update_data(msg=msg)
        return
    msg = await message.bot.send_message(
        chat_id=message.from_user.id, reply_markup=keyboard.appointa(ROLES.index(i) for i in ROLES),
        text='Выберите одну из должностей:',)
    await state.clear()
    await state.update_data(msg=msg, nickname=message.text.strip())


@router.callback_query(keyboard.Callback.filter(F.type.startswith('appoint_a_')))
async def appoint_a_(query: CallbackQuery, state: FSMContext):
    code = ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(8)])
    msg = await query.bot.send_message(chat_id=query.from_user.id, reply_markup=keyboard.appoint_acheck(),
                                       text=f'Заполните <a href="{FORMURL}">форму</a>.\n'
                                            f'Проверочный код: <code>{code}</code>',)
    await state.update_data(msg=msg, code=code, role=int(query.data.split(':')[-1].split('_')[-1]))


@router.callback_query(keyboard.Callback.filter(F.type == 'appoint_acheck'))
async def appoint_acheck(query: CallbackQuery, state: FSMContext):
    await query.bot.send_chat_action(chat_id=query.from_user.id, action="typing")
    sdata = sheets.getappointformbycode(FORMSSHEET, (await state.get_data())['code'],
                                        (await state.get_data())['nickname'])
    if sdata is None:
        msg = await query.bot.send_message(
            chat_id=query.from_user.id, reply_markup=keyboard.appointcheck(),
            text=f'⚠️ Форма не найдена.\nЗаполните <a href="{FORMURL}">форму</a>.\nПроверочный код: '
                 f'<code>{(await state.get_data())["code"]}</code>')
        await state.update_data(msg=msg)
        return
    user = Users.get_or_create(telegram_id=int(sdata[7]), defaults={
        'nickname': sdata[0], 'role': ROLES[(await state.get_data())['role']], 'fraction': None,
        'appointed': int(time.time()), 'promoted': None, 'objective_completed': 0, 'apa': 0, 'rebuke': 0, 'warn': 0,
        'verbal': 0, 'inactivestart': None, 'inactiveend': None, 'name': sdata[1], 'age': int(sdata[2]),
        'city': sdata[3], 'discord_id': int(sdata[4]), 'forum': sdata[6], 'vk': sdata[5]})
    if user[1]:
        user = user[0]
        user.nickname = sdata[0]
        user.role = ROLES[(await state.get_data())['role']]
        user.fraction = user.promoted = user.inactivestart = user.inactiveend = None
        user.appointed = int(time.time())
        user.objective_completed = user.apa = user.rebuke = user.warn = user.verbal = 0
        user.name = sdata[1]
        user.age = int(sdata[2])
        user.city = sdata[3]
        user.discord_id = int(sdata[4])
        user.forum = sdata[6]
        user.vk = sdata[5]
        user.save()
    else:
        msg = await query.bot.send_message(
            chat_id=query.from_user.id,
            text=f'❌ Пользователь с таким Telegram ID уже существует.')
        await state.clear()
        await state.update_data(msg=msg)
        return
    msg = await query.bot.send_message(
        chat_id=query.from_user.id,
        text=f'✅ Вы успешно назначили нового пользователя на должность "<code>{user.role}</code>" - '
             f'<a href="tg://user?id={user.telegram_id}">{user.nickname}</a>')
    await state.clear()
    await state.update_data(msg=msg)
    sheets.main(composition=True)


@router.callback_query(keyboard.Callback.filter(F.type == 'updateinfo'))
async def updateinfo(query: CallbackQuery, state: FSMContext):
    code = ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(8)])
    msg = await query.bot.send_message(chat_id=query.from_user.id, reply_markup=keyboard.updateinfo_check(),
                                       text=f'Заполните <a href="{FORMURL}">форму</a>.\n'
                                            f'Проверочный код: <code>{code}</code>')
    await state.clear()
    await state.update_data(msg=msg, code=code)


@router.callback_query(keyboard.Callback.filter(F.type == 'updateinfo_check'))
async def updateinfo_check(query: CallbackQuery, state: FSMContext):
    await query.bot.send_chat_action(chat_id=query.from_user.id, action="typing")
    sdata = sheets.getappointformbycode(FORMSSHEET, (await state.get_data())['code'], None)
    if sdata is None:
        msg = await query.bot.send_message(
            chat_id=query.from_user.id, reply_markup=keyboard.updateinfo_check(),
            text=f'⚠️ Форма не найдена.\nЗаполните <a href="{FORMURL}">форму</a>.\nПроверочный код: '
                 f'<code>{(await state.get_data())["code"]}</code>')
        await state.update_data(msg=msg)
        return
    user: Users = Users.get(Users.telegram_id == int(sdata[7]))
    user.nickname = sdata[0]
    user.name = sdata[1]
    user.age = int(sdata[2])
    user.city = sdata[3]
    user.discord_id = int(sdata[4])
    user.telegram_id = int(sdata[7])
    user.forum = sdata[6]
    user.vk = sdata[5]
    user.save()
    msg = await query.bot.send_message(
        chat_id=query.from_user.id,
        text=f'✅ Вы успешно обновили информацию пользователя '
             f'<a href="tg://user?id={user.telegram_id}">{user.nickname}</a>.')
    await state.clear()
    await state.update_data(msg=msg)
    sheets.main(composition=True)


@router.message(Command('ap_p'), F.chat.type == "private")
@router.callback_query(keyboard.Callback.filter(F.type == 'punishments'))
async def punishments(query: CallbackQuery, state: FSMContext):
    user = Users.get_or_none(Users.telegram_id == query.from_user.id)
    if not user or (user.role not in (
            'Главный АП', 'Главный следящий АП', 'Заместитель ГС АП', 'Главный администратор', 'Основной ЗГА',
            'Заместитель ГА') and not SpecialAccesses.get_or_none(SpecialAccesses.role == 'swatcher',
                                                                  SpecialAccesses.telegram_id == query.from_user.id)):
        return
    msg = await query.bot.send_message(chat_id=query.from_user.id, text='Выберите тип наказания:',
                                       reply_markup=keyboard.punishments())
    await state.clear()
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type.in_(('punishments_v', 'punishments_w', 'punishments_r'))))
async def punishments_(query: CallbackQuery, state: FSMContext):
    msg = await query.bot.send_message(
        chat_id=query.from_user.id,
        text='Введите никнейм агента поддержки, действие("+" чтобы выдать или "-" чтобы снять) и причину. '
             'Пример: "Andrey_Mal + Тест"')
    await state.clear()
    if query.data.split(':')[-1] == 'punishments_v':
        await state.set_state(states.Punishments.v.state)
    elif query.data.split(':')[-1] == 'punishments_w':
        await state.set_state(states.Punishments.w.state)
    elif query.data.split(':')[-1] == 'punishments_r':
        await state.set_state(states.Punishments.r.state)
    else:
        raise TypeError
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type == 'inactives_s'))
async def inactives_s(query: CallbackQuery, state: FSMContext):
    msg = await query.bot.send_message(chat_id=query.from_user.id, text='Управление неактивами:',
                                       reply_markup=keyboard.inactives_s())
    await state.clear()
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type.in_(('setinactive_s', 'removeinactive_s'))))
async def setrminactive_s(query: CallbackQuery, state: FSMContext):
    msg = await query.bot.send_message(
        chat_id=query.from_user.id,
        text='Введите никнейм агента поддержки, дату начала и дату окончания. Пример: "Andrey_Mal 15.12.2024 '
             '20.12.2024"' if query.data.split(':')[-1] == 'setinactive_s' else 'Введите никнейм агента поддержки.')
    await state.clear()
    if query.data.split(':')[-1] == 'setinactive_s':
        await state.set_state(states.UsersInactive.set.state)
    elif query.data.split(':')[-1] == 'removeinactive_s':
        await state.set_state(states.UsersInactive.remove.state)
    else:
        raise TypeError
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type == 'listinactive_s'))
async def listinactive_s(query: CallbackQuery, state: FSMContext):
    sup = (sorted(Users.select().where(Users.role == SUPPORT_ROLES[1], Users.inactiveend.is_null(False),
                                       Users.inactiveend > int(time.time())), key=lambda x: x.appointed) +
           sorted(Users.select().where(Users.role == SUPPORT_ROLES[0], Users.inactiveend.is_null(False),
                                       Users.inactiveend > int(time.time())), key=lambda x: x.appointed))
    text = f'📚 Список агентов поддержки в неактиве - {len(sup)}\n\n'
    for k, i in enumerate(sup):
        i: Users
        text += (f'[{k + 1}]. <a href="tg://user?id={i.telegram_id}">{i.nickname}</a> '
                 f'| <code>{formatts(i.inactivestart)} - {formatts(i.inactiveend)}</code>\n')
    msg = await query.bot.send_message(chat_id=query.from_user.id, text=text)
    await state.clear()
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type == 'settings_s'))
async def settings_s(query: CallbackQuery, state: FSMContext):
    msg = await query.bot.send_message(chat_id=query.from_user.id, text='Настройки АП:',
                                       reply_markup=keyboard.settings_s())
    await state.clear()
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type == 'setinactiveamnt_s'))
async def setinactiveamnt_s(query: CallbackQuery, state: FSMContext):
    msg = await query.bot.send_message(chat_id=query.from_user.id,
                                       text='Введите количество асков, которые будут сниматься за день неактива:')
    await state.clear()
    await state.set_state(states.Settings.setinactiveamnt_asks.state)
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type == 'settransferamnt'))
async def settransferamnt(query: CallbackQuery, state: FSMContext):
    msg = await query.bot.send_message(chat_id=query.from_user.id, reply_markup=keyboard.settransferamnt(),
                                       text='Настройки перевода:')
    await state.clear()
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type.in_(('settransferdays', 'settransferasks'))))
async def settransferda(query: CallbackQuery, state: FSMContext):
    msg = await query.bot.send_message(
        chat_id=query.from_user.id,
        text='Введите минимальный срок службы для перевода в администрацию:'
        if query.data.split(':')[-1] == 'settransferdays' else
        'Введите минимальное количество асков для перевода в администрацию:')
    await state.clear()
    if query.data.split(':')[-1] == 'settransferdays':
        await state.set_state(states.Settings.settransferamnt_d.state)
    elif query.data.split(':')[-1] == 'settransferasks':
        await state.set_state(states.Settings.settransferamnt_a.state)
    else:
        raise TypeError
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type == 'leaderslist'))
async def leaderslist(query: CallbackQuery, state: FSMContext):
    leaders = sorted(Users.select().where(Users.role.is_null(True)), key=lambda x: FRACTIONS.index(x.fraction))
    msg = await query.bot.send_message(chat_id=query.from_user.id, reply_markup=keyboard.leaderslist(leaders),
                                       text='Выберите лидера:')
    await state.clear()
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type.startswith('leaderstats_')))
async def leaderstats(query: CallbackQuery, state: FSMContext):
    leader = '_'.join(query.data.split(':')[-1].split('_')[-2:])
    user: Users = Users.get_or_none(Users.nickname == leader)
    if not user:
        msg = await query.bot.send_message(chat_id=query.from_user.id, text='⚠️ Данного пользователя не существует.')
        await state.clear()
        await state.update_data(msg=msg)
        return
    msg = await query.bot.send_message(chat_id=query.from_user.id, reply_markup=keyboard.leaderstats_remove(leader),
                                       text=getuserstats(user))
    await state.clear()
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type.startswith('removeleader_')))
async def removeleader(query: CallbackQuery, state: FSMContext):
    leader: Users = Users.get_or_none(Users.nickname == '_'.join(query.data.split(':')[-1].split('_')[-2:]))
    if not leader:
        msg = await query.bot.send_message(chat_id=query.from_user.id, text='⚠️ Данного пользователя не существует.')
        await state.clear()
        await state.update_data(msg=msg)
        return
    msg = await query.bot.send_message(chat_id=query.from_user.id, text='Введите причину снятия:')
    await state.clear()
    await state.set_state(states.RemoveLeader.reason.state)
    await state.update_data(msg=msg, leader=leader.nickname)


@router.message(states.RemoveLeader.reason)
async def removeleader(message: Message, state: FSMContext):
    await message.delete()
    leader = (await state.get_data())['leader']
    if not leader:
        msg = await message.bot.send_message(chat_id=message.from_user.id,
                                             text='⚠️ Данного пользователя не существует.')
        await state.clear()
        await state.update_data(msg=msg)
        return
    user: Users = Users.get_or_none(Users.nickname == leader)
    Removed.create(nickname=user.nickname, role=user.role, appointed=user.appointed, name=user.name,
                   age=user.age, city=user.city, discord_id=user.discord_id, telegram_id=user.telegram_id,
                   reason=message.text, forum=user.forum, vk=user.vk,
                   whoremoved=Users.get(Users.telegram_id == message.from_user.id).nickname,
                   date=formatts(time.time()), fraction=user.fraction, struct='l').save()
    user.delete_instance()
    Inactives.delete().where(Inactives.nickname == leader).execute()
    msg = await message.bot.send_message(chat_id=message.from_user.id, text='✅ Вы успешно сняли лидера с должности.')
    try:
        admin = Users.get(Users.telegram_id == message.from_user.id)
        await message.bot.send_message(
            chat_id=user.telegram_id,
            text=f'📕 Администратор <a href="tg://user?id={admin.telegram_id}">{admin.nickname}</a> снял вас с '
                 f'должности.')
    except:
        pass
    await state.clear()
    await state.update_data(msg=msg)
    sheets.main(composition=True, inactives=True, removed=True)


@router.callback_query(keyboard.Callback.filter(F.type == 'inactives_l'))
async def inactives_l(query: CallbackQuery, state: FSMContext):
    msg = await query.bot.send_message(chat_id=query.from_user.id, text='Управление неактивами:',
                                       reply_markup=keyboard.inactives_l())
    await state.clear()
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type.in_(('setinactive_l', 'removeinactive_l'))))
async def setrminactive_l(query: CallbackQuery, state: FSMContext):
    msg = await query.bot.send_message(
        chat_id=query.from_user.id,
        text='Введите никнейм лидера, дату начала и дату окончания. Пример: "Andrey_Mal 15.12.2024 '
             '20.12.2024"' if query.data.split(':')[-1] == 'setinactive_l' else 'Введите никнейм лидера.')
    await state.clear()
    if query.data.split(':')[-1] == 'setinactive_l':
        await state.set_state(states.UsersInactive.set.state)
    elif query.data.split(':')[-1] == 'removeinactive_l':
        await state.set_state(states.UsersInactive.remove.state)
    else:
        raise TypeError
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type == 'listinactive_l'))
async def listinactive_l(query: CallbackQuery, state: FSMContext):
    leaders = Users.select().where(Users.fraction.is_null(False), Users.inactiveend.is_null(False),
                                   Users.inactiveend > int(time.time()))
    text = f'📚 Список лидеров в неактиве - {len(leaders)}\n\n'
    for k, i in enumerate(leaders):
        text += (f'[{k + 1}]. <a href="tg://user?id={i.telegram_id}">{i.nickname}</a> | '
                 f'<code>{formatts(i.inactivestart)} - {formatts(i.inactiveend)}</code>\n')
    msg = await query.bot.send_message(chat_id=query.from_user.id, text=text)
    await state.clear()
    await state.update_data(msg=msg)


@router.message(Command('ball'), F.chat.type == "private")
@router.callback_query(keyboard.Callback.filter(F.type == 'points'))
async def points(query: CallbackQuery, state: FSMContext):
    user = Users.get_or_none(Users.telegram_id == query.from_user.id)
    if not user or user.role not in (
            'Главный за лидерами', 'Главный следящий ГОСС', 'Главный следящий ОПГ', 'Заместитель ГС ГОСС',
            'Заместитель ГС ОПГ', 'Главный администратор', 'Основной ЗГА', 'Заместитель ГА'):
        return
    msg = await query.bot.send_message(
        chat_id=query.from_user.id,
        text='Введите никнейм лидера(-ов, через запятую или пробел), действие("+" или "-") и количество баллов. '
             'Пример: "Andrey_Mal +300"')
    await state.clear()
    await state.set_state(states.APA.change.state)
    await state.update_data(msg=msg)


@router.message(Command('ask'), F.chat.type == "private")
@router.callback_query(keyboard.Callback.filter(F.type == 'asks'))
async def asks(query: CallbackQuery, state: FSMContext):
    user = Users.get_or_none(Users.telegram_id == query.from_user.id)
    if not user or (user.role not in (
            'Главный АП', 'Главный следящий АП', 'Заместитель ГС АП', 'Главный администратор', 'Основной ЗГА',
            'Заместитель ГА') and not SpecialAccesses.get_or_none(SpecialAccesses.role == 'swatcher',
                                                                  SpecialAccesses.telegram_id == query.from_user.id)):
        return
    msg = await query.bot.send_message(
        chat_id=query.from_user.id,
        text='Введите никнейм агента(-ов, через запятую или пробел) поддержки, '
             'действие("+" или "-") и количество асков. Пример: "Andrey_Mal +300"')
    await state.clear()
    await state.set_state(states.APA.change.state)
    await state.update_data(msg=msg)


@router.message(Command('adm_p'), F.chat.type == "private")
@router.callback_query(keyboard.Callback.filter(F.type == 'punishments_a'))
async def punishments_a(query: CallbackQuery, state: FSMContext):
    user = Users.get_or_none(Users.telegram_id == query.from_user.id)
    if not user or user.role not in (
            'Куратор администрации', 'Главный администратор', 'Основной ЗГА', 'Заместитель ГА'):
        return
    msg = await query.bot.send_message(chat_id=query.from_user.id, text='Выберите тип наказания:',
                                       reply_markup=keyboard.punishments_a())
    await state.clear()
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type.in_(('punishments_a_v', 'punishments_a_w', 'punishments_a_r'))))
async def punishments_a_(query: CallbackQuery, state: FSMContext):
    msg = await query.bot.send_message(
        chat_id=query.from_user.id,
        text='Введите никнейм администратора, действие("+" чтобы выдать или "-" чтобы снять) и причину. '
             'Пример: "Andrey_Mal + Тест"')
    await state.clear()
    if query.data.split(':')[-1] == 'punishments_a_v':
        await state.set_state(states.Punishments.v.state)
    elif query.data.split(':')[-1] == 'punishments_a_w':
        await state.set_state(states.Punishments.w.state)
    elif query.data.split(':')[-1] == 'punishments_a_r':
        await state.set_state(states.Punishments.r.state)
    else:
        raise TypeError
    await state.update_data(msg=msg)


@router.message(Command('ld_p'), F.chat.type == "private")
@router.callback_query(keyboard.Callback.filter(F.type == 'punishments_l'))
async def punishments_l(query: CallbackQuery, state: FSMContext):
    user = Users.get_or_none(Users.telegram_id == query.from_user.id)
    if not user or user.role not in (
            'Главный за лидерами', 'Главный следящий ГОСС', 'Главный следящий ОПГ', 'Заместитель ГС ГОСС',
            'Заместитель ГС ОПГ', 'Главный администратор', 'Основной ЗГА', 'Заместитель ГА'):
        return
    msg = await query.bot.send_message(chat_id=query.from_user.id, text='Выберите тип наказания:',
                                       reply_markup=keyboard.punishments_l())
    await state.clear()
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type.in_(('punishments_l_v', 'punishments_l_w', 'punishments_l_r'))))
async def punishments_l_(query: CallbackQuery, state: FSMContext):
    msg = await query.bot.send_message(
        chat_id=query.from_user.id,
        text='Введите никнейм администратора, действие("+" чтобы выдать или "-" чтобы снять) и причину. '
             'Пример: "Andrey_Mal + Тест"')
    await state.clear()
    if query.data.split(':')[-1] == 'punishments_l_v':
        await state.set_state(states.Punishments.v.state)
    elif query.data.split(':')[-1] == 'punishments_l_w':
        await state.set_state(states.Punishments.w.state)
    elif query.data.split(':')[-1] == 'punishments_l_r':
        await state.set_state(states.Punishments.r.state)
    else:
        raise TypeError
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type == 'settings_l'))
async def settings_l(query: CallbackQuery, state: FSMContext):
    msg = await query.bot.send_message(chat_id=query.from_user.id, text='Настройки фракций:',
                                       reply_markup=keyboard.settings_l())
    await state.clear()
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type == 'setinactiveamnt_l'))
async def setinactiveamnt_l(query: CallbackQuery, state: FSMContext):
    msg = await query.bot.send_message(chat_id=query.from_user.id,
                                       text='Введите количество баллов, которые будут сниматься за день неактива:')
    await state.clear()
    await state.set_state(states.Settings.setinactiveamnt_points.state)
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type == 'administration'))
async def administration(query: CallbackQuery, state: FSMContext):
    msg = await query.bot.send_message(chat_id=query.from_user.id, reply_markup=keyboard.administration(),
                                       text='Управление администрацией:')
    await state.clear()
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type.contains('administration_list_')))
async def administration_list(query: CallbackQuery, state: FSMContext):
    page = int(query.data.split(':')[-1].split('_')[2])
    admins = sorted(Users.select().where(Users.role << ROLES), key=lambda x: ROLES.index(x.role))
    text = (f'📚 Список администраторов - {len(admins)} {pointWords(len(admins), ("человек", "человека", "человек"))}.'
            f'\n\n')
    for k, i in enumerate(admins[page * 15: (page + 1) * 15]):
        text += (f'[{(15 * page) + k + 1}]. <a href="tg://user?id={i.telegram_id}">{i.nickname}</a> |'
                 f' <a href="{i.vk}">VK</a> | '
                 f'{i.telegram_id} | <a href="{i.forum}">FA</a> | '
                 f'<code>{i.role}</code>\n')
    msg = await query.bot.send_message(chat_id=query.from_user.id, text=text,
                                       reply_markup=keyboard.administration_list(page, len(admins)))
    await state.clear()
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type == 'promote'))
async def promote(query: CallbackQuery, state: FSMContext):
    msg = await query.bot.send_message(chat_id=query.from_user.id, text='Введите никнейм администратора:',)
    await state.clear()
    await state.set_state(states.Promote.promote.state)
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type == 'inactives_a'))
async def inactives_a(query: CallbackQuery, state: FSMContext):
    msg = await query.bot.send_message(chat_id=query.from_user.id, text='Управление неактивами:',
                                       reply_markup=keyboard.inactives_a())
    await state.clear()
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type.in_(('setinactive_a', 'removeinactive_a'))))
async def setrminactive_a(query: CallbackQuery, state: FSMContext):
    msg = await query.bot.send_message(
        chat_id=query.from_user.id,
        text='Введите никнейм администратора, дату начала и дату окончания. Пример: "Andrey_Mal 15.12.2024 '
             '20.12.2024"' if query.data.split(':')[-1] == 'setinactive_a' else 'Введите никнейм администратора.')
    await state.clear()
    if query.data.split(':')[-1] == 'setinactive_a':
        await state.set_state(states.UsersInactive.set.state)
    elif query.data.split(':')[-1] == 'removeinactive_a':
        await state.set_state(states.UsersInactive.remove.state)
    else:
        raise TypeError
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type == 'listinactive_a'))
async def listinactive_a(query: CallbackQuery, state: FSMContext):
    admins = sorted(Users.select().where(Users.role << ROLES, Users.inactiveend.is_null(False),
                                         Users.inactiveend > int(time.time())), key=lambda x: ROLES.index(x.role))
    text = f'📚 Список администраторов в неактиве - {len(admins)}\n\n'
    for k, i in enumerate(admins):
        text += (f'[{k + 1}]. <a href="tg://user?id={i.telegram_id}">{i.nickname}</a> |'
                 f' <code>{formatts(i.inactivestart)} - {formatts(i.inactiveend)}</code>\n')
    msg = await query.bot.send_message(chat_id=query.from_user.id, text=text)
    await state.clear()
    await state.update_data(msg=msg)


@router.message(Command('rep'), F.chat.type == "private")
@router.callback_query(keyboard.Callback.filter(F.type == 'answers'))
async def answers(query: CallbackQuery, state: FSMContext):
    user = Users.get_or_none(Users.telegram_id == query.from_user.id)
    if not user or user.role not in (
            'Куратор администрации', 'Главный администратор', 'Основной ЗГА', 'Заместитель ГА'):
        return
    msg = await query.bot.send_message(
        chat_id=query.from_user.id,
        text='Введите никнейм администратора(-ов, через запятую или пробел), действие("+" или "-") и количество '
             'ответов. Пример: "Andrey_Mal +300"')
    await state.clear()
    await state.set_state(states.APA.change.state)
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type == 'structurescontrol'))
async def structurescontrol(query: CallbackQuery, state: FSMContext):
    msg = await query.bot.send_message(chat_id=query.from_user.id, reply_markup=keyboard.structurescontrol(),
                                       text='Управление структурами')
    await state.clear()
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type == 'strctrstats'))
async def strctrstats(query: CallbackQuery, state: FSMContext):
    users = Users.select()
    fractions = list(FRACTIONS)
    admins, sup, leaders = 0, 0, 0
    for i in users:
        if i.fraction is not None:
            leaders += 1
            fractions.remove(i.fraction)
        elif i.role in SUPPORT_ROLES:
            sup += 1
        else:
            admins += 1
    text = f'''❇️ Администраторов: <code>{admins}</code>
📚 Агентов Поддержки: <code>{sup}</code>
⚙️ Лидеров: <code>{leaders}</code>
'''
    if len(fractions) > 0:
        text += (f'\n\n⚠️ Не хватает лидеров для следующих фракций: <code>' + '</code>, <code>'.join(fractions) +
                 '</code>')
    msg = await query.bot.send_message(chat_id=query.from_user.id, text=text)
    await state.clear()
    await state.update_data(msg=msg)


@router.message(Command('sc'), F.chat.type == "private")
@router.callback_query(keyboard.Callback.filter(F.type == 'servercontrol'))
async def servercontrol(query: CallbackQuery, state: FSMContext):
    user = Users.get_or_none(Users.telegram_id == query.from_user.id)
    if not user or user.role not in (
            'Главный администратор', 'Основной ЗГА', 'Заместитель ГА'):
        return
    msg = await query.bot.send_message(chat_id=query.from_user.id, reply_markup=keyboard.servercontrol(),
                                       text='Управление сервером')
    await state.clear()
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type == 'serversettings'))
async def serversettings(query: CallbackQuery, state: FSMContext):
    msg = await query.bot.send_message(chat_id=query.from_user.id, reply_markup=keyboard.serversettings(),
                                       text='Настройки')
    await state.clear()
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type == 'serveradmins'))
async def serveradmins(query: CallbackQuery, state: FSMContext):
    msg = await query.bot.send_message(chat_id=query.from_user.id, reply_markup=keyboard.serveradmins(),
                                       text='Настройка администрации:')
    await state.clear()
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type == 'serversheets'))
async def serversheets(query: CallbackQuery, state: FSMContext):
    msg = await query.bot.send_message(chat_id=query.from_user.id, reply_markup=keyboard.serversheets(),
                                       text='Настройка таблиц:')
    await state.clear()
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type.startswith('serversheets_')))
async def serversheets_(query: CallbackQuery, state: FSMContext):
    msg = await query.bot.send_message(chat_id=query.from_user.id, text='Введите ID Google таблицы:')
    await state.clear()
    if query.data.split(':')[-1].endswith('support'):
        await state.set_state(states.ServerSheets.s)
    elif query.data.split(':')[-1].endswith('leaders'):
        await state.set_state(states.ServerSheets.l)
    elif query.data.split(':')[-1].endswith('admins'):
        await state.set_state(states.ServerSheets.a)
    else:
        raise ValueError
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type == 'setinactiveamnt_a'))
async def setinactiveamnt_a(query: CallbackQuery, state: FSMContext):
    msg = await query.bot.send_message(chat_id=query.from_user.id,
                                       text='Введите количество ответов, которые будут сниматься за день неактива:')
    await state.clear()
    await state.set_state(states.Settings.setinactiveamnt_answers.state)
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type == 'serverchats'))
async def serverchats(query: CallbackQuery, state: FSMContext):
    msg = await query.bot.send_message(chat_id=query.from_user.id, reply_markup=keyboard.serverchats(),
                                       text='Беседы')
    await state.clear()
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type == 'serverchats_objective'))
async def serverchats_objective(query: CallbackQuery, state: FSMContext):
    msg = await query.bot.send_message(chat_id=query.from_user.id, reply_markup=keyboard.serverchats_objective(),
                                       text='Норматив')
    await state.clear()
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type == 'objective_admins'))
async def objective_admins(query: CallbackQuery, state: FSMContext):
    msg = await query.bot.send_message(chat_id=query.from_user.id, text='Введите ID канала/темы(через "/"):')
    await state.clear()
    await state.set_state(states.ServerChats.objective_admins.state)
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type == 'serverchats_additionalreplies'))
async def serverchats_additionalreplies(query: CallbackQuery, state: FSMContext):
    msg = await query.bot.send_message(chat_id=query.from_user.id, text='Доп. ответы',
                                       reply_markup=keyboard.serverchats_additionalreplies())
    await state.clear()
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type == 'additionalreplies_admins'))
async def additionalreplies_admins(query: CallbackQuery, state: FSMContext):
    msg = await query.bot.send_message(chat_id=query.from_user.id, text='Введите ID канала/темы(через "/"):')
    await state.clear()
    await state.set_state(states.ServerChats.additionalreplies.state)
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type == 'serverchats_inactive'))
async def serverchats_inactive(query: CallbackQuery, state: FSMContext):
    msg = await query.bot.send_message(chat_id=query.from_user.id, text='Неактивы',
                                       reply_markup=keyboard.serverchats_inactive())
    await state.clear()
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type == 'inactive_support'))
async def inactive_support(query: CallbackQuery, state: FSMContext):
    msg = await query.bot.send_message(chat_id=query.from_user.id, text='Введите ID канала/темы(через "/"):')
    await state.clear()
    await state.set_state(states.ServerChats.inactive_support.state)
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type == 'inactive_leaders'))
async def inactive_leaders(query: CallbackQuery, state: FSMContext):
    msg = await query.bot.send_message(chat_id=query.from_user.id, text='Введите ID канала/темы(через "/"):')
    await state.clear()
    await state.set_state(states.ServerChats.inactive_leaders.state)
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type == 'inactive_admins'))
async def inactive_admins(query: CallbackQuery, state: FSMContext):
    msg = await query.bot.send_message(chat_id=query.from_user.id, text='Введите ID канала/темы(через "/"):')
    await state.clear()
    await state.set_state(states.ServerChats.inactive_admins.state)
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type == 'serverchats_forms'))
async def serverchats_forms(query: CallbackQuery, state: FSMContext):
    msg = await query.bot.send_message(chat_id=query.from_user.id, text='Введите ID канала/темы(через "/"):')
    await state.clear()
    await state.set_state(states.ServerChats.forms.state)
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type == 'formproof_y'))
async def formproof_y(query: CallbackQuery, state: FSMContext):
    msg = await query.bot.send_message(chat_id=query.from_user.id,
                                       text='Отправьте ссылку(-и, через запятую или пробел) на доказательства:')
    await state.set_state(states.Forms.proof.state)
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type == 'formproof_send'))
async def formproof_send(query: CallbackQuery, state: FSMContext):
    user: Users = Users.get(Users.telegram_id == query.from_user.id)
    form: str = (await state.get_data())['form']
    form: Forms = Forms.create(form=form, fromtgid=user.telegram_id)
    text = f'''
[📗 #{str(form.get_id()).zfill(4)}] Новая форма от <a href="tg://user?id={user.telegram_id}">{user.nickname}</a>\n
<code>{form.form}</code>
'''
    chat: Chats = Chats.get(Chats.setting == 'forms')
    await query.bot.send_message(chat_id=int(f'-100{chat.chat_id}'), message_thread_id=chat.thread_id, text=text,
                                 reply_markup=keyboard.form(form.get_id()))
    msg = await query.bot.send_message(chat_id=query.from_user.id,
                                       text=f'✅ Форма №{str(form.get_id()).zfill(4)} отправлена.')
    await state.clear()
    await state.update_data(msg=msg)


@router.callback_query(keyboard.Callback.filter(F.type.startswith('form_')))
async def form_(query: CallbackQuery):
    text = query.message.html_text
    form: Forms = Forms.get_by_id(int(query.data.split(':')[-1].split('_')[-1]))
    admin: Users = Users.get(Users.telegram_id == query.from_user.id)
    if '🔎' in text:
        text = text[:text.find('🔎') - 3]
    text += f'''\n
❓ Статус: <b>{"Отказано" if 'disapprove' in query.data.split(':')[-1] else "Одобрено"}</b>
👤 Ответственный: <a href="tg://user?id={admin.telegram_id}">{admin.nickname}</a>''' + (
        f'\n🔎 Доказательства: {", ".join(ast.literal_eval(form.proofs))}' if form.proofs else '') + f'''
🕒 Дата обработки: <code>{formatts(time.time())}</code>'''
    await query.message.edit_text(text)
    try:
        await query.bot.send_message(
            chat_id=form.fromtgid,
            text=f'❌ Форма №{str(form.get_id()).zfill(4)} была отказана администратором '
                 f'<a href="tg://user?id={admin.telegram_id}">{admin.nickname}</a>.'
            if 'disapprove' in query.data.split(':')[-1] else
            f'✅ Форма №{str(form.get_id()).zfill(4)} была одобрена администратором '
            f'<a href="tg://user?id={admin.telegram_id}">{admin.nickname}</a>.')
    except:
        pass


@router.callback_query(keyboard.Callback.filter(F.type.startswith('inactiverequest_')))
async def inactiverequest_(query: CallbackQuery):
    text = query.message.html_text
    try:
        ir: InactiveRequests = InactiveRequests.get_by_id(int(query.data.split('_')[-1]))
    except:
        await query.bot.answer_callback_query(query.id, text='⚠️ Данное заявление уже было обработано.')
        return
    user: Users = Users.get(Users.telegram_id == ir.tgid)
    admin: Users = Users.get(Users.telegram_id == query.from_user.id)
    if 'disapprove' in query.data.split(':')[-1]:
        text += f'\n\n🔴 Заявление было отказано — <a href="tg://user?id={admin.telegram_id}">{admin.nickname}</a>'
        Inactives.create(nickname=user.nickname, role=user.role, start=ir.start, end=ir.end, status='Отказан',
                         reason=ir.reason, fraction=user.fraction)
        markup = None
    else:
        text += f'\n\n🟢 Заявление было одобрено — <a href="tg://user?id={admin.telegram_id}">{admin.nickname}</a>'
        Inactives.create(nickname=user.nickname, role=user.role, start=ir.start, end=ir.end, status='Одобрен',
                         reason=ir.reason, fraction=user.fraction)
        user.inactivestart = formatedtotts(ir.start)
        user.inactiveend = formatedtotts(ir.end)
        user.save()
        if user.fraction:
            apa = 'баллы'
        elif user.role in SUPPORT_ROLES:
            apa = 'аски'
        else:
            apa = 'ответы'
        markup = keyboard.inactiveapa(user.telegram_id, apa)
    ir.delete_instance()
    await query.message.edit_text(text, reply_markup=markup)
    try:
        await query.bot.send_message(
            chat_id=ir.tgid,
            text=f'❌ <a href="tg://user?id={admin.telegram_id}">{admin.nickname}</a> отказал вам в неактиве '
                 f'№{str(ir.get_id()).zfill(4)}.' if 'disapprove' in query.data.split(':')[-1] else
            f'✅ <a href="tg://user?id={admin.telegram_id}">{admin.nickname}</a> одобрил вам неактив '
            f'№{str(ir.get_id()).zfill(4)}.')
    except:
        pass
    sheets.main(composition=True, inactives=True)


@router.callback_query(keyboard.Callback.filter(F.type.startswith('inactiveapa_')))
async def inactiveapa_(query: CallbackQuery):
    text = query.message.html_text
    data = query.message.text.strip().split()
    admin: Users = Users.get(Users.telegram_id == query.from_user.id)
    user: Users = Users.get(Users.telegram_id == int(query.data.split(':')[-1].split('_')[-1]))
    w = f'{data[data.index("Количество") + 2]} {data[data.index("Количество") + 1][:-1]}'
    user.apa -= int(w.split()[0])
    user.save()
    text += f'\n🟢 Снято <code>{w}</code>'
    await query.message.edit_text(text)
    try:
        await query.bot.send_message(chat_id=user.telegram_id,
                                     text=f'📕 Администратор <a href="tg://user?id='
                                          f'{admin.telegram_id}">{admin.nickname}</a> снял вам <code>{w}</code>.')
    except:
        pass
    sheets.main(composition=True)


@router.callback_query(keyboard.Callback.filter(F.type.startswith('additionalreply_')))
async def additionalreply_(query: CallbackQuery, state: FSMContext):
    text = query.message.html_text
    admin: Users = Users.get(Users.telegram_id == query.from_user.id)
    if 'disapprove' in query.data.split(':')[-1]:
        text += f'\n\n🔴 Заявление было отказано — <a href="tg://user?id={admin.telegram_id}">{admin.nickname}</a>'
        try:
            await query.bot.send_message(chat_id=int(query.data.split(':')[-1].split('_')[-1]),
                                         text=f'❌ <a href="tg://user?id={admin.telegram_id}">'
                                              f'{admin.nickname}</a> отказал вам в дополнительных ответах.')
        except:
            pass
        return await query.message.edit_text(text)
    await state.set_state(states.Reports.sendadditionalreplyw.state)
    msg = await query.bot.send_message(chat_id=query.message.chat.id, message_thread_id=query.message.message_thread_id,
                                       text='❓ Введите количество выдаваемых ответов:')
    await state.update_data(msg=msg, edit=query.message, user=int(query.data.split(':')[-1].split('_')[-1]))


@router.callback_query(keyboard.Callback.filter(F.type.startswith('reportssendobjective_')))
async def reportssendobjective_(query: CallbackQuery, state: FSMContext):
    text = query.message.html_text
    admin: Users = Users.get(Users.telegram_id == query.from_user.id)
    if 'disapprove' in query.data.split(':')[-1]:
        text += f'\n\n🔴 Заявление было отказано — <a href="tg://user?id={admin.telegram_id}">{admin.nickname}</a>'
        try:
            await query.bot.send_message(chat_id=int(query.data.split(':')[-1].split('_')[-1]),
                                         text=f'❌ <a href="tg://user?id={admin.telegram_id}">'
                                              f'{admin.nickname}</a> отказал вашу заявку на норматив.')
        except:
            pass
        return await query.message.edit_caption(caption=text)
    elif 'approve' in query.data.split(':')[-1]:
        await state.set_state(states.Reports.sendobjectivewa.state)
    else:
        await state.set_state(states.Reports.sendobjectivew.state)
    msg = await query.bot.send_message(chat_id=query.message.chat.id, message_thread_id=query.message.message_thread_id,
                                       text='❓ Введите количество выдаваемых ответов:')
    await state.update_data(msg=msg, edit=query.message, user=int(query.data.split(':')[-1].split('_')[-1]))


@router.callback_query(keyboard.Callback.filter(F.type == 'usersinactiveset_y'))
async def usersinactiveset_y(query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user = Users.get_by_id(data['uid'])
    user.apa -= data["w"]
    user.save()
    admin = Users.get(Users.telegram_id == query.from_user.id)
    msg = await query.bot.send_message(
        chat_id=query.from_user.id,
        text=f'✅ Вы успешно сняли <code>{data["p"]}</code> <code>{data["user"]}</code>.')
    try:
        await query.bot.send_message(
            chat_id=user.telegram_id,
            text=f'📕 Администратор <a href="tg://user?id={admin.telegram_id}">{admin.nickname}</a>'
                 f' снял вам <code>{data["p"]}</code>, '
                 f'теперь у вас <code>{user.apa} {data["p"].split()[-1]}</code>.')
    except:
        pass
    await state.clear()
    await state.update_data(msg=msg)
    sheets.main(composition=True)


@router.callback_query(keyboard.Callback.filter(F.type.startswith('promote_')))
async def promote_(query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user = Users.get_or_none(Users.telegram_id == data['uid'])
    if user is None or not checkrole(Users.get_or_none(Users.telegram_id == query.from_user.id), user):
        msg = await query.bot.send_message(chat_id=query.from_user.id,
                                           text=f'⚠️ Вы не можете повысить данного пользователя.')
        await state.clear()
        await state.update_data(msg=msg)
        return
    user.role = ROLES[int(query.data.split(':')[-1].split('_')[-1])]
    user.promoted = int(time.time())
    user.save()
    msg = await query.bot.send_message(
        chat_id=query.from_user.id, reply_markup=keyboard.promote_days(),
        text=f'✅ Вы успешно установили должность "<code>{user.role}</code>" '
             f'администратору <a href="tg://user?id={user.telegram_id}">{user.nickname}</a>. Аннулировать дни нормы?')
    try:
        admin = Users.get(Users.telegram_id == query.from_user.id)
        await query.bot.send_message(
            chat_id=user.telegram_id,
            text=f'📗 Администратор <a href="tg://user?id={admin.telegram_id}">{admin.nickname}'
                 f'</a> повысил вас до должности "<code>{user.role}</code>".')
    except:
        pass
    await state.clear()
    await state.update_data(msg=msg, user=user)
    sheets.main(composition=True)


@router.callback_query(keyboard.Callback.filter(F.type.startswith('promotedays')))
async def promotedays(query: CallbackQuery, state: FSMContext):
    user = (await state.get_data())['user']
    if query.data.split(':')[-1].endswith('_y'):
        user.objective_completed = 0
        user.save()
    msg = await query.bot.send_message(
        chat_id=query.from_user.id, reply_markup=keyboard.promote_answers(),
        text=f'Аннулировать ответы?')
    await state.clear()
    await state.update_data(msg=msg, user=user)
    sheets.main(composition=True)


@router.callback_query(keyboard.Callback.filter(F.type.startswith('promoteanswers')))
async def promoteanswers(query: CallbackQuery, state: FSMContext):
    user = (await state.get_data())['user']
    if query.data.split(':')[-1].endswith('_y'):
        user.apa = 0
        user.save()
    msg = await query.bot.send_message(
        chat_id=query.from_user.id,
        text=f'✅ Вы успешно повысили администратора <a href="tg://user?id={user.telegram_id}">{user.nickname}</a>.')
    await state.clear()
    await state.update_data(msg=msg)
    sheets.main(composition=True)


@router.message(states.Reports.sendobjectivew)
@router.message(states.Reports.sendobjectivewa)
async def reportssendobjectivew_wa(message: Message, state: FSMContext):
    await message.delete()

    if not message.text or not message.text.strip().isdigit():
        msg = await message.bot.send_message(chat_id=message.chat.id, message_thread_id=message.message_thread_id,
                                             text='⚠️ Введите число.\n❓ Введите количество выдаваемых ответов:')
        await state.update_data(msg=msg)
        return
    user: Users = Users.get(Users.telegram_id == (await state.get_data())['user'])
    user.apa += int(message.text.strip())
    admin: Users = Users.get(Users.telegram_id == message.from_user.id)
    text = (f'✅ <a href="tg://user?id={admin.telegram_id}">{admin.nickname}</a> принял вашу заявку на норматив. '
            f'Начислено <code>{message.text.strip()} ответов')
    if await state.get_state() == states.Reports.sendobjectivewa.state:
        user.objective_completed += 1
        text += ' + 1 день норматива'
    try:
        await message.bot.send_message(chat_id=user.telegram_id, text=text + '</code>.')
    except:
        pass
    user.save()
    edit: Message = (await state.get_data())['edit']
    text = edit.html_text + (f'\n\n🟢 Заявление было одобрено — <a href="tg://user?id={admin.telegram_id}">'
                             f'{admin.nickname}</a>\n🟢 Начислено <code>{message.text.strip()} ответов')
    if await state.get_state() == states.Reports.sendobjectivewa.state:
        text += ' + 1 день норматива'
    await edit.edit_caption(caption=text + '</code>.')
    sheets.main(composition=True)
    await state.clear()


@router.message(states.Reports.sendadditionalreplyw)
async def reportssendadditionalreplyw(message: Message, state: FSMContext):
    await message.delete()

    if not message.text or not message.text.strip().isdigit():
        msg = await message.bot.send_message(chat_id=message.chat.id, message_thread_id=message.message_thread_id,
                                             text='⚠️ Введите число.\n❓ Введите количество выдаваемых ответов:')
        await state.update_data(msg=msg)
        return
    user: Users = Users.get(Users.telegram_id == (await state.get_data())['user'])
    user.apa += int(message.text.strip())
    user.save()
    edit: Message = (await state.get_data())['edit']
    admin: Users = Users.get(Users.telegram_id == message.from_user.id)
    try:
        await message.bot.send_message(chat_id=user.telegram_id,
                                       text=f'✅ <a href="tg://user?id={admin.telegram_id}">'
                                            f'{admin.nickname}</a> одобрил вашу заявку на доп. ответы. '
                                            f'Начислено <code>{message.text.strip()} ответов</code>.')
    except:
        pass
    await edit.edit_text(
        text=edit.html_text + f'\n\n🟢 Заявление было одобрено — <a href="tg://user?id={admin.telegram_id}">'
                              f'{admin.nickname}</a>\n🟢 Начислено <code>{message.text.strip()} ответов</code>.')
    sheets.main(composition=True)
    await state.clear()


@router.message(states.APA.change)
async def apachange(message: Message, state: FSMContext):
    await message.delete()

    admin = Users.get(Users.telegram_id == message.from_user.id)
    if admin.fraction:
        apa = 'баллов'
    elif admin.role in SUPPORT_ROLES:
        apa = 'асков'
    else:
        apa = 'ответов'
    stext, fdata = '', message.text.split('\n')
    for c, text in enumerate(fdata):
        data = [i for i in re.split(r'[, \n]', text.strip()) if i != '']
        splitter = 0
        users = []
        for i in data:
            if i[0] in ('+', '-'):
                splitter = data.index(i)
                break
            users.append(i)
        if len(data) < 2 or not splitter or not data[splitter][1:].isdigit():
            continue
        nicks = set()
        failed = set()
        reason = '' if splitter == (len(data) - 1) else f' по причине: "{",".join(data[splitter + 1:])}"'
        for i in data[:splitter]:
            user = Users.get_or_none(Users.nickname == i.replace(',', ''))
            if user is None or not checkrole(admin, user):
                stext += (f'{f"[{c + 1}]. " if len(fdata) > 1 else ""}⚠️ Пользователя с никнеймом {i.replace(",", "")} '
                          f'не существует.\n\n')
                continue
            if user.nickname in nicks:
                continue
            user.apa += int(data[splitter])
            user.save()
            nicks.add(user.nickname)
            try:
                await message.bot.send_message(
                    chat_id=user.telegram_id,
                    text=f'{"📗" if "+" in data[splitter] else "📕"} <code>{admin.nickname}</code> '
                         f'{"выдал" if "+" in data[splitter] else "снял"} вам <code>{data[splitter]} {apa}</code>, '
                         f'теперь у вас <code>{user.apa} {apa}</code>{reason}.')
            except:
                failed.add(user.nickname)
        if nicks:
            stext += (f'{f"[{c + 1}]. " if len(fdata) > 1 else ""} ✅ Вы успешно '
                      f'{"выдали" if "+" in data[splitter] else "сняли"} <code>{data[splitter]} {apa}</code> '
                      f'<code>{"</code>, <code>".join(nicks)}</code>{reason}.\n')
            if failed:
                stext += f'⚠️ Не удалось отправить уведомление <code>{"</code>, <code>".join(failed)}</code>.\n\n'
            else:
                stext += '\n'
    msg = await message.bot.send_message(chat_id=message.from_user.id, text=stext)

    await state.clear()
    await state.update_data(msg=msg)
    sheets.main(composition=True)


@router.message(StatesGroupHandle(states.ServerChats))
async def serverchats(message: Message, state: FSMContext):
    curr_state = await state.get_state()
    await message.delete()

    data = message.text.strip().split('/')
    if len(data) > 2 or not all(i.isdigit() for i in data):
        msg = await message.bot.send_message(
            chat_id=message.from_user.id,
            text='⚠️ Неверные данные.\nВведите ID канала/темы(через "/"):')
        await state.update_data(msg=msg)
        return
    chid = int(data[0])
    threadid = int(data[1]) if len(data) == 2 else None
    Chats.create(setting=curr_state.replace('ServerChats:', ''), chat_id=chid, thread_id=threadid)
    msg = await message.bot.send_message(
        chat_id=message.from_user.id,
        text=f'✅ Вы успешно установили новый чат для отправки уведомлений класса <code>{curr_state}</code>.')

    await state.clear()
    await state.update_data(msg=msg)


@router.message(StatesGroupHandle(states.Punishments))
async def punishments(message: Message, state: FSMContext):
    curr_state = await state.get_state()
    await message.delete()

    stext, fdata = '', message.text.split('\n')
    for c, ftext in enumerate(fdata):
        action = curr_state[-1]
        data = ftext.strip().split()
        user: Users = Users.get_or_none(Users.nickname == data[0])
        text = '⚠️ Неверные данные.'
        if not user:
            check = False
        elif len(data) > 1:
            if data[1] != '-':
                check = True
            elif data[1] in ('+', '-'):
                text = '⚠️ У пользователя нет наказаний такого типа.'
                if action == 'v':
                    check = user.verbal >= 1
                elif action == 'w':
                    check = user.warn >= 1
                else:
                    check = user.rebuke >= 1
            else:
                check = False
        else:
            check = False
        if not check or not checkrole(Users.get_or_none(Users.telegram_id == message.from_user.id), user):
            stext += (f"[{c + 1}]. " if len(fdata) > 1 else "") + text + '\n\n'
            continue
        if action == 'v':
            user.verbal += int(data[1] + '1')
            action = 'одно устное предупреждение'
        elif action == 'w':
            user.warn += int(data[1] + '1')
            action = 'одно предупреждение'
        else:
            user.rebuke += int(data[1] + '1')
            action = 'один выговор'
        if user.verbal >= 2:
            user.warn += user.verbal // 2
            user.verbal -= (user.verbal // 2) * 2
        if user.warn >= 2:
            user.rebuke += user.warn // 2
            user.warn -= (user.warn // 2) * 2
        user.save()
        reason = (' по причине: "' + ' '.join(data[2:]) + '"') if len(data) > 2 else ''
        try:
            await message.bot.send_message(
                chat_id=user.telegram_id,
                text=f"{'📗' if data[1] == '-' else '📕'} Администратор <code>"
                     f"{Users.get(Users.telegram_id == message.from_user.id).nickname}</code> "
                     f"{'снял' if data[1] == '-' else 'выдал'} вам <code>{action}</code>{reason }.")
        except:
            pass
        stext += (f'{f"[{c + 1}]. " if len(fdata) > 1 else ""}✅ Вы успешно '
                  f'{"сняли" if "-" in data[1] else"выдали"} <code>{action}</code>'
                  f' пользователю <a href="tg://user?id={user.telegram_id}">{user.nickname}</a>.\n\n')
    msg = await message.bot.send_message(chat_id=message.from_user.id, text=stext)
    await state.clear()
    await state.update_data(msg=msg)
    sheets.main(composition=True)


@router.message(StatesGroupHandle(states.Settings))
async def settings(message: Message, state: FSMContext):
    curr_state = await state.get_state()
    await message.delete()

    if curr_state.endswith('points'):
        action = 'количество баллов, которые будут сниматься за день неактива'
        setting, new = Settings_l.get_or_create(setting="inactiveamnt_points", defaults={'val': 0})
    elif curr_state.endswith('asks'):
        action = 'количество асков, которые будут сниматься за день неактива'
        setting, new = Settings_s.get_or_create(setting="inactiveamnt_asks", defaults={'val': 0})
    elif curr_state.endswith('answers'):
        action = 'количество ответов, которые будут сниматься за день неактива'
        setting, new = Settings_a.get_or_create(setting="inactiveamnt_answers", defaults={'val': 0})
    elif curr_state.endswith('_d'):
        action = 'количество дней, требуемых для перевода в администрацию'
        setting, new = Settings_s.get_or_create(setting="transferamnt_d", defaults={'val': 0})
    elif curr_state.endswith('_a'):
        action = 'количество асков, требуемых для перевода в администрацию'
        setting, new = Settings_s.get_or_create(setting="transferamnt_a", defaults={'val': 0})
    else:
        raise ValueError

    if not message.text.strip().isdigit():
        msg = await message.bot.send_message(chat_id=message.from_user.id,
                                             text=f'⚠️ Введите число.\nВведите {action}:')
        await state.update_data(msg=msg)
        if new:
            setting.delete_instance()
        return
    setting.val = int(message.text.strip())
    setting.save()
    msg = await message.bot.send_message(
        chat_id=message.from_user.id,
        text=f'✅ Вы успешно установили новое {action} - <code>{message.text.strip()}</code>.')
    await state.clear()
    await state.update_data(msg=msg)


@router.message(StatesGroupHandle(states.ServerSheets))
async def serversheets(message: Message, state: FSMContext):
    curr_state = await state.get_state()
    await message.delete()

    if curr_state.endswith('s'):
        setting, new = Sheets.get_or_create(setting="s", defaults={'val': '0'})
    elif curr_state.endswith('l'):
        setting, new = Sheets.get_or_create(setting="l", defaults={'val': '0'})
    elif curr_state.endswith('a'):
        setting, new = Sheets.get_or_create(setting="a", defaults={'val': '0'})
    else:
        raise ValueError
    setting.val = message.text.strip()
    setting.save()
    msg = await message.bot.send_message(chat_id=message.from_user.id, text=f'✅ Вы успешно установили новый Google ID.')
    await state.clear()
    await state.update_data(msg=msg)


@router.message(states.UsersInactive.set)
async def usersinactiveset(message: Message, state: FSMContext):
    await message.delete()

    data = message.text.strip().replace(' - ', ' ').split()
    try:
        if len(data) != 3:
            raise ValueError
        user: Users | None = Users.get_or_none(Users.nickname == data[0])
        if user is None:
            raise ValueError
        start = datetime.strptime(data[1], '%d.%m.%Y')
        end = datetime.strptime(data[2], '%d.%m.%Y')
        if start.timestamp() > end.timestamp():
            raise ValueError
    except:
        msg = await message.bot.send_message(
            chat_id=message.from_user.id,
            text='⚠️ Неверные данные или формат.\nВведите никнейм, дату начала и дату окончания. Пример: '
                 '"Andrey_Mal 15.12.2024 20.12.2024"')
        await state.update_data(msg=msg)
        return
    admin: Users = Users.get(Users.telegram_id == message.from_user.id)
    if not checkrole(admin, user):
        msg = await message.bot.send_message(
            chat_id=message.from_user.id,
            text=f'⚠️ Пользователя с никнеймом "{data[0]}" не существует.\n'
                 f'Введите никнейм, дату начала и дату окончания. Пример: "Andrey_Mal 15.12.2024 20.12.2024"')
        await state.update_data(msg=msg)
        return
    if user.role in SUPPORT_ROLES:
        w = Settings_s.get(Settings_s.setting == 'inactiveamnt_asks').val * ceil(
            (end.timestamp() - start.timestamp()) / 86400)
        p = f'{w} {pointWords(w, ("аск", "аска", "асков"))}'
        sla = 'агенту поддержки'
    elif user.fraction:
        w = Settings_l.get(Settings_l.setting == 'inactiveamnt_points').val * ceil(
            (end.timestamp() - start.timestamp()) / 86400)
        p = f'{w} {pointWords(w, ("балл", "балла", "баллов"))}'
        sla = 'лидеру фракции'
    else:
        w = Settings_a.get(Settings_a.setting == 'inactiveamnt_answers').val * ceil(
            (end.timestamp() - start.timestamp()) / 86400)
        p = f'{w} {pointWords(w, ("ответ", "ответа", "ответов"))}'
        sla = 'администратору'
    Inactives.create(nickname=user.nickname, role=user.role, fraction=user.fraction,
                     start=formatts(start.timestamp()), end=formatts(end.timestamp()), status="Одобрен").save()
    user.inactivestart = start.timestamp()
    user.inactiveend = end.timestamp()
    user.save()
    days = ceil((end.timestamp() - start.timestamp()) / 86400)
    text = (f'✅ Вы успешно выдали неактив {sla} <a href="tg://user?id={user.telegram_id}">{user.nickname}</a>. '
            f'Хотите снять <code>{p}</code> за неактив сроком в '
            f'<code>{days} {pointWords(days, ("день", "дня", "дней"))}</code>?')
    try:
        await message.bot.send_message(
            chat_id=user.telegram_id,
            text=f'📗 Администратор <a href="tg://user?id={admin.telegram_id}">{admin.nickname}'
                 f'</a> выдал вам неактив сроком в '
                 f'<code>{days} {pointWords(days, ("день", "дня", "дней"))}</code> (<code>'
                 f'{formatts(start.timestamp())} - {formatts(end.timestamp())}</code>).')
    except:
        text = '⚠️ Пользователя не удалось уведомить.\n' + text
    msg = await message.bot.send_message(
        chat_id=message.from_user.id, reply_markup=keyboard.usersinactiveset(),
        text=text)
    await state.clear()
    await state.update_data(msg=msg, w=w, user=f'{sla} {user.nickname}', uid=user.get_id(), p=p)
    sheets.main(composition=True, inactives=True)


@router.message(states.UsersInactive.remove)
async def usersinactiverm(message: Message, state: FSMContext):
    await message.delete()

    data = message.text.strip().replace(' - ', ' ').split()
    user: Users | None = Users.get_or_none(Users.nickname == data[0])
    admin = Users.get(Users.telegram_id == message.from_user.id)
    if user is None or not user.inactiveend or user.inactiveend < time.time() or not checkrole(admin, user):
        msg = await message.bot.send_message(
            chat_id=message.from_user.id,
            text='⚠️ Неверные данные или у пользователя нет действующего неактива.\nВведите никнейм:')
        await state.update_data(msg=msg)
        return
    Inactives.delete().where(Inactives.nickname == user.nickname, Inactives.start == formatts(user.inactivestart),
                             Inactives.end == formatts(user.inactiveend)).execute()
    user.inactivestart = None
    user.inactiveend = None
    user.save()
    try:
        await message.bot.send_message(
            chat_id=user.telegram_id,  text=f'📕 Администратор <a href="tg://user?id={admin.telegram_id}">'
                                            f'{admin.nickname}</a> снял вам действующий неактив.')
    except:
        pass
    msg = await message.bot.send_message(
        chat_id=message.from_user.id,
        text=f'✅ Вы успешно сняли неактив пользователю <a href="tg://user?id={user.telegram_id}">{user.nickname}</a>.')
    await state.clear()
    await state.update_data(msg=msg, uid=user.get_id())
    sheets.main(composition=True, inactives=True)


@router.message(states.Inactives.take)
async def inactivestake(message: Message, state: FSMContext):
    await message.delete()

    data = message.text.strip().replace(' - ', ' ').split()
    try:
        if len(data) != 2:
            raise ValueError
        start = datetime.strptime(data[0], '%d.%m.%Y')
        end = datetime.strptime(data[1], '%d.%m.%Y')
        if start.timestamp() > end.timestamp():
            raise ValueError
    except:
        msg = await message.bot.send_message(
            chat_id=message.from_user.id,
            text='⚠️ Неверные данные или формат.\nВведите дату неактива (формат: "15.12.2024 - 18.12.2024"):')
        await state.update_data(msg=msg)
        return
    user: Users = Users.get_or_none(Users.telegram_id == message.from_user.id)
    if user.role in SUPPORT_ROLES:
        w = Settings_s.get(Settings_s.setting == 'inactiveamnt_asks').val * ceil(
            (end.timestamp() - start.timestamp()) / 86400)
        p = f'{w} {pointWords(w, ("аск", "аска", "асков"))}'
    elif user.fraction:
        w = Settings_l.get(Settings_l.setting == 'inactiveamnt_points').val * ceil(
            (end.timestamp() - start.timestamp()) / 86400)
        p = f'{w} {pointWords(w, ("балл", "балла", "баллов"))}'
    else:
        w = Settings_a.get(Settings_a.setting == 'inactiveamnt_answers').val * ceil(
            (end.timestamp() - start.timestamp()) / 86400)
        p = f'{w} {pointWords(w, ("ответ", "ответа", "ответов"))}'
    msg = await message.bot.send_message(
        chat_id=message.from_user.id, reply_markup=keyboard.inactive_take_yon(),
        text=f'Вы уверены, что хотите взять неактив на {int((end.timestamp() - start.timestamp()) / 86400)} дня? '
             f'У вас будет снято {p}.')
    await state.clear()
    await state.update_data(msg=msg, w=w, start=start, end=end)


@router.message(states.Inactives.reason)
async def inactivesreason(message: Message, state: FSMContext):
    await message.delete()

    data = await state.get_data()
    user: Users = Users.get(Users.telegram_id == message.from_user.id)
    if user.fraction:
        chat = Chats.get(Chats.setting == 'inactive_leaders')
        apa = 'баллов'
    elif user.role in SUPPORT_ROLES:
        chat = Chats.get(Chats.setting == 'inactive_support')
        apa = 'асков'
    else:
        chat = Chats.get(Chats.setting == 'inactive_admins')
        apa = 'ответов'
    start = formatts(data['start'].timestamp())
    end = formatts(data['end'].timestamp())
    ir = InactiveRequests.create(start=start, end=end, w=data['w'], reason=message.text.strip(),
                                 tgid=user.telegram_id)
    iid = Inactives.select().order_by(Inactives.id.desc())
    if len(iid) > 0:
        iid = iid[0].get_id() + 1
    else:
        iid = 1
    await message.bot.send_message(chat_id=int(f'-100{chat.chat_id}'), message_thread_id=chat.thread_id,
                                   reply_markup=keyboard.inactiverequest(ir.get_id()), text=f'''
📗 [#{str(iid).zfill(4)}] Заявление на неактив — <a href="tg://user?id={user.telegram_id}">{user.nickname}</a>\n
🕘 Начало неактива: <code>{start}</code>
🕘 Конец неактива: <code>{end}</code>
📚 Причина: <code>{ir.reason}</code>
🟣 Количество {apa}: <code>{ir.w}</code>''')
    msg = await message.bot.send_message(chat_id=message.from_user.id,
                                         text=f'✅ Заявка №{f"{ir.get_id()}".zfill(4)} отправлена.')

    await state.clear()
    await state.update_data(msg=msg)


@router.message(states.Reports.sendadditionalreply)
@media_group_handler(only_album=False)
async def reportssendadditionalreply(messages: List[Message], state: FSMContext):
    for message in messages:
        try:
            await message.delete()
        except:
            pass

    message: Message = messages[-1]
    user: Users = Users.get(Users.telegram_id == message.from_user.id)
    media = MediaGroupBuilder()
    for obj in messages:
        if obj.photo:
            file_id = obj.photo[-1].file_id
        else:
            file_id = obj[obj.content_type].file_id
        media.add(media=file_id, type=obj.content_type)
    chat = Chats.get(Chats.setting == 'additionalreplies')
    msg = await message.bot.send_media_group(chat_id=int(f'-100{chat.chat_id}'), message_thread_id=chat.thread_id,
                                             media=media.build())
    await msg[0].reply(text=f'''
📗 Дополнительные ответы — <a href="tg://user?id={user.telegram_id}">{user.nickname}</a>
👤 Должность: <code>{user.role}</code>
🕘 Дата: <code>{datetime.now().strftime('%d.%m.%Y / %H:%M')}</code>
''', reply_markup=keyboard.additionalreply(user.telegram_id))
    msg = await message.bot.send_message(chat_id=message.from_user.id, text=f'✅ Заявка отправлена.')

    await state.clear()
    await state.update_data(msg=msg)


@router.message(states.Reports.sendobjective)
@media_group_handler(only_album=False)
async def reportssendobjective(messages: List[Message], state: FSMContext):
    for message in messages:
        try:
            await message.delete()
        except:
            pass

    message = messages[-1]
    if len(messages) > 1:
        msg = await message.bot.send_message(
            chat_id=message.from_user.id,
            text='⚠️ Вы можете отправить только одну картинку.\nОтправьте скриншот из "/astats":')
        await state.update_data(msg=msg)
        return
    user: Users = Users.get(Users.telegram_id == message.from_user.id)
    chat = Chats.get(Chats.setting == 'objective_admins')
    edit = await message.bot.send_photo(
        chat_id=int(f'-100{chat.chat_id}'), message_thread_id=chat.thread_id,
        caption=f'''
📗 Норматив от  — <a href="tg://user?id={user.telegram_id}">{user.nickname}</a>
👤 Должность: <code>{user.role}</code>
🕘 Дата: <code>{datetime.now().strftime('%d.%m.%Y / %H:%M')}</code>
''' + ('\n❗ Повторный норматив, требуется проверка.' if Objectives.get_or_none(
            Objectives.telegram_id == user.telegram_id,
            Objectives.time > datetime.now().replace(hour=0, minute=0, second=0).timestamp()) else ''),
        photo=messages[0].photo[-1].file_id, reply_markup=keyboard.reportssendobjective(user.telegram_id))
    Objectives.create(telegram_id=user.telegram_id, time=int(time.time()))
    msg = await message.bot.send_message(chat_id=message.from_user.id, text='✅ Заявка отправлена.')

    await state.clear()
    await state.update_data(msg=msg, edit=edit)


@router.message(states.Forms.create)
async def formscreate(message: Message, state: FSMContext):
    await message.delete()

    if not message.text or not message.text.strip().startswith('/'):
        msg = await message.bot.send_message(chat_id=message.from_user.id, text='⚠️ Неверная форма.\nВведите форму:')
        await state.update_data(msg=msg)
        return

    user: Users = Users.get(Users.telegram_id == message.from_user.id)
    msg = await message.bot.send_message(chat_id=message.from_user.id, reply_markup=keyboard.formproof_yon(),
                                         text='Прикрепить доказательства?')
    await state.clear()
    await state.update_data(
        msg=msg, form=message.text.strip() + f' by {user.nickname[0].upper()}.{user.nickname.split("_")[-1]}')


@router.message(states.Forms.proof)
async def formsproof(message: Message, state: FSMContext):
    await message.delete()

    if not message.text or not message.text.strip():
        data = None
    else:
        data = [i for i in re.split(r'[, \n]', message.text.strip()) if i != '']
    if not data or not all(validators.url(i) or validators.url('https://' + i) for i in data):
        msg = await message.bot.send_message(
            chat_id=message.from_user.id,
            text=f'⚠️ Вы не отправили ни одной ссылки.\n'
                 f'Отправьте ссылку(-и, через запятую или пробел) на доказательства:')
        await state.update_data(msg=msg)
        return
    data = [f'<a href="{i}">ссылка №{k + 1}</a>' for k, i in enumerate(data)]
    user: Users = Users.get(Users.telegram_id == message.from_user.id)
    form: str = (await state.get_data())['form']
    form: Forms = Forms.create(form=form, proofs=f'{data}', fromtgid=user.telegram_id)
    text = f'''
[📗 #{str(form.get_id()).zfill(4)}] Новая форма от <a href="tg://user?id={user.telegram_id}">{user.nickname}</a>\n
<code>{form.form}</code>\n\n 🔎 Доказательства: {", ".join(data)}.
'''
    chat: Chats = Chats.get(Chats.setting == 'forms')
    await message.bot.send_message(chat_id=int(f'-100{chat.chat_id}'), message_thread_id=chat.thread_id, text=text,
                                   reply_markup=keyboard.form(form.get_id()))
    msg = await message.bot.send_message(chat_id=message.from_user.id,
                                         text=f'✅ Форма #{str(form.get_id()).zfill(4)} отправлена.')

    await state.clear()
    await state.update_data(msg=msg)


@router.message(states.Promote.promote)
async def promotepromote(message: Message, state: FSMContext):
    await message.delete()

    user: Users | None = Users.get_or_none(Users.nickname == message.text.strip())
    if not user:
        msg = await message.bot.send_message(
            chat_id=message.from_user.id,
            text=f'⚠️ Администратора с таким никнеймом не существует.\nВведите никнейм администратора:')
        await state.update_data(msg=msg)
        return
    msg = await message.bot.send_message(chat_id=message.from_user.id, reply_markup=keyboard.promote(),
                                         text=f'Выберите новую должность:')
    await state.clear()
    await state.update_data(msg=msg, uid=user.telegram_id)


@router.message(states.Stats.remove)
async def statsremove(message: Message, state: FSMContext):
    await message.delete()

    user: Users = Users.get_by_id((await state.get_data())['user'])
    reason = message.text.strip()
    admin: Users = Users.get(Users.telegram_id == message.from_user.id)
    if admin.fraction:
        struct = 'l'
    elif admin.role in SUPPORT_ROLES:
        struct = 's'
    else:
        struct = 'a'
    Removed.create(nickname=user.nickname, role=user.role, appointed=user.appointed, name=user.name,
                   age=user.age, city=user.city, discord_id=user.discord_id, telegram_id=user.telegram_id,
                   reason=reason, forum=user.forum, whoremoved=admin.nickname, vk=user.vk,
                   date=formatts(time.time()), fraction=user.fraction, struct=struct).save()
    user.delete_instance()
    msg = await message.bot.send_message(chat_id=message.from_user.id,
                                         text=f'✅ Вы успешно сняли пользователя '
                                              f'<a href="tg://user?id={user.telegram_id}">{user.nickname}</a>.')
    try:
        await message.bot.send_message(
            chat_id=user.telegram_id,
            text=f'📕 Администратор <a href="tg://user?id={admin.telegram_id}">{admin.nickname}</a> снял вас с '
                 f'должности.')
    except:
        pass
    await state.clear()
    await state.update_data(msg=msg)
    sheets.main(composition=True, removed=True)
