from typing import Iterable

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import ROLES, FRACTIONS, SUPPORT_ROLES


class Callback(CallbackData, prefix='cb'):
    type: str


def start() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text='Главное меню', callback_data=Callback(type='panel').pack()))

    return builder.as_markup()


def panel(role: str | None, isswatcher) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text='Моя статистика', callback_data=Callback(type='mystats').pack()))
    builder.row(InlineKeyboardButton(text='Неактивы', callback_data=Callback(type='myinactives').pack()))
    if role in ROLES:
        builder.row(InlineKeyboardButton(text='Отчёты', callback_data=Callback(type='reports').pack()),
                    InlineKeyboardButton(text='Формы', callback_data=Callback(type='forms').pack()))
    if role in ('Главный АП', 'Главный следящий АП', 'Заместитель ГС АП') or isswatcher:
        builder.row(InlineKeyboardButton(text='Управление АП', callback_data=Callback(type='supportcontrol'
                                                                                      ).pack()))
    if role in ('Главный за лидерами', 'Главный следящий ГОСС', 'Главный следящий ОПГ', 'Заместитель ГС ГОСС',
                'Заместитель ГС ОПГ'):
        builder.row(InlineKeyboardButton(text='Управление ЛД', callback_data=Callback(type='leaderscontrol'
                                                                                      ).pack()))
    elif role in ('Куратор администрации',):
        builder.row(InlineKeyboardButton(text='Управление АДМ', callback_data=Callback(type='adminscontrol'
                                                                                       ).pack()))
    elif role in ('Главный администратор', 'Основной ЗГА', 'Заместитель ГА'):
        builder.row(InlineKeyboardButton(text='Управление сервером', callback_data=Callback(type='servercontrol'
                                                                                            ).pack()))

    return builder.as_markup()


def supportcontrol() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text='Список АП', callback_data=Callback(type='supportlist_0').pack()))
    builder.row(InlineKeyboardButton(text='Назначить', callback_data=Callback(type='appoint').pack()),
                InlineKeyboardButton(text='Аски', callback_data=Callback(type='asks').pack()))
    builder.row(InlineKeyboardButton(text='Наказания', callback_data=Callback(type='punishments').pack()),
                InlineKeyboardButton(text='Неактивы', callback_data=Callback(type='inactives_s').pack()))
    builder.row(InlineKeyboardButton(text='Настройки АП', callback_data=Callback(type='settings_s').pack()))

    return builder.as_markup()


def leaderscontrol() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text='Список лидеров', callback_data=Callback(type='leaderslist').pack()))
    builder.row(InlineKeyboardButton(text='Назначить', callback_data=Callback(type='appointleader').pack()),
                InlineKeyboardButton(text='Неактивы', callback_data=Callback(type='inactives_l').pack()))
    builder.row(InlineKeyboardButton(text='Баллы', callback_data=Callback(type='points').pack()),
                InlineKeyboardButton(text='Наказания', callback_data=Callback(type='punishments_l').pack()))
    builder.row(InlineKeyboardButton(text='Настройки', callback_data=Callback(type='settings_l').pack()))

    return builder.as_markup()


def adminscontrol() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text='Администрация', callback_data=Callback(type='administration').pack()))
    builder.row(InlineKeyboardButton(text='Неактивы', callback_data=Callback(type='inactives_a').pack()),
                InlineKeyboardButton(text='Наказания', callback_data=Callback(type='punishments_a').pack()))
    builder.row(InlineKeyboardButton(text='Ответы', callback_data=Callback(type='answers').pack()))
    builder.row(InlineKeyboardButton(text='Управление структурами', callback_data=Callback(type='structurescontrol'
                                                                                           ).pack()))

    return builder.as_markup()


def myinactives() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text='Взять неактив', callback_data=Callback(type='takeinactive').pack()),
                InlineKeyboardButton(text='Снять неактив', callback_data=Callback(type='cancelinactive').pack()))
    builder.row(InlineKeyboardButton(text='Список неактивов', callback_data=Callback(type='listinactive').pack()))

    return builder.as_markup()


def reports() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text='Отправить норматив', callback_data=Callback(type='sendobjective').pack()))
    builder.row(InlineKeyboardButton(text='Отправить доп. ответы', callback_data=Callback(type='sendadditionalreply'
                                                                                          ).pack()))

    return builder.as_markup()


def forms() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text='Создать форму', callback_data=Callback(type='createform').pack()))

    return builder.as_markup()


def createform() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text='Да', callback_data=Callback(type='createform_y').pack()),
                InlineKeyboardButton(text='Нет', callback_data=Callback(type='createform_n').pack()))

    return builder.as_markup()


def appoint() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text='Проверить', callback_data=Callback(type='appointcheck').pack()))

    return builder.as_markup()


