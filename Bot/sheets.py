import time
import traceback
from math import ceil
import threading

import gspread
from gspread import Cell
from loguru import logger

from Bot.utils import formatts, pointWords, calcage
from config import LEADERS_TIME_LEFT, ROLES, SUPPORT_ROLES, FRACTIONS
from db import Users, Settings_s, Removed, Inactives, Sheets

google_sheets = gspread.service_account(filename='credits.json')
_lastupdate = 0


def getSheetsByID(sheetid: str):
    sh = google_sheets.open_by_key(sheetid)
    return sh.get_worksheet(0), sh.get_worksheet(1), sh.get_worksheet(2)


def getappointformbycode(sheetid: str, code: str, nickname: str | None) -> list | None:
    sh = google_sheets.open_by_key(sheetid)
    ws = sh.get_worksheet(0)
    for i in ws.get_all_values()[::-1]:
        if i[2].strip() == code.strip() and (nickname is None or i[3].strip() == nickname.strip()):
            res = i[3:]
            for k, y in enumerate(res):
                if isinstance(y, str):
                    res[k] = y.strip()
            return res  # nickname, name, age, city, discord_id, vk, forum, telegram_id
    return None


def main(composition: bool = False, removed: bool = False, inactives: bool = False):
    global _lastupdate
    if time.time() - _lastupdate < 60:
        return
    _lastupdate = time.time()
    try:
        threading.Thread(target=fill, args=(composition, removed, inactives,)).start()
    except:
        logger.exception(traceback.format_exc())


def fill(composition: bool, removed: bool, inactives: bool):
    try:
        sheetid_s = Sheets.get(Sheets.setting == "s").val
        sheetid_l = Sheets.get(Sheets.setting == "l").val
        sheetid_a = Sheets.get(Sheets.setting == "a").val
        composition_s, removed_s, inactives_s = getSheetsByID(sheetid_s)
        composition_l, removed_l, inactives_l = getSheetsByID(sheetid_l)
        composition_a, removed_a, inactives_a = getSheetsByID(sheetid_a)
        if composition:
            compdata_s = (sorted(Users.select().where(Users.role == SUPPORT_ROLES[1]), key=lambda x: x.appointed) +
                          sorted(Users.select().where(Users.role == SUPPORT_ROLES[0]), key=lambda x: x.appointed))
            compdata_l = sorted(Users.select().where(Users.role.is_null(True)),
                                key=lambda x: FRACTIONS.index(x.fraction))
            compdata_a = sorted(Users.select().where(Users.role << ROLES),
                                key=lambda x: (ROLES.index(x.role), x.promoted if x.promoted else x.appointed))
            fillcompisiton_s(composition_s, compdata_s)
            fillcompisiton_l(composition_l, compdata_l)
            fillcompisiton_a(composition_a, compdata_a)
        if removed:
            removeddata_s = Removed.select().where(Removed.role << SUPPORT_ROLES)[::-1]
            removeddata_l = Removed.select().where(Removed.role.is_null(True))[::-1]
            removeddata_a = Removed.select().where(Removed.role << ROLES)[::-1]
            fillremoved_s(removed_s, removeddata_s)
            fillremoved_l(removed_l, removeddata_l)
            fillremoved_a(removed_a, removeddata_a)
        if inactives:
            inactivesdata_s = Inactives.select().where(Inactives.role << SUPPORT_ROLES)
            inactivesdata_l = Inactives.select().where(Inactives.role.is_null(True))
            inactivesdata_a = Inactives.select().where(Inactives.role << ROLES)
            fillinactives_s(inactives_s, inactivesdata_s)
            fillinactives_l(inactives_l, inactivesdata_l)
            fillinactives_a(inactives_a, inactivesdata_a)
    except gspread.exceptions.APIError:
        pass
    except:
        logger.exception(traceback.format_exc())


