"""
Time utilities.
Provide a shared interface for retrieving time information.
"""

import cnlunar
from datetime import datetime

# Chinese weekday names are locale data used by prompts and language fixtures.
WEEKDAY_MAP = {
    "Monday": "星期一",
    "Tuesday": "星期二", 
    "Wednesday": "星期三",
    "Thursday": "星期四",
    "Friday": "星期五",
    "Saturday": "星期六",
    "Sunday": "星期日",
}


def get_current_time() -> str:
    """
    Return the current time as HH:MM.
    """
    return datetime.now().strftime("%H:%M")


def get_current_date() -> str:
    """
    Return today's date as YYYY-MM-DD.
    """
    return datetime.now().strftime("%Y-%m-%d")


def get_current_weekday() -> str:
    """
    Return today's weekday in Chinese.
    """
    now = datetime.now()
    return WEEKDAY_MAP[now.strftime("%A")]


def get_current_lunar_date() -> str:
    """
    Return the lunar date in Chinese, preserving locale formatting and fallback text.
    """
    try:
        now = datetime.now()
        today_lunar = cnlunar.Lunar(now, godType="8char")
        return "%s年%s%s" % (
            today_lunar.lunarYearCn,
            today_lunar.lunarMonthCn[:-1],
            today_lunar.lunarDayCn,
        )
    except Exception:
        return "农历获取失败"


def get_current_time_info() -> tuple:
    """
    Return current time information.
    Returns: (time string, today's date, weekday, lunar date).
    """
    current_time = get_current_time()
    today_date = get_current_date()
    today_weekday = get_current_weekday()
    lunar_date = get_current_lunar_date()
    
    return current_time, today_date, today_weekday, lunar_date