def punishments() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text='Устные предупреждения', callback_data=Callback(type='punishments_v').pack()))
    builder.row(InlineKeyboardButton(text='Предупреждения', callback_data=Callback(type='punishments_w').pack()))
    builder.row(InlineKeyboardButton(text='Выговоры', callback_data=Callback(type='punishments_r').pack()))

    return builder.as_markup()


def punishments_l() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text='Устные предупреждения', callback_data=Callback(type='punishments_l_v'
                                                                                          ).pack()))
    builder.row(InlineKeyboardButton(text='Предупреждения', callback_data=Callback(type='punishments_l_w').pack()))
    builder.row(InlineKeyboardButton(text='Выговоры', callback_data=Callback(type='punishments_l_r').pack()))

    return builder.as_markup()


def punishments_a() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text='Устные предупреждения', callback_data=Callback(type='punishments_a_v'
                                                                                          ).pack()))
    builder.row(InlineKeyboardButton(text='Предупреждения', callback_data=Callback(type='punishments_a_w').pack()))
    builder.row(InlineKeyboardButton(text='Выговоры', callback_data=Callback(type='punishments_a_r').pack()))

    return builder.as_markup()


def inactives_s() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text='Выдать неактив', callback_data=Callback(type='setinactive_s').pack()),
                InlineKeyboardButton(text='Снять неактив', callback_data=Callback(type='removeinactive_s').pack()))
    builder.row(InlineKeyboardButton(text='Список неактивов', callback_data=Callback(type='listinactive_s').pack()))

    return builder.as_markup()


def inactives_a() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text='Выдать неактив', callback_data=Callback(type='setinactive_a').pack()),
                InlineKeyboardButton(text='Снять неактив', callback_data=Callback(type='removeinactive_a').pack()))
    builder.row(InlineKeyboardButton(text='Список неактивов', callback_data=Callback(type='listinactive_a').pack()))

    return builder.as_markup()


def settings_s() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text='Неактивы', callback_data=Callback(type='setinactiveamnt_s').pack()))
    builder.row(InlineKeyboardButton(text='Перевод', callback_data=Callback(type='settransferamnt').pack()))

    return builder.as_markup()


def settransferamnt() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text='Назад', callback_data=Callback(type='settings_s').pack()))
    builder.row(InlineKeyboardButton(text='Количество дней', callback_data=Callback(type='settransferdays').pack()))
    builder.row(InlineKeyboardButton(text='Количество асков', callback_data=Callback(type='settransferasks').pack()))

    return builder.as_markup()


def leaderslist(leaders: Iterable) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for i in leaders:
        builder.row(
            InlineKeyboardButton(text=i.fraction, callback_data=Callback(type=f'leaderstats_{i.nickname}').pack()),
            InlineKeyboardButton(text=i.nickname, callback_data=Callback(type=f'leaderstats_{i.nickname}').pack())
        )

    return builder.as_markup()


def inactives_l() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text='Выдать неактив', callback_data=Callback(type='setinactive_l').pack()),
                InlineKeyboardButton(text='Снять неактив', callback_data=Callback(type='removeinactive_l').pack()))
    builder.row(InlineKeyboardButton(text='Список неактивов', callback_data=Callback(type='listinactive_l').pack()))

    return builder.as_markup()


def settings_l() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text='Неактивы', callback_data=Callback(type='setinactiveamnt_l').pack()))

    return builder.as_markup()


def administration() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text='Список', callback_data=Callback(type='administration_list_0').pack()))
    builder.row(InlineKeyboardButton(text='Назначить', callback_data=Callback(type='appoint_a').pack()),
                InlineKeyboardButton(text='Повысить', callback_data=Callback(type='promote').pack()))

    return builder.as_markup()


def structurescontrol() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text='Лидеры', callback_data=Callback(type='leaderscontrol').pack()),
                InlineKeyboardButton(text='Агенты Поддержки', callback_data=Callback(type='supportcontrol').pack()))
    builder.row(InlineKeyboardButton(text='Статистика', callback_data=Callback(type='strctrstats').pack()))

    return builder.as_markup()


def servercontrol() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text='Настройки', callback_data=Callback(type='serversettings').pack()))
    builder.row(InlineKeyboardButton(text='Управление АП', callback_data=Callback(type='supportcontrol').pack()),
                InlineKeyboardButton(text='Управление ЛД', callback_data=Callback(type='leaderscontrol').pack()))
    builder.row(InlineKeyboardButton(text='Управление АДМ', callback_data=Callback(type='adminscontrol').pack()))
    builder.row(InlineKeyboardButton(text='Следящие АП', callback_data=Callback(type='swatchers').pack()))
    # builder.row(InlineKeyboardButton(text='Доступы', callback_data=Callback(type='accesses').pack()))

    return builder.as_markup()