def fillcompisiton_s(sheet, data):
    if sheet.row_count > 2:
        try:
            sheet.delete_rows(2, sheet.row_count)
        except:
            pass
    update_data = [Cell(row=1, col=1, value='СОСТАВ АГЕНТОВ ПОДДЕРЖКИ'), Cell(row=2, col=1, value='ID'),
                   Cell(row=2, col=2, value='Nickname'), Cell(row=2, col=3, value="Должность"),
                   Cell(row=2, col=4, value='Назначен'), Cell(row=2, col=5, value='Дней до перевода'),
                   Cell(row=2, col=6, value='Асков'), Cell(row=2, col=7, value='Выговоры'),
                   Cell(row=2, col=8, value='Предупреждения'), Cell(row=2, col=9, value='Устники'),
                   Cell(row=2, col=10, value='Действующий'), Cell(row=2, col=11, value='Имя'),
                   Cell(row=2, col=12, value='Возраст'), Cell(row=2, col=13, value='Город'),
                   Cell(row=2, col=14, value='DISCORD'), Cell(row=2, col=15, value='TELEGRAM'),
                   Cell(row=2, col=16, value='FORUM'), Cell(row=2, col=17, value='VK')]
    transferamnt_d = Settings_s.get(Settings_s.setting == "transferamnt_d").val
    k = 0
    for k, i in enumerate(data):
        i: Users
        inactive = f'{formatts(i.inactivestart)} - {formatts(i.inactiveend)}' \
            if i.inactiveend and i.inactiveend > time.time() else 'Нету'
        utd = transferamnt_d - ceil((time.time() - i.appointed) / 86400)
        utd = 0 if utd < 0 else utd
        appointed = formatts(i.appointed) + f' ({ceil((time.time() - i.appointed) / 86400)} дней)'
        update_data.extend([
            Cell(row=3 + k, col=1, value=k + 1), Cell(row=3 + k, col=2, value=i.nickname),
            Cell(row=3 + k, col=3, value=i.role), Cell(row=3 + k, col=4, value=appointed),
            Cell(row=3 + k, col=5, value=f'{utd} {pointWords(utd, ("день", "дня", "дней"))}'),
            Cell(row=3 + k, col=6, value=i.apa), Cell(row=3 + k, col=7, value=f'{i.rebuke} из 3'),
            Cell(row=3 + k, col=8, value=f'{i.warn} из 2'), Cell(row=3 + k, col=9, value=f'{i.verbal} из 2'),
            Cell(row=3 + k, col=10, value=inactive), Cell(row=3 + k, col=11, value=i.name),
            Cell(row=3 + k, col=12, value=f'{calcage(i.age)} ({i.dateofbirth})'), Cell(row=3 + k, col=13, value=i.city),
            Cell(row=3 + k, col=14, value=str(i.discord_id)), Cell(row=3 + k, col=15, value=i.telegram_id),
            Cell(row=3 + k, col=16, value=f'=HYPERLINK("{i.forum}"; "CLICK")'),
            Cell(row=3 + k, col=17, value=f'=HYPERLINK("{i.vk}"; "CLICK")')
        ])

    sheet.update_cells(update_data, value_input_option="USER_ENTERED")
    sheet.format("A1:Q1",
                 {"backgroundColor": {"red": 0.57, "green": 0.76, "blue": 0.49}, "horizontalAlignment": "CENTER",
                  "textFormat": {"foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}, "bold": True}})
    sheet.format("A2:Q2",
                 {"backgroundColor": {"red": 0.57, "green": 0.76, "blue": 0.49}, "horizontalAlignment": "CENTER",
                  "textFormat": {"foregroundColor": {"red": 0.0, "green": 0.0, "blue": 0.0}, "bold": True}})
    if len(data) > 0:
        sheet.format(f"A3:Q{k + 3}",
                     {"backgroundColor": {"red": 0.84, "green": 0.91, "blue": 0.82}, "horizontalAlignment": "CENTER",
                      "textFormat": {"foregroundColor": {"red": 0.0, "green": 0.0, "blue": 0.0}, "bold": True}})


def fillcompisiton_l(sheet, data):
    if sheet.row_count > 2:
        try:
            sheet.delete_rows(2, sheet.row_count)
        except:
            pass
    update_data = [Cell(row=1, col=1, value='СОСТАВ ЛИДЕРОВ'), Cell(row=2, col=1, value='ID'),
                   Cell(row=2, col=2, value='Nickname'), Cell(row=2, col=3, value="Фракция"),
                   Cell(row=2, col=4, value='Назначен'), Cell(row=2, col=5, value='Дней до перевода'),
                   Cell(row=2, col=6, value='Баллов'), Cell(row=2, col=7, value='Выговоры'),
                   Cell(row=2, col=8, value='Предупреждения'), Cell(row=2, col=9, value='Устники'),
                   Cell(row=2, col=10, value='Действующий'), Cell(row=2, col=11, value='Имя'),
                   Cell(row=2, col=12, value='Возраст'), Cell(row=2, col=13, value='Город'),
                   Cell(row=2, col=14, value='DISCORD'), Cell(row=2, col=15, value='TELEGRAM'),
                   Cell(row=2, col=16, value='FORUM'), Cell(row=2, col=17, value='VK')]
    k = 0
    for k, i in enumerate(data):
        i: Users
        inactive = f'{formatts(i.inactivestart)} - {formatts(i.inactiveend)}' \
            if i.inactiveend and i.inactiveend > time.time() else 'Нету'
        utd = LEADERS_TIME_LEFT - ceil((time.time() - i.appointed) / 86400)
        utd = 0 if utd < 0 else utd
        appointed = formatts(i.appointed) + f' ({ceil((time.time() - i.appointed) / 86400)} дней)'
        update_data.extend([
            Cell(row=3 + k, col=1, value=k + 1), Cell(row=3 + k, col=2, value=i.nickname),
            Cell(row=3 + k, col=3, value=i.fraction), Cell(row=3 + k, col=4, value=appointed),
            Cell(row=3 + k, col=5, value=f'{utd} {pointWords(utd, ("день", "дня", "дней"))}'),
            Cell(row=3 + k, col=6, value=i.apa), Cell(row=3 + k, col=7, value=f'{i.rebuke} из 3'),
            Cell(row=3 + k, col=8, value=f'{i.warn} из 2'), Cell(row=3 + k, col=9, value=f'{i.verbal} из 2'),
            Cell(row=3 + k, col=10, value=inactive), Cell(row=3 + k, col=11, value=i.name),
            Cell(row=3 + k, col=12, value=f'{calcage(i.age)} ({i.dateofbirth})'), Cell(row=3 + k, col=13, value=i.city),
            Cell(row=3 + k, col=14, value=str(i.discord_id)), Cell(row=3 + k, col=15, value=i.telegram_id),
            Cell(row=3 + k, col=16, value=f'=HYPERLINK("{i.forum}"; "CLICK")'),
            Cell(row=3 + k, col=17, value=f'=HYPERLINK("{i.vk}"; "CLICK")')
        ])

    sheet.update_cells(update_data, value_input_option="USER_ENTERED")
    sheet.format("A1:Q1",
                 {"backgroundColor": {"red": 0.57, "green": 0.76, "blue": 0.49}, "horizontalAlignment": "CENTER",
                  "textFormat": {"foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}, "bold": True}})
    sheet.format("A2:Q2",
                 {"backgroundColor": {"red": 0.57, "green": 0.76, "blue": 0.49}, "horizontalAlignment": "CENTER",
                  "textFormat": {"foregroundColor": {"red": 0.0, "green": 0.0, "blue": 0.0}, "bold": True}})
    if len(data) > 0:
        sheet.format(f"A3:Q{k + 3}",
                     {"backgroundColor": {"red": 0.84, "green": 0.91, "blue": 0.82}, "horizontalAlignment": "CENTER",
                      "textFormat": {"foregroundColor": {"red": 0.0, "green": 0.0, "blue": 0.0}, "bold": True}})


def fillcompisiton_a(sheet, data):
    if sheet.row_count > 2:
        try:
            sheet.delete_rows(2, sheet.row_count)
        except:
            pass
    update_data = [Cell(row=1, col=1, value='СОСТАВ АДМИНИСТРАЦИИ'), Cell(row=2, col=1, value='ID'),
                   Cell(row=2, col=2, value='Nickname'), Cell(row=2, col=3, value="Должность"),
                   Cell(row=2, col=4, value='Назначен'), Cell(row=2, col=5, value='Последнее повышение'),
                   Cell(row=2, col=6, value='Норматив'), Cell(row=2, col=7, value='Ответов'),
                   Cell(row=2, col=8, value='Выговоры'), Cell(row=2, col=9, value='Предупреждения'),
                   Cell(row=2, col=10, value='Устники'), Cell(row=2, col=11, value='Действующий'),
                   Cell(row=2, col=12, value='Имя'), Cell(row=2, col=13, value='Возраст'),
                   Cell(row=2, col=14, value='Город'), Cell(row=2, col=15, value='DISCORD'),
                   Cell(row=2, col=16, value='TELEGRAM'), Cell(row=2, col=17, value='FORUM'),
                   Cell(row=2, col=18, value='VK')]
    k = 0
    for k, i in enumerate(data):
        i: Users
        inactive = f'{formatts(i.inactivestart)} - {formatts(i.inactiveend)}' \
            if i.inactiveend and i.inactiveend > time.time() else 'Нету'
        oc = i.objective_completed if i.objective_completed is not None else '0'
        promoted = formatts(i.promoted) if i.promoted else 'Пусто'
        appointed = formatts(i.appointed) + f' ({ceil((time.time() - i.appointed) / 86400)} дней)'
        update_data.extend([
            Cell(row=3 + k, col=1, value=k + 1), Cell(row=3 + k, col=2, value=i.nickname),
            Cell(row=3 + k, col=3, value=i.role), Cell(row=3 + k, col=4, value=appointed),
            Cell(row=3 + k, col=5, value=promoted), Cell(row=3 + k, col=6, value=oc),
            Cell(row=3 + k, col=7, value=i.apa), Cell(row=3 + k, col=8, value=f'{i.rebuke} из 3'),
            Cell(row=3 + k, col=9, value=f'{i.warn} из 2'), Cell(row=3 + k, col=10, value=f'{i.verbal} из 2'),
            Cell(row=3 + k, col=11, value=inactive), Cell(row=3 + k, col=12, value=i.name),
            Cell(row=3 + k, col=13, value=f'{calcage(i.age)} ({i.dateofbirth})'), Cell(row=3 + k, col=14, value=i.city),
            Cell(row=3 + k, col=15, value=str(i.discord_id)), Cell(row=3 + k, col=16, value=i.telegram_id),
            Cell(row=3 + k, col=17, value=f'=HYPERLINK("{i.forum}"; "CLICK")'),
            Cell(row=3 + k, col=18, value=f'=HYPERLINK("{i.vk}"; "CLICK")')
        ])

    sheet.update_cells(update_data, value_input_option="USER_ENTERED")
    sheet.format("A1:R1",
                 {"backgroundColor": {"red": 0.57, "green": 0.76, "blue": 0.49}, "horizontalAlignment": "CENTER",
                  "textFormat": {"foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}, "bold": True}})
    sheet.format("A2:R2",
                 {"backgroundColor": {"red": 0.57, "green": 0.76, "blue": 0.49}, "horizontalAlignment": "CENTER",
                  "textFormat": {"foregroundColor": {"red": 0.0, "green": 0.0, "blue": 0.0}, "bold": True}})
    if len(data) > 0:
        sheet.format(f"A3:R{k + 3}",
                     {"backgroundColor": {"red": 0.84, "green": 0.91, "blue": 0.82}, "horizontalAlignment": "CENTER",
                      "textFormat": {"foregroundColor": {"red": 0.0, "green": 0.0, "blue": 0.0}, "bold": True}})


def fillremoved_s(sheet, data):
    if sheet.row_count > 2:
        try:
            sheet.delete_rows(2, sheet.row_count)
        except:
            pass
    update_data = [Cell(row=1, col=1, value='УЧЁТ СНЯТЫХ АГЕНТОВ ПОДДЕРЖКИ'), Cell(row=2, col=1, value='ID'),
                   Cell(row=2, col=2, value='Nickname'), Cell(row=2, col=3, value='Назначен'),
                   Cell(row=2, col=4, value='Имя'), Cell(row=2, col=5, value='Возраст'),
                   Cell(row=2, col=6, value='Город'), Cell(row=2, col=7, value='DISCORD'),
                   Cell(row=2, col=8, value='TELEGRAM'), Cell(row=2, col=9, value='FORUM'),
                   Cell(row=2, col=10, value='VK'), Cell(row=2, col=11, value='Снят кем'),
                   Cell(row=2, col=12, value='Причина'), Cell(row=2, col=13, value='Дата снятия')]
    k = 0
    for k, i in enumerate(data):
        i: Removed
        appointed = formatts(i.appointed) + f' ({ceil((time.time() - i.appointed) / 86400)} дней)'
        update_data.extend([
            Cell(row=3 + k, col=1, value=len(data) - k), Cell(row=3 + k, col=2, value=i.nickname),
            Cell(row=3 + k, col=3, value=appointed), Cell(row=3 + k, col=4, value=i.name),
            Cell(row=3 + k, col=5, value=i.age), Cell(row=3 + k, col=6, value=i.city),
            Cell(row=3 + k, col=7, value=str(i.discord_id)), Cell(row=3 + k, col=8, value=i.telegram_id),
            Cell(row=3 + k, col=9, value=f'=HYPERLINK("{i.forum}"; "CLICK")'),
            Cell(row=3 + k, col=10, value=f'=HYPERLINK("{i.vk}"; "CLICK")'),
            Cell(row=3 + k, col=11, value=i.whoremoved), Cell(row=3 + k, col=12, value=i.reason),
            Cell(row=3 + k, col=13, value=i.date)
        ])

    sheet.update_cells(update_data, value_input_option="USER_ENTERED")
    sheet.format("A1:M1",
                 {"backgroundColor": {"red": 0.57, "green": 0.76, "blue": 0.49}, "horizontalAlignment": "CENTER",
                  "textFormat": {"foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}, "bold": True}})
    sheet.format("A2:M2",
                 {"backgroundColor": {"red": 0.57, "green": 0.76, "blue": 0.49}, "horizontalAlignment": "CENTER",
                  "textFormat": {"foregroundColor": {"red": 0.0, "green": 0.0, "blue": 0.0}, "bold": True}})
    if len(data) > 0:
        sheet.format(f"A3:M{k + 3}",
                     {"backgroundColor": {"red": 0.84, "green": 0.91, "blue": 0.82}, "horizontalAlignment": "CENTER",
                      "textFormat": {"foregroundColor": {"red": 0.0, "green": 0.0, "blue": 0.0}, "bold": True}})


def fillremoved_l(sheet, data):
    if sheet.row_count > 2:
        try:
            sheet.delete_rows(2, sheet.row_count)
        except:
            pass
    update_data = [Cell(row=1, col=1, value='УЧЁТ СНЯТЫХ ЛИДЕРОВ'), Cell(row=2, col=1, value='ID'),
                   Cell(row=2, col=2, value='Nickname'), Cell(row=2, col=3, value="Фракция"),
                   Cell(row=2, col=4, value='Назначен'), Cell(row=2, col=5, value='Имя'),
                   Cell(row=2, col=6, value='Возраст'), Cell(row=2, col=7, value='Город'),
                   Cell(row=2, col=8, value='DISCORD'), Cell(row=2, col=9, value='TELEGRAM'),
                   Cell(row=2, col=10, value='FORUM'), Cell(row=2, col=11, value='VK'),
                   Cell(row=2, col=12, value='Снят кем'), Cell(row=2, col=13, value='Причина'),
                   Cell(row=2, col=14, value='Дата снятия')]
    k = 0
    for k, i in enumerate(data):
        i: Removed
        appointed = formatts(i.appointed) + f' ({ceil((time.time() - i.appointed) / 86400)} дней)'
        update_data.extend([
            Cell(row=3 + k, col=1, value=len(data) - k), Cell(row=3 + k, col=2, value=i.nickname),
            Cell(row=3 + k, col=3, value=i.fraction), Cell(row=3 + k, col=4, value=appointed),
            Cell(row=3 + k, col=5, value=i.name), Cell(row=3 + k, col=6, value=i.age),
            Cell(row=3 + k, col=7, value=i.city), Cell(row=3 + k, col=8, value=str(i.discord_id)),
            Cell(row=3 + k, col=9, value=i.telegram_id),
            Cell(row=3 + k, col=10, value=f'=HYPERLINK("{i.forum}"; "CLICK")'),
            Cell(row=3 + k, col=11, value=f'=HYPERLINK("{i.vk}"; "CLICK")'),
            Cell(row=3 + k, col=12, value=i.whoremoved),
            Cell(row=3 + k, col=13, value=i.reason), Cell(row=3 + k, col=14, value=i.date)
        ])

    sheet.update_cells(update_data, value_input_option="USER_ENTERED")
    sheet.format("A1:N1",
                 {"backgroundColor": {"red": 0.57, "green": 0.76, "blue": 0.49}, "horizontalAlignment": "CENTER",
                  "textFormat": {"foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}, "bold": True}})
    sheet.format("A2:N2",
                 {"backgroundColor": {"red": 0.57, "green": 0.76, "blue": 0.49}, "horizontalAlignment": "CENTER",
                  "textFormat": {"foregroundColor": {"red": 0.0, "green": 0.0, "blue": 0.0}, "bold": True}})
    if len(data) > 0:
        sheet.format(f"A3:N{k + 3}",
                     {"backgroundColor": {"red": 0.84, "green": 0.91, "blue": 0.82}, "horizontalAlignment": "CENTER",
                      "textFormat": {"foregroundColor": {"red": 0.0, "green": 0.0, "blue": 0.0}, "bold": True}})


def fillremoved_a(sheet, data):
    if sheet.row_count > 2:
        try:
            sheet.delete_rows(2, sheet.row_count)
        except:
            pass
    update_data = [Cell(row=1, col=1, value='УЧЁТ СНЯТЫХ АДМИНИСТРАТОРОВ'), Cell(row=2, col=1, value='ID'),
                   Cell(row=2, col=2, value='Nickname'), Cell(row=2, col=3, value="Должность"),
                   Cell(row=2, col=4, value='Назначен'), Cell(row=2, col=5, value='Имя'),
                   Cell(row=2, col=6, value='Возраст'), Cell(row=2, col=7, value='Город'),
                   Cell(row=2, col=8, value='DISCORD'), Cell(row=2, col=9, value='TELEGRAM'),
                   Cell(row=2, col=10, value='FORUM'), Cell(row=2, col=11, value='VK'),
                   Cell(row=2, col=12, value='Снят кем'), Cell(row=2, col=13, value='Причина'),
                   Cell(row=2, col=14, value='Дата снятия')]
    k = 0
    for k, i in enumerate(data):
        i: Removed
        appointed = formatts(i.appointed) + f' ({ceil((time.time() - i.appointed) / 86400)} дней)'
        update_data.extend([
            Cell(row=3 + k, col=1, value=len(data) - k), Cell(row=3 + k, col=2, value=i.nickname),
            Cell(row=3 + k, col=3, value=i.role), Cell(row=3 + k, col=4, value=appointed),
            Cell(row=3 + k, col=5, value=i.name), Cell(row=3 + k, col=6, value=i.age),
            Cell(row=3 + k, col=7, value=i.city), Cell(row=3 + k, col=8, value=str(i.discord_id)),
            Cell(row=3 + k, col=9, value=i.telegram_id),
            Cell(row=3 + k, col=10, value=f'=HYPERLINK("{i.forum}"; "CLICK")'),
            Cell(row=3 + k, col=11, value=f'=HYPERLINK("{i.vk}"; "CLICK")'),
            Cell(row=3 + k, col=12, value=i.whoremoved),
            Cell(row=3 + k, col=13, value=i.reason), Cell(row=3 + k, col=14, value=i.date)
        ])

    sheet.update_cells(update_data, value_input_option="USER_ENTERED")
    sheet.format("A1:N1",
                 {"backgroundColor": {"red": 0.57, "green": 0.76, "blue": 0.49}, "horizontalAlignment": "CENTER",
                  "textFormat": {"foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}, "bold": True}})
    sheet.format("A2:N2",
                 {"backgroundColor": {"red": 0.57, "green": 0.76, "blue": 0.49}, "horizontalAlignment": "CENTER",
                  "textFormat": {"foregroundColor": {"red": 0.0, "green": 0.0, "blue": 0.0}, "bold": True}})
    if len(data) > 0:
        sheet.format(f"A3:N{k + 3}",
                     {"backgroundColor": {"red": 0.84, "green": 0.91, "blue": 0.82}, "horizontalAlignment": "CENTER",
                      "textFormat": {"foregroundColor": {"red": 0.0, "green": 0.0, "blue": 0.0}, "bold": True}})


def fillinactives_s(sheet, data):
    if sheet.row_count > 2:
        try:
            sheet.delete_rows(2, sheet.row_count)
        except:
            pass
    update_data = [Cell(row=1, col=1, value='УЧЁТ НЕАКТИВОВ АГЕНТОВ ПОДДЕРЖКИ'), Cell(row=2, col=1, value='ID'),
                   Cell(row=2, col=2, value='Nickname'), Cell(row=2, col=3, value='Начало'),
                   Cell(row=2, col=4, value='Конец'), Cell(row=2, col=5, value='Статус'),
                   Cell(row=2, col=6, value='Причина'),]
    k = 0
    for k, i in enumerate(data):
        i: Inactives
        update_data.extend([
            Cell(row=3 + k, col=1, value=k + 1), Cell(row=3 + k, col=2, value=i.nickname),
            Cell(row=3 + k, col=3, value=i.start), Cell(row=3 + k, col=4, value=i.end),
            Cell(row=3 + k, col=5, value=i.status), Cell(row=3 + k, col=6, value=i.reason)
        ])

    sheet.update_cells(update_data, value_input_option="USER_ENTERED")
    sheet.format("A1:F1",
                 {"backgroundColor": {"red": 0.57, "green": 0.76, "blue": 0.49}, "horizontalAlignment": "CENTER",
                  "textFormat": {"foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}, "bold": True}})
    sheet.format("A2:F2",
                 {"backgroundColor": {"red": 0.57, "green": 0.76, "blue": 0.49}, "horizontalAlignment": "CENTER",
                  "textFormat": {"foregroundColor": {"red": 0.0, "green": 0.0, "blue": 0.0}, "bold": True}})
    if len(data) > 0:
        sheet.format(f"A3:F{k + 3}",
                     {"backgroundColor": {"red": 0.84, "green": 0.91, "blue": 0.82}, "horizontalAlignment": "CENTER",
                      "textFormat": {"foregroundColor": {"red": 0.0, "green": 0.0, "blue": 0.0}, "bold": True}})


def fillinactives_l(sheet, data):
    if sheet.row_count > 2:
        try:
            sheet.delete_rows(2, sheet.row_count)
        except:
            pass
    update_data = [Cell(row=1, col=1, value='УЧЁТ НЕАКТИВОВ ЛИДЕРОВ'), Cell(row=2, col=1, value='ID'),
                   Cell(row=2, col=2, value='Nickname'), Cell(row=2, col=3, value="Фракция"),
                   Cell(row=2, col=4, value='Начало'), Cell(row=2, col=5, value='Конец'),
                   Cell(row=2, col=6, value='Статус'), Cell(row=2, col=7, value='Причина'),]
    k = 0
    for k, i in enumerate(data):
        i: Inactives
        update_data.extend([
            Cell(row=3 + k, col=1, value=k + 1), Cell(row=3 + k, col=2, value=i.nickname),
            Cell(row=3 + k, col=3, value=i.fraction), Cell(row=3 + k, col=4, value=i.start),
            Cell(row=3 + k, col=5, value=i.end), Cell(row=3 + k, col=6, value=i.status),
            Cell(row=3 + k, col=7, value=i.reason)
        ])

    sheet.update_cells(update_data, value_input_option="USER_ENTERED")
    sheet.format("A1:G1",
                 {"backgroundColor": {"red": 0.57, "green": 0.76, "blue": 0.49}, "horizontalAlignment": "CENTER",
                  "textFormat": {"foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}, "bold": True}})
    sheet.format("A2:G2",
                 {"backgroundColor": {"red": 0.57, "green": 0.76, "blue": 0.49}, "horizontalAlignment": "CENTER",
                  "textFormat": {"foregroundColor": {"red": 0.0, "green": 0.0, "blue": 0.0}, "bold": True}})
    if len(data) > 0:
        sheet.format(f"A3:G{k + 3}",
                     {"backgroundColor": {"red": 0.84, "green": 0.91, "blue": 0.82}, "horizontalAlignment": "CENTER",
                      "textFormat": {"foregroundColor": {"red": 0.0, "green": 0.0, "blue": 0.0}, "bold": True}})


def fillinactives_a(sheet, data):
    if sheet.row_count > 2:
        try:
            sheet.delete_rows(2, sheet.row_count)
        except:
            pass
    update_data = [Cell(row=1, col=1, value='УЧЁТ НЕАКТИВОВ АДМИНИСТРАЦИИ'), Cell(row=2, col=1, value='ID'),
                   Cell(row=2, col=2, value='Nickname'), Cell(row=2, col=3, value="Должность"),
                   Cell(row=2, col=4, value='Начало'), Cell(row=2, col=5, value='Конец'),
                   Cell(row=2, col=6, value='Статус'), Cell(row=2, col=7, value='Причина'),]
    k = 0
    for k, i in enumerate(data):
        i: Inactives
        update_data.extend([
            Cell(row=3 + k, col=1, value=k + 1), Cell(row=3 + k, col=2, value=i.nickname),
            Cell(row=3 + k, col=3, value=i.role), Cell(row=3 + k, col=4, value=i.start),
            Cell(row=3 + k, col=5, value=i.end), Cell(row=3 + k, col=6, value=i.status),
            Cell(row=3 + k, col=7, value=i.reason)
        ])

    sheet.update_cells(update_data, value_input_option="USER_ENTERED")
    sheet.format("A1:G1",
                 {"backgroundColor": {"red": 0.57, "green": 0.76, "blue": 0.49}, "horizontalAlignment": "CENTER",
                  "textFormat": {"foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}, "bold": True}})
    sheet.format("A2:G2",
                 {"backgroundColor": {"red": 0.57, "green": 0.76, "blue": 0.49}, "horizontalAlignment": "CENTER",
                  "textFormat": {"foregroundColor": {"red": 0.0, "green": 0.0, "blue": 0.0}, "bold": True}})
    if len(data) > 0:
        sheet.format(f"A3:G{k + 3}",
                     {"backgroundColor": {"red": 0.84, "green": 0.91, "blue": 0.82}, "horizontalAlignment": "CENTER",
                      "textFormat": {"foregroundColor": {"red": 0.0, "green": 0.0, "blue": 0.0}, "bold": True}})