def swatchers() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text='Назад', callback_data=Callback(type='servercontrol').pack()))
    builder.row(InlineKeyboardButton(text='Добавить следящего', callback_data=Callback(type='addswatcher').pack()),
                InlineKeyboardButton(text='Удалить следящего', callback_data=Callback(type='remswatcher').pack()))
    builder.row(InlineKeyboardButton(text='Список следящих', callback_data=Callback(type='listswatcher').pack()))

    return builder.as_markup()


def serversettings() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text='Чаты', callback_data=Callback(type='serverchats').pack()))
    builder.row(InlineKeyboardButton(text='Администрация', callback_data=Callback(type='serveradmins').pack()))
    builder.row(InlineKeyboardButton(text='Таблицы', callback_data=Callback(type='serversheets').pack()))

    return builder.as_markup()


def serversheets() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text='Агенты поддержки', callback_data=Callback(type='serversheets_support'
                                                                                     ).pack()))
    builder.row(InlineKeyboardButton(text='Лидеры', callback_data=Callback(type='serversheets_leaders').pack()))
    builder.row(InlineKeyboardButton(text='Администрация', callback_data=Callback(type='serversheets_admins').pack()))

    return builder.as_markup()


def serveradmins() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text='Неактивы', callback_data=Callback(type='setinactiveamnt_a').pack()))

    return builder.as_markup()


def serverchats() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text='Норматив', callback_data=Callback(type='serverchats_objective').pack()),
                InlineKeyboardButton(text='Доп. ответы', callback_data=Callback(type='serverchats_additionalreplies'
                                                                                ).pack()))
    builder.row(InlineKeyboardButton(text='Формы', callback_data=Callback(type='serverchats_forms').pack()),
                InlineKeyboardButton(text='Неактивы', callback_data=Callback(type='serverchats_inactive').pack()))

    return builder.as_markup()


def serverchats_objective() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text='Администрация', callback_data=Callback(type='objective_admins').pack()))

    return builder.as_markup()


def serverchats_additionalreplies() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text='Администрация', callback_data=Callback(type='additionalreplies_admins'
                                                                                  ).pack()))

    return builder.as_markup()


def serverchats_inactive() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text='Агенты поддержки', callback_data=Callback(type='inactive_support').pack()))
    builder.row(InlineKeyboardButton(text='Лидеры', callback_data=Callback(type='inactive_leaders').pack()))
    builder.row(InlineKeyboardButton(text='Администрация', callback_data=Callback(type='inactive_admins').pack()))

    return builder.as_markup()


def accesses() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text='Список', callback_data=Callback(type='accesseslist').pack()))
    builder.row(InlineKeyboardButton(text='Выдать доступ', callback_data=Callback(type='setaccess').pack()),
                InlineKeyboardButton(text='Снять доступ', callback_data=Callback(type='removeaccess').pack()))

    return builder.as_markup()


def cancelinactive() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text='Да', callback_data=Callback(type='cancelinactive_y').pack()),
                InlineKeyboardButton(text='Нет', callback_data=Callback(type='cancelinactive_n').pack()))

    return builder.as_markup()


def supportlist(page, sup):
    builder = InlineKeyboardBuilder()

    row = []
    if sup > (page + 1) * 15:
        row.append(InlineKeyboardButton(text='▶️', callback_data=Callback(type=f'supportlist_{page + 1}').pack()))
    if page > 0:
        row.append(InlineKeyboardButton(text='◀️', callback_data=Callback(type=f'supportlist_{page - 1}').pack()))

    if not row:
        return None
    builder.row(*row)
    return builder.as_markup()


def administration_list(page, sup):
    builder = InlineKeyboardBuilder()

    row = []
    if sup > (page + 1) * 15:
        row.append(InlineKeyboardButton(text='▶️', callback_data=Callback(type=f'administration_list_{page + 1}'
                                                                          ).pack()))
    if page > 0:
        row.append(InlineKeyboardButton(text='◀️', callback_data=Callback(type=f'administration_list_{page - 1}'
                                                                          ).pack()))

    if not row:
        return None
    builder.row(*row)
    return builder.as_markup()


def appointleadercheck():
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text='Проверить', callback_data=Callback(type='appointleadercheck').pack()))

    return builder.as_markup()


def appointcheck():
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text='Проверить', callback_data=Callback(type='appointcheck').pack()))

    return builder.as_markup()


def leaderstats_remove(leader):
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text='Снять лидера', callback_data=Callback(type=f'removeleader_{leader}').pack()))

    return builder.as_markup()


def appoint_acheck():
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text='Проверить', callback_data=Callback(type='appoint_acheck').pack()))

    return builder.as_markup()


def inactive_take_yon() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text='Да', callback_data=Callback(type='inactive_take_y').pack()),
                InlineKeyboardButton(text='Нет', callback_data=Callback(type='inactive_take_n').pack()))

    return builder.as_markup()


def formproof_yon():
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text='Да', callback_data=Callback(type='formproof_y').pack()),
                InlineKeyboardButton(text='Нет', callback_data=Callback(type='formproof_send').pack()))

    return builder.as_markup()


def formproof_send():
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text='Отправить', callback_data=Callback(type='formproof_send').pack()))

    return builder.as_markup()


def form(id):
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text='Одобрить', callback_data=Callback(type=f'form_approve_{id}').pack()),
                InlineKeyboardButton(text='Отказать', callback_data=Callback(type=f'form_disapprove_{id}').pack()))

    return builder.as_markup()


def inactiverequest(id):
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text='Одобрить', callback_data=Callback(type=f'inactiverequest_approve_{id}'
                                                                             ).pack()),
                InlineKeyboardButton(text='Отказать', callback_data=Callback(type=f'inactiverequest_disapprove_{id}'
                                                                             ).pack()))

    return builder.as_markup()


def additionalreply(id):
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text='Одобрить', callback_data=Callback(type=f'additionalreply_approve_{id}'
                                                                             ).pack()),
                InlineKeyboardButton(text='Отказать', callback_data=Callback(type=f'additionalreply_disapprove_{id}'
                                                                             ).pack()))

    return builder.as_markup()


def inactiveapa(id, apa):
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text=f'Снять {apa}', callback_data=Callback(type=f'inactiveapa_{id}').pack()))

    return builder.as_markup()


def reportssendobjective(id):
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text='Одобрить', callback_data=Callback(type=f'reportssendobjective_approve_{id}'
                                                                             ).pack()),
                InlineKeyboardButton(text='Отказать', callback_data=Callback(type=f'reportssendobjective_disapprove_'
                                                                                  f'{id}').pack()))
    builder.row(InlineKeyboardButton(text='Ответы', callback_data=Callback(type=f'reportssendobjective_answers_{id}'
                                                                           ).pack()))

    return builder.as_markup()


def usersinactiveset():
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text='Снять', callback_data=Callback(type='usersinactiveset_y').pack()),
                InlineKeyboardButton(text='Не снимать', callback_data=Callback(type='usersinactiveset_n').pack()))

    return builder.as_markup()


def promote():
    builder = InlineKeyboardBuilder()

    for k, i in enumerate(ROLES):
        builder.row(InlineKeyboardButton(text=i, callback_data=Callback(type=f'promote_{k}').pack()))

    return builder.as_markup()


def promote_days():
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text='Да', callback_data=Callback(type=f'promotedays_y').pack()),
                InlineKeyboardButton(text='Нет', callback_data=Callback(type=f'promotedays_n').pack()))

    return builder.as_markup()


def promote_answers():
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text='Да', callback_data=Callback(type=f'promoteanswers_y').pack()),
                InlineKeyboardButton(text='Нет', callback_data=Callback(type=f'promoteanswers_n').pack()))

    return builder.as_markup()


def stats(role, uid):
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text='Снять с должности', callback_data=Callback(type=f'removereason_{uid}'
                                                                                      ).pack()))
    if role in SUPPORT_ROLES:
        t = [InlineKeyboardButton(text='Наказания', callback_data=Callback(type='punishments').pack()),]
    elif role in ROLES:
        t = [InlineKeyboardButton(text='Наказания', callback_data=Callback(type='punishments_a').pack()),]
    else:
        t = [InlineKeyboardButton(text='Наказания', callback_data=Callback(type='punishments_l').pack()),]
    if role in SUPPORT_ROLES:
        builder.row(InlineKeyboardButton(text='Перевод', callback_data=Callback(type=f'transfer_{uid}').pack()))
    elif role in ROLES:
        t.insert(0, InlineKeyboardButton(text='Повысить', callback_data=Callback(type='promote').pack()))
    builder.row(*t)
    builder.row(InlineKeyboardButton(text='Обновить информацию', callback_data=Callback(type='updateinfo').pack()))

    return builder.as_markup()


def appointl(fracs):
    builder = InlineKeyboardBuilder()

    for i in fracs:
        builder.row(InlineKeyboardButton(text=i, callback_data=Callback(type=f'appointl_{FRACTIONS.index(i)}').pack()))

    return builder.as_markup()


def appointa(roles):
    builder = InlineKeyboardBuilder()

    for i in roles:
        builder.row(InlineKeyboardButton(text=ROLES[i], callback_data=Callback(type=f'appoint_a_{i}').pack()))

    return builder.as_markup()


def updateinfo_check():
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text='Проверить', callback_data=Callback(type='updateinfo_check').pack()))

    return builder.as_markup()
