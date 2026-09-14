# -*- coding: utf-8 -*-
"""
================================================================
ربات گیم بات ریکوئست (روبیکا) - Nova-Country
================================================================
تغییرات نسخه Nova-Country نسبت به نسخه قبل:
  ۱) شانس برد در بازی‌ها به ۶۰٪ افزایش و شانس باخت به ۴۰٪ کاهش پیدا کرد
  ۲) سیستم کامل «کشورها» اضافه شد:
     • بیش از ۵۰ کشور قابل‌تصاحب (خرید کشور <اسم> — ۱۵۰,۰۰۰,۰۰۰ تومان)
     • هر کشور برای همیشه مال همون کاربره؛ هیچ‌وقت گرفته/عوض نمیشه
     • موشک (۱.۵ میلیون هرکدوم) برای حمله
     • کارخانه (۱ میلیون، روزی ۲۰۰ هزار سود) و مدرسه (۵۰۰ هزار، روزی
       ۱۰۰ هزار سود) - سودشون با «درآمد کشور» برداشت میشه
     • پایگاه (۱۲ میلیون هرکدوم) - روزی ۱۰ موشک مجانی تولید می‌کنه
     • پدافند (۱ میلیون هرکدوم) - هر واحد، یک موشک ورودی رو خنثی می‌کنه
     • تا ۴ ساعت بعد گرفتن کشور، نه میشه بهش حمله کرد نه خودش حمله کنه
     • جاسوسی (۳۰ میلیون) برای دیدن کامل وضعیت یک کشور دیگه
     • ترمیم کشور: بازسازی خسارت‌های واردشده با پرداخت هزینه
     • آتش‌بس ۱۲ ساعته (هر ۲۴ ساعت یک‌بار قابل‌فعال‌سازی)
     • رتبه کشورها: بهترین کشورهای بازی بر اساس ارزش کل
  ۳) خرید انبوه/حداکثر: «خرید ماینر 5» یا «خرید ماینر حداکثر»، همینطور
     برای موشک/کارخانه/مدرسه/پایگاه/پدافند
  ۴) راهنمای بازی کوتاه‌تر و مرتب‌تر شد (دستور «راهنما» و «راهنما کشورها»)
  ۵) پنل کامل مدیریت با دستورای ساده و جدا (بدون پیشوند اضافه، راحت‌تر
     حفظ میشه): دادن سکه/ماینر، تغییر لقب، هدیه، هدیه همگانی، سکه همگانی،
     دادن/آزاد کشور، تنظیم/تنظیمات، پیام همگانی — همه‌چیز بازی (حتی شانس
     برد) از همینجا قابل‌تغییره
  ۶) باگ «پیام همگانی» رفع شد: حالا به همه‌ی چت‌هایی که تابه‌حال با ربات
     پیام رد و بدل کردن میره (پی‌وی، گروه، کانال)، نه فقط کاربرهای تکی

نحوه اجرا:
  1) pip install requests
  2) پایین همین فایل (بخش config)، TOKEN و ADMIN_IDS رو پر کن
  3) python Nova-Country.py
"""

import os
import re
import random
import time
import threading
import sqlite3
import requests
from datetime import datetime


# ================================================================
# بخش ۱: تنظیمات
# ================================================================
class config:
    # توکن ربات: اول از Environment Variable خونده میشه (روی Render تنظیمش کن)
    TOKEN = os.environ.get("BOT_TOKEN", "CEBGCI0BGSSKQLDZJJYUZDVOTXZYERPTITDBBIQFNVFUKCELSBRTXFPKGLKMQAAM")

    # آیدی ادمین‌ها: می‌تونی توی Render با ADMIN_IDS به‌شکل «id1,id2» ست کنی
    _admin_ids_env = os.environ.get("ADMIN_IDS")
    ADMIN_IDS = (
        [x.strip() for x in _admin_ids_env.split(",") if x.strip()]
        if _admin_ids_env
        else ["u0Ih8kR014d3081e31c2cdd98fbe1e0b"]
    )

    BASE_URL = "https://botapi.rubika.ir/v3/{token}"
    DB_PATH = "game_bot.db"
    OFFSET_PATH = "offset.txt"

    # موجودی اولیه‌ای که هر کاربر جدید، همون لحظه اول باهاش وارد بازی میشه.
    # جایزه روزانه حذف شده و به‌جاش همین مبلغ ثابت رو کاربر همیشه با خودش داره.
    STARTING_BALANCE = 10_000_000

    WHEEL_MIN = 1_000_000
    WHEEL_MAX = 10_000_000
    WHEEL_COOLDOWN_HOURS = 24

    MINER_BASE_PRICE = 500_000
    MINER_PROFIT_PER_UNIT = 200_000
    MINER_COLLECT_COOLDOWN_HOURS = 1

    JOBS = {
        "کارگر": 50_000,
        "فروشنده": 100_000,
        "برنامه‌نویس": 200_000,
        "پزشک": 350_000,
        "مدیر شرکت": 500_000,
    }
    JOB_INCOME_COOLDOWN_HOURS = 1

    WIN_CHANCE = 0.6
    SLOT_MULTIPLIER_WEIGHTS = {
        2: 60,
        3: 30,
        4: 10,
    }

    # میانبرهای مبلغ - کاربر به‌جای تایپ عدد می‌تونه این کلمات رو بنویسه
    # و بر اساس موجودی/تعدادش محاسبه میشه (مثلاً: اسلات نصف)
    FRACTIONS = {
        "خمس": 1 / 5,
        "ربع": 1 / 4,
        "ثلث": 1 / 3,
        "نصف": 1 / 2,
        "کل": 1.0,
    }

    # میانبرهای واحد مبلغ - کاربر می‌تونه به‌جای صفرهای زیاد بنویسه
    # مثلاً: 1کا = 1,000  /  5میل = 5,000,000  /  2بیل = 2,000,000,000
    # پشتیبانی از اعشار هم هست: 1.5میل = 1,500,000
    UNITS = {
        "کا": 1_000,                      # هزار (k)
        "هزار": 1_000,
        "میل": 1_000_000,                 # میلیون (m)
        "میلیون": 1_000_000,
        "بیل": 1_000_000_000,             # میلیارد (b)
        "میلیارد": 1_000_000_000,
        "تیل": 1_000_000_000_000,         # تریلیون (t)
        "تریلیون": 1_000_000_000_000,
    }

    # ---------------- فروشگاه ماشین ----------------
    CARS = {
        "پراید": 5_000_000,
        "تیبا": 12_000_000,
        "پژو ۲۰۶": 15_000_000,
        "سمند": 20_000_000,
        "دنا پلاس": 35_000_000,
        "مزدا ۳": 80_000_000,
        "هیوندای سوناتا": 150_000_000,
        "بی‌ام‌و سری ۵": 400_000_000,
        "مرسدس بنز اس‌کلاس": 900_000_000,
        "لامبورگینی هوراکان": 3_000_000_000,
        "فراری اف۸": 4_500_000_000,
        "بوگاتی شیرون": 10_000_000_000,
    }

    # ---------------- فروشگاه خانه ----------------
    HOUSES = {
        "آپارتمان کوچک": 30_000_000,
        "آپارتمان متوسط": 80_000_000,
        "خانه ویلایی": 200_000_000,
        "پنت‌هاوس": 600_000_000,
        "ویلای شمال": 1_000_000_000,
        "عمارت لوکس": 3_000_000_000,
        "قصر": 8_000_000_000,
        "کاخ": 20_000_000_000,
    }

    # ---------------- فروشگاه گوشی ----------------
    PHONES = {
        "نوکیا ۱۱۰۰": 500_000,
        "نوکیا ۳۳۱۰": 800_000,
        "سامسونگ گلکسی J5": 3_000_000,
        "شیائومی ردمی نوت": 6_000_000,
        "سامسونگ گلکسی S23": 25_000_000,
        "آیفون ۱۳": 30_000_000,
        "آیفون ۱۵ پرو": 55_000_000,
        "آیفون ۱۶ پرو مکس": 80_000_000,
        "آیفون ۱۷ پرو مکس": 120_000_000,
    }

    # ================================================================
    # سیستم کشورها (جنگ/کشورگیری)
    # ================================================================
    COUNTRY_PRICE = 150_000_000

    MISSILE_PRICE = 1_500_000
    FACTORY_PRICE = 1_000_000
    FACTORY_INCOME = 200_000          # درآمد روزانه‌ی هر کارخانه
    BASE_PRICE = 12_000_000
    BASE_MISSILE_YIELD = 10           # هر پایگاه روزانه چندتا موشک تولید می‌کنه
    SCHOOL_PRICE = 500_000
    SCHOOL_INCOME = 100_000           # درآمد روزانه‌ی هر مدرسه
    DEFENSE_PRICE = 1_000_000         # هر پدافند، یک موشک ورودی رو خنثی می‌کنه

    # هزینه‌ی بازسازی هر واحدی که نابود بشه، دقیقاً برابر قیمت خریدشه
    # (کارخانه/مدرسه/پایگاه/پدافند) - جمعشون میشه هزینه‌ی «ترمیم کشور»

    ATTACK_COOLDOWN_HOURS = 4         # بعد از گرفتن کشور، تا این‌مدت نه میشه حمله کرد نه حمله شد
    COUNTRY_INCOME_COOLDOWN_HOURS = 24
    ESPIONAGE_PRICE = 30_000_000
    CEASEFIRE_HOURS = 12
    CEASEFIRE_COOLDOWN_HOURS = 24     # هر چندوقت یه‌بار میشه دوباره آتش‌بس زد

    # وقتی موشکی از سد پدافند رد بشه ولی کشور دیگه ساختمانی نداشته باشه
    # که نابودش کنه، همین مقدار به‌عنوان خسارت نقدی به کشور وارد میشه
    MISSILE_CASH_DAMAGE = 1_000_000

    # لیست کشورهای قابل‌خرید (بالای ۵۰ تا)
    COUNTRIES = [
        "ایران", "عراق", "ترکیه", "عربستان", "امارات", "قطر", "کویت", "عمان",
        "بحرین", "یمن", "سوریه", "لبنان", "اردن", "مصر", "لیبی", "الجزایر",
        "مراکش", "تونس", "سودان", "پاکستان", "افغانستان", "هند", "چین", "ژاپن",
        "کره جنوبی", "کره شمالی", "روسیه", "آلمان", "فرانسه", "انگلیس", "ایتالیا",
        "اسپانیا", "پرتغال", "هلند", "بلژیک", "سوئیس", "اتریش", "یونان", "لهستان",
        "اوکراین", "بلاروس", "سوئد", "نروژ", "فنلاند", "دانمارک", "ایسلند",
        "آمریکا", "کانادا", "مکزیک", "برزیل", "آرژانتین", "شیلی", "کلمبیا",
        "پرو", "ونزوئلا", "استرالیا", "نیوزیلند", "اندونزی", "مالزی", "تایلند",
        "ویتنام", "فیلیپین", "سنگاپور", "قزاقستان", "ازبکستان", "آذربایجان",
        "ارمنستان", "گرجستان",
    ]


# ================================================================
# بخش ۲: دیتابیس
# ================================================================
class db:
    _lock = threading.Lock()

    @staticmethod
    def get_conn():
        conn = sqlite3.connect(config.DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def init_db():
        with db._lock, db.get_conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    nickname TEXT UNIQUE,
                    balance INTEGER DEFAULT 0,
                    miners INTEGER DEFAULT 0,
                    job TEXT DEFAULT NULL,
                    last_wheel TEXT,
                    last_job_income TEXT,
                    last_miner_collect TEXT,
                    created_at TEXT
                )
                """
            )
            try:
                conn.execute("ALTER TABLE users ADD COLUMN banned INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                pass  # ستون از قبل وجود داره (دیتابیس قدیمی‌تر)
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS inventory (
                    user_id TEXT,
                    category TEXT,
                    item_name TEXT,
                    PRIMARY KEY (user_id, category, item_name)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS countries (
                    name TEXT PRIMARY KEY,
                    owner_id TEXT,
                    claimed_at TEXT,
                    missiles INTEGER DEFAULT 0,
                    factories INTEGER DEFAULT 0,
                    bases INTEGER DEFAULT 0,
                    schools INTEGER DEFAULT 0,
                    defenses INTEGER DEFAULT 0,
                    destroyed_factories INTEGER DEFAULT 0,
                    destroyed_schools INTEGER DEFAULT 0,
                    destroyed_bases INTEGER DEFAULT 0,
                    destroyed_defenses INTEGER DEFAULT 0,
                    cash_damage INTEGER DEFAULT 0,
                    last_income TEXT,
                    last_ceasefire TEXT,
                    ceasefire_until TEXT
                )
                """
            )
            for name in config.COUNTRIES:
                conn.execute(
                    "INSERT OR IGNORE INTO countries (name) VALUES (?)", (name,)
                )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chats (
                    chat_id TEXT PRIMARY KEY,
                    last_seen TEXT
                )
                """
            )
            conn.commit()

    @staticmethod
    def _now():
        return datetime.utcnow().isoformat()

    @staticmethod
    def get_user(user_id):
        with db._lock, db.get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            ).fetchone()
            if row:
                return dict(row)
            # کاربر جدید: لقب خالی می‌مونه (باید خودش با «لقب» انتخاب کنه)
            # و موجودی شروع طبق تنظیمات پر میشه.
            # نکته: اینجا مستقیم از conn باز شده استفاده می‌کنیم و
            # cfg()/get_setting() صدا زده نمیشه، چون قفل (db._lock) از قبل
            # گرفته شده و اون توابع دوباره سعی می‌کنن قفلش کنن (دِدلاک).
            setting_row = conn.execute(
                "SELECT value FROM settings WHERE key = 'STARTING_BALANCE'"
            ).fetchone()
            starting_balance = (
                int(setting_row["value"]) if setting_row else config.STARTING_BALANCE
            )
            conn.execute(
                """
                INSERT INTO users (user_id, nickname, balance, miners, created_at)
                VALUES (?, NULL, ?, 0, ?)
                """,
                (user_id, starting_balance, db._now()),
            )
            conn.commit()
            row = conn.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            ).fetchone()
            return dict(row)

    @staticmethod
    def get_user_by_nickname(nickname):
        with db._lock, db.get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE nickname = ?", (nickname,)
            ).fetchone()
            return dict(row) if row else None

    @staticmethod
    def set_nickname(user_id, nickname):
        with db._lock, db.get_conn() as conn:
            exists = conn.execute(
                "SELECT 1 FROM users WHERE nickname = ? AND user_id != ?",
                (nickname, user_id),
            ).fetchone()
            if exists:
                return False
            conn.execute(
                "UPDATE users SET nickname = ? WHERE user_id = ?",
                (nickname, user_id),
            )
            conn.commit()
            return True

    @staticmethod
    def set_banned(user_id, banned):
        with db._lock, db.get_conn() as conn:
            conn.execute(
                "UPDATE users SET banned = ? WHERE user_id = ?",
                (1 if banned else 0, user_id),
            )
            conn.commit()

    @staticmethod
    def update_balance(user_id, delta):
        with db._lock, db.get_conn() as conn:
            conn.execute(
                "UPDATE users SET balance = MAX(0, balance + ?) WHERE user_id = ?",
                (delta, user_id),
            )
            conn.commit()
            row = conn.execute(
                "SELECT balance FROM users WHERE user_id = ?", (user_id,)
            ).fetchone()
            return row["balance"]

    @staticmethod
    def set_balance(user_id, amount):
        with db._lock, db.get_conn() as conn:
            conn.execute(
                "UPDATE users SET balance = ? WHERE user_id = ?", (amount, user_id)
            )
            conn.commit()

    @staticmethod
    def update_miners(user_id, delta):
        with db._lock, db.get_conn() as conn:
            conn.execute(
                "UPDATE users SET miners = MAX(0, miners + ?) WHERE user_id = ?",
                (delta, user_id),
            )
            conn.commit()
            row = conn.execute(
                "SELECT miners FROM users WHERE user_id = ?", (user_id,)
            ).fetchone()
            return row["miners"]

    @staticmethod
    def set_job(user_id, job_name):
        with db._lock, db.get_conn() as conn:
            conn.execute(
                "UPDATE users SET job = ? WHERE user_id = ?", (job_name, user_id)
            )
            conn.commit()

    @staticmethod
    def set_timestamp_field(user_id, field_name, value=None):
        value = value or db._now()
        with db._lock, db.get_conn() as conn:
            conn.execute(
                f"UPDATE users SET {field_name} = ? WHERE user_id = ?",
                (value, user_id),
            )
            conn.commit()

    @staticmethod
    def hours_since(iso_timestamp):
        if not iso_timestamp:
            return float("inf")
        try:
            then = datetime.fromisoformat(iso_timestamp)
        except ValueError:
            return float("inf")
        delta = datetime.utcnow() - then
        return delta.total_seconds() / 3600.0

    @staticmethod
    def is_same_utc_day(iso_timestamp):
        if not iso_timestamp:
            return False
        try:
            then = datetime.fromisoformat(iso_timestamp)
        except ValueError:
            return False
        now = datetime.utcnow()
        return then.date() == now.date()

    @staticmethod
    def top_richest(limit=10):
        with db._lock, db.get_conn() as conn:
            rows = conn.execute(
                "SELECT nickname, balance, miners FROM users "
                "WHERE nickname IS NOT NULL ORDER BY balance DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    def all_user_ids():
        with db._lock, db.get_conn() as conn:
            rows = conn.execute("SELECT user_id FROM users").fetchall()
            return [r["user_id"] for r in rows]

    @staticmethod
    def add_item(user_id, category, item_name):
        """دارایی جدید (ماشین/خانه/گوشی) رو ثبت می‌کنه.
        اگه از قبل داشت، False برمی‌گردونه."""
        with db._lock, db.get_conn() as conn:
            exists = conn.execute(
                "SELECT 1 FROM inventory WHERE user_id = ? AND category = ? AND item_name = ?",
                (user_id, category, item_name),
            ).fetchone()
            if exists:
                return False
            conn.execute(
                "INSERT INTO inventory (user_id, category, item_name) VALUES (?, ?, ?)",
                (user_id, category, item_name),
            )
            conn.commit()
            return True

    @staticmethod
    def get_items(user_id, category):
        with db._lock, db.get_conn() as conn:
            rows = conn.execute(
                "SELECT item_name FROM inventory WHERE user_id = ? AND category = ?",
                (user_id, category),
            ).fetchall()
            return [r["item_name"] for r in rows]

    # ------------------------------------------------------------------
    # کشورها
    # ------------------------------------------------------------------

    @staticmethod
    def get_country(name):
        with db._lock, db.get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM countries WHERE name = ?", (name,)
            ).fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_country_by_owner(user_id):
        with db._lock, db.get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM countries WHERE owner_id = ?", (user_id,)
            ).fetchone()
            return dict(row) if row else None

    @staticmethod
    def list_unclaimed_countries():
        with db._lock, db.get_conn() as conn:
            rows = conn.execute(
                "SELECT name FROM countries WHERE owner_id IS NULL ORDER BY name"
            ).fetchall()
            return [r["name"] for r in rows]

    @staticmethod
    def list_owned_countries():
        with db._lock, db.get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM countries WHERE owner_id IS NOT NULL"
            ).fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    def claim_country(name, user_id):
        """فقط اگه کشور آزاد باشه، تصاحبش می‌کنه. برای همیشه مال همون کاربر می‌مونه."""
        with db._lock, db.get_conn() as conn:
            row = conn.execute(
                "SELECT owner_id FROM countries WHERE name = ?", (name,)
            ).fetchone()
            if row is None or row["owner_id"] is not None:
                return False
            conn.execute(
                "UPDATE countries SET owner_id = ?, claimed_at = ? WHERE name = ?",
                (user_id, db._now(), name),
            )
            conn.commit()
            return True

    @staticmethod
    def admin_force_claim_country(name, user_id):
        """فقط برای ادمین: کشور رو بدون شرط به یه کاربر میده (حتی اگه قبلاً مال یکی دیگه بوده)."""
        with db._lock, db.get_conn() as conn:
            row = conn.execute("SELECT 1 FROM countries WHERE name = ?", (name,)).fetchone()
            if row is None:
                return False
            conn.execute(
                "UPDATE countries SET owner_id = ?, claimed_at = ? WHERE name = ?",
                (user_id, db._now(), name),
            )
            conn.commit()
            return True

    @staticmethod
    def admin_reset_country(name):
        """فقط برای ادمین: کشور رو کاملاً به حالت آزاد و صفر برمی‌گردونه."""
        with db._lock, db.get_conn() as conn:
            row = conn.execute("SELECT 1 FROM countries WHERE name = ?", (name,)).fetchone()
            if row is None:
                return False
            conn.execute(
                """
                UPDATE countries SET
                    owner_id = NULL, claimed_at = NULL,
                    missiles = 0, factories = 0, bases = 0, schools = 0, defenses = 0,
                    destroyed_factories = 0, destroyed_schools = 0,
                    destroyed_bases = 0, destroyed_defenses = 0,
                    cash_damage = 0, last_income = NULL,
                    last_ceasefire = NULL, ceasefire_until = NULL
                WHERE name = ?
                """,
                (name,),
            )
            conn.commit()
            return True

    @staticmethod
    def adjust_country(name, **deltas):
        """تعدادی از ستون‌های عددی کشور رو با delta جمع می‌زنه (نمی‌تونه منفی بشه)."""
        if not deltas:
            return
        with db._lock, db.get_conn() as conn:
            for field, delta in deltas.items():
                conn.execute(
                    f"UPDATE countries SET {field} = MAX(0, {field} + ?) WHERE name = ?",
                    (delta, name),
                )
            conn.commit()

    @staticmethod
    def set_country_field(name, field, value):
        with db._lock, db.get_conn() as conn:
            conn.execute(
                f"UPDATE countries SET {field} = ? WHERE name = ?", (value, name)
            )
            conn.commit()

    @staticmethod
    def get_user_nickname_map(user_ids):
        if not user_ids:
            return {}
        with db._lock, db.get_conn() as conn:
            q = f"SELECT user_id, nickname FROM users WHERE user_id IN ({','.join('?' * len(user_ids))})"
            rows = conn.execute(q, tuple(user_ids)).fetchall()
            return {r["user_id"]: r["nickname"] for r in rows}

    # ------------------------------------------------------------------
    # تنظیمات قابل‌دستکاری توسط ادمین (اورراید مقادیر پیش‌فرض config)
    # ------------------------------------------------------------------

    @staticmethod
    def get_setting(key):
        with db._lock, db.get_conn() as conn:
            row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
            return row["value"] if row else None

    @staticmethod
    def set_setting(key, value):
        with db._lock, db.get_conn() as conn:
            conn.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, str(value)),
            )
            conn.commit()

    @staticmethod
    def all_settings():
        with db._lock, db.get_conn() as conn:
            rows = conn.execute("SELECT key, value FROM settings").fetchall()
            return {r["key"]: r["value"] for r in rows}

    # ------------------------------------------------------------------
    # چت‌ها (برای پیام همگانی: پی‌وی + گروه + کانال)
    # ------------------------------------------------------------------

    @staticmethod
    def record_chat(chat_id):
        with db._lock, db.get_conn() as conn:
            conn.execute(
                "INSERT INTO chats (chat_id, last_seen) VALUES (?, ?) "
                "ON CONFLICT(chat_id) DO UPDATE SET last_seen = excluded.last_seen",
                (chat_id, db._now()),
            )
            conn.commit()

    @staticmethod
    def all_chat_ids():
        with db._lock, db.get_conn() as conn:
            rows = conn.execute("SELECT chat_id FROM chats").fetchall()
            return [r["chat_id"] for r in rows]


# ------------------------------------------------------------------
# تنظیمات قابل‌دستکاری با پنل ادمین (بدون نیاز به تغییر کد/ری‌استارت)
# ------------------------------------------------------------------

TUNABLE_SETTINGS = [
    "STARTING_BALANCE", "WHEEL_MIN", "WHEEL_MAX", "WHEEL_COOLDOWN_HOURS",
    "MINER_BASE_PRICE", "MINER_PROFIT_PER_UNIT", "MINER_COLLECT_COOLDOWN_HOURS",
    "JOB_INCOME_COOLDOWN_HOURS", "WIN_CHANCE",
    "COUNTRY_PRICE", "MISSILE_PRICE", "FACTORY_PRICE", "FACTORY_INCOME",
    "BASE_PRICE", "BASE_MISSILE_YIELD", "SCHOOL_PRICE", "SCHOOL_INCOME",
    "DEFENSE_PRICE", "ATTACK_COOLDOWN_HOURS", "COUNTRY_INCOME_COOLDOWN_HOURS",
    "ESPIONAGE_PRICE", "CEASEFIRE_HOURS", "CEASEFIRE_COOLDOWN_HOURS",
    "MISSILE_CASH_DAMAGE",
]


def cfg(name):
    """
    مقدار یه تنظیم رو برمی‌گردونه: اگه ادمین از پنل عوضش کرده باشه همون
    مقدار جدید، وگرنه مقدار پیش‌فرضی که توی کلاس config نوشته شده.
    """
    default = getattr(config, name)
    override = db.get_setting(name)
    if override is None:
        return default
    try:
        if isinstance(default, float):
            return float(override)
        return int(override)
    except (TypeError, ValueError):
        return default


# ================================================================
# بخش ۳: ارتباط با API روبیکا
# ================================================================
class api:
    @staticmethod
    def _url(method):
        return config.BASE_URL.format(token=config.TOKEN) + "/" + method

    @staticmethod
    def send_message(chat_id, text, inline_keypad=None, chat_keypad=None,
                      chat_keypad_type=None, reply_to_message_id=None):
        data = {
            "chat_id": chat_id,
            "text": text,
        }
        if inline_keypad:
            data["inline_keypad"] = inline_keypad
        if chat_keypad:
            data["chat_keypad"] = chat_keypad
        if chat_keypad_type:
            data["chat_keypad_type"] = chat_keypad_type
        if reply_to_message_id:
            data["reply_to_message_id"] = reply_to_message_id

        try:
            resp = requests.post(api._url("sendMessage"), json=data, timeout=15)
            return resp.json()
        except requests.RequestException as e:
            print(f"[خطا در ارسال پیام] {e}")
            return None

    @staticmethod
    def get_updates(offset_id=None, limit=100):
        data = {"limit": limit}
        if offset_id:
            data["offset_id"] = offset_id
        try:
            resp = requests.post(api._url("getUpdates"), json=data, timeout=20)
            return resp.json()
        except requests.RequestException as e:
            print(f"[خطا در دریافت پیام‌ها] {e}")
            return None

    @staticmethod
    def get_me():
        try:
            resp = requests.post(api._url("getMe"), timeout=15)
            return resp.json()
        except requests.RequestException as e:
            print(f"[خطا در getMe] {e}")
            return None


# ================================================================
# بخش ۴: منطق اصلی ربات
# ================================================================

PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
ARABIC_DIGITS = "٠١٢٣٤٥٦٧٨٩"


def normalize_digits(text):
    for i, ch in enumerate(PERSIAN_DIGITS):
        text = text.replace(ch, str(i))
    for i, ch in enumerate(ARABIC_DIGITS):
        text = text.replace(ch, str(i))
    return text


def fmt(n):
    return f"{n:,}"


UNIT_PATTERN = re.compile(r"^(-?\d+(?:\.\d+)?)\s*([آ-ی]+)$")


def parse_int(text):
    text = normalize_digits(text).replace(",", "").replace("٫", ".").strip()
    if text.lstrip("-").isdigit():
        return int(text)

    # پشتیبانی از میانبر واحد: 1کا، 5 میل، 2.5بیل و ...
    m = UNIT_PATTERN.match(text)
    if m:
        number_part, unit_part = m.groups()
        multiplier = config.UNITS.get(unit_part.strip())
        if multiplier:
            try:
                return int(float(number_part) * multiplier)
            except ValueError:
                return None
    return None


def resolve_amount(text, base):
    """
    مبلغ رو برمی‌گردونه. اگه کاربر به‌جای عدد، یکی از کلمات
    خمس/ربع/ثلث/نصف/کل رو نوشته باشه، بر اساس «base» (مثلاً موجودی
    یا تعداد ماینر) محاسبه میشه. مثال: «اسلات نصف» یعنی نصف موجودی.
    """
    text = text.strip()
    if text in config.FRACTIONS:
        return int(base * config.FRACTIONS[text])
    return parse_int(text)


def remaining_hours_text(hours_passed, cooldown_hours):
    remaining = cooldown_hours - hours_passed
    if remaining <= 0:
        return None
    h = int(remaining)
    m = int((remaining - h) * 60)
    return f"{h} ساعت و {m} دقیقه"


# ------------------------------------------------------------------
# ابزار ریپلای: هر جواب ربات روی همون پیامِ دستور ریپلای می‌زنه
# ------------------------------------------------------------------

def reply(chat_id, message_id, text):
    api.send_message(chat_id, text, reply_to_message_id=message_id)


# ------------------------------------------------------------------
# قالب‌های ظاهری (قاب‌ها) برای زیبا شدن پیام‌ها
# ------------------------------------------------------------------

BOX_TOP = "╔══════════════════════╗"
BOX_BOTTOM = "╚══════════════════════╝"
SEP = "━━━━━━━━━━━━━━━━"

SLOT_BOX_TOP = "┏━━━━━━━━━━━━┓"
SLOT_BOX_BOTTOM = "┗━━━━━━━━━━━━┛"
SLOT_SEP = "━━━━━━━━━━━━"

DICE_BOX_TOP = "┏━━━━━━┓"
DICE_BOX_BOTTOM = "┗━━━━━━┛"

KEYCAP = {4: "4️⃣", 5: "5️⃣", 6: "6️⃣", 7: "7️⃣", 8: "8️⃣", 9: "9️⃣", 10: "🔟"}


def card(title, lines, footer=None):
    """یه پیام با قاب و جداکننده می‌سازه (برای پیام‌های اقتصادی/پروفایل/خطا)."""
    parts = [BOX_TOP, f"   {title}", BOX_BOTTOM, SEP]
    parts.extend(lines)
    if footer:
        parts.append(SEP)
        parts.append(footer)
    return "\n".join(parts)


def error_card(message, tip=None):
    return card("❌ خطا", [f"💔 {message}"], tip)


# ------------------------------------------------------------------
# دستورات عمومی
# ------------------------------------------------------------------

def cmd_help(user, args, chat_id, message_id):
    text = (
        f"{BOX_TOP}\n   📜 راهنمای بازی\n{BOX_BOTTOM}\n"
        f"{SEP}\n"
        "💰 اقتصاد\n"
        "موجودی | گردونه\n\n"
        "⛏ ماینر\n"
        "ماینر | خرید ماینر <تعداد/حداکثر> | ماینر بگیر | انتقال ماینر <لقب> <تعداد>\n\n"
        "💼 شغل\n"
        "مشاغل | شغل <نام> | درآمد\n\n"
        "🎰 شرط‌بندی\n"
        "اسلات/تاس/شیر یا خط <مبلغ>\n"
        "💡 مبلغ: عدد، یا خمس/ربع/ثلث/نصف/کل، یا با کا/میل/بیل/تیل (مثل 5میل)\n\n"
        "🚗 فروشگاه\n"
        "ماشین‌ها | خانه‌ها | گوشی‌ها — لیست و قیمت\n"
        "خرید ماشین/خانه/گوشی <اسم> | ماشین‌های من / خانه‌های من / گوشی‌های من\n\n"
        "👤 حساب\n"
        "لقب <اسم> | اطلاعات <لقب> | انتقال سکه <لقب> <مبلغ> | رتبه\n\n"
        "🌍 برای سیستم کشورها: راهنما کشورها\n"
        "• سازنده — آیدی سازنده\n"
        f"{SEP}"
    )
    reply(chat_id, message_id, text)


def cmd_help_countries(user, args, chat_id, message_id):
    text = (
        f"{BOX_TOP}\n   🌍 راهنمای کشورها\n{BOX_BOTTOM}\n"
        f"{SEP}\n"
        f"کشور ها | کشورهای گرفته شده | خرید کشور <اسم> ({fmt(cfg('COUNTRY_PRICE'))})\n"
        "کشور من — وضعیت کامل\n\n"
        "🏗 ساخت‌وساز (هرکدوم می‌تونی عدد یا «حداکثر» بدی)\n"
        f"خرید موشک <تعداد> — {fmt(cfg('MISSILE_PRICE'))}\n"
        f"خرید کارخانه <تعداد> — {fmt(cfg('FACTORY_PRICE'))}، روزی {fmt(cfg('FACTORY_INCOME'))}\n"
        f"خرید مدرسه <تعداد> — {fmt(cfg('SCHOOL_PRICE'))}، روزی {fmt(cfg('SCHOOL_INCOME'))}\n"
        f"خرید پایگاه <تعداد> — {fmt(cfg('BASE_PRICE'))}، روزی {cfg('BASE_MISSILE_YIELD')} موشک\n"
        f"خرید پدافند <تعداد> — {fmt(cfg('DEFENSE_PRICE'))}، هرکدوم ۱ موشک خنثی می‌کنه\n\n"
        "⚔️ جنگ\n"
        "درآمد کشور | حمله <کشور> <تعداد موشک> | ترمیم کشور\n"
        f"جاسوسی <کشور> ({fmt(cfg('ESPIONAGE_PRICE'))}) | آتش بس ({cfg('CEASEFIRE_HOURS')} ساعت) | رتبه کشورها\n\n"
        f"💡 تا {cfg('ATTACK_COOLDOWN_HOURS')} ساعت بعد گرفتن کشور، نه حمله می‌کنی نه حمله می‌بینی\n"
        f"{SEP}"
    )
    reply(chat_id, message_id, text)


def _assets_lines(user_id):
    """به‌جای تعداد، اسم دقیق دارایی‌هایی که فرد داره رو برمی‌گردونه."""
    cars = db.get_items(user_id, "ماشین")
    houses = db.get_items(user_id, "خانه")
    phones = db.get_items(user_id, "گوشی")
    return [
        f"🚗 ماشین: {'، '.join(cars) if cars else 'ندارد'}",
        f"🏠 خانه: {'، '.join(houses) if houses else 'ندارد'}",
        f"📱 گوشی: {'، '.join(phones) if phones else 'ندارد'}",
    ]


def cmd_balance(user, args, chat_id, message_id):
    text = card(
        "💰 کیف پول شما",
        [
            f"👤 لقب: {user['nickname']}",
            f"🏦 موجودی: {fmt(user['balance'])} تومان",
            f"⛏️ ماینرها: {user['miners']}",
            f"💼 شغل: {user['job'] or 'ندارد'}",
            *_assets_lines(user["user_id"]),
        ],
    )
    reply(chat_id, message_id, text)


def cmd_nickname(user, args, chat_id, message_id):
    if not args:
        reply(chat_id, message_id, error_card(
            "لقب جدید رو بعد از دستور بنویس.", "مثال: لقب علی_شاه"
        ))
        return
    new_nick = " ".join(args).strip()
    if len(new_nick) < 2 or len(new_nick) > 20:
        reply(chat_id, message_id, error_card("لقب باید بین ۲ تا ۲۰ کاراکتر باشه."))
        return
    ok = db.set_nickname(user["user_id"], new_nick)
    if ok:
        text = card("👑 تغییر لقب", [f"✅ لقب جدیدت: «{new_nick}»"])
        reply(chat_id, message_id, text)
    else:
        reply(chat_id, message_id, error_card("این لقب قبلاً توسط شخص دیگری انتخاب شده."))


def cmd_profile(user, args, chat_id, message_id):
    if not args:
        reply(chat_id, message_id, error_card(
            "لقب مورد نظر رو بنویس.", "مثال: اطلاعات علی_شاه"
        ))
        return
    nickname = " ".join(args).strip()
    target = db.get_user_by_nickname(nickname)
    if not target:
        reply(chat_id, message_id, error_card("کاربری با این لقب پیدا نشد."))
        return
    cars = len(db.get_items(target["user_id"], "ماشین"))
    houses = len(db.get_items(target["user_id"], "خانه"))
    phones = len(db.get_items(target["user_id"], "گوشی"))
    text = card(
        f"👤 اطلاعات {target['nickname']}",
        [
            f"👑 لقب: {target['nickname']}",
            f"🏦 موجودی: {fmt(target['balance'])} تومان",
            f"⛏️ ماینرها: {target['miners']}",
            f"💼 شغل: {target['job'] or 'ندارد'}",
            *_assets_lines(target["user_id"]),
        ],
    )
    reply(chat_id, message_id, text)


def cmd_rank(user, args, chat_id, message_id):
    top = db.top_richest(10)
    if not top:
        reply(chat_id, message_id, card("🏆 ثروتمندترین‌ها", ["هنوز کسی توی بازی ثبت نشده."]))
        return
    medals = ["🥇", "🥈", "🥉"]
    lines = []
    for i, row in enumerate(top):
        rank = i + 1
        prefix = medals[i] if i < 3 else KEYCAP.get(rank, f"{rank}.")
        lines.append(f"{prefix} {row['nickname']} — {fmt(row['balance'])} تومان")
    text = card("🏆 ثروتمندترین‌ها", lines, "💡 برای بالا رفتن، بازی کن!")
    reply(chat_id, message_id, text)


WHEEL_ICONS = ["💰 💰 💰", "💎 💎 💎", "🍀 🍀 🍀", "🎉 🎉 🎉"]


def cmd_wheel(user, args, chat_id, message_id):
    hours = db.hours_since(user["last_wheel"])
    remaining = remaining_hours_text(hours, cfg("WHEEL_COOLDOWN_HOURS"))
    if remaining:
        text = card(
            "⏰ صبر کن!",
            [
                "🎡 گردونه رو امروز چرخوندی",
                f"⏰ زمان باقی‌مونده: {remaining}",
            ],
            "💡 فردا دوباره بیا",
        )
        reply(chat_id, message_id, text)
        return
    amount = random.randint(cfg("WHEEL_MIN"), cfg("WHEEL_MAX"))
    amount = round(amount / 100_000) * 100_000
    new_balance = db.update_balance(user["user_id"], amount)
    db.set_timestamp_field(user["user_id"], "last_wheel")
    icon_row = random.choice(WHEEL_ICONS)
    text = (
        f"🎡 گردونه شانس\n"
        f"{SLOT_BOX_TOP}\n"
        f"┃   {icon_row}  ┃\n"
        f"{SLOT_BOX_BOTTOM}\n"
        f"🎉 گردونه چرخید...\n"
        f"{SLOT_SEP}\n"
        f"🎁 جایزه: {fmt(amount)} تومان\n"
        f"{SLOT_SEP}\n"
        f"🏦 موجودی جدید: {fmt(new_balance)}"
    )
    reply(chat_id, message_id, text)


# ------------------------------------------------------------------
# ماینر
# ------------------------------------------------------------------

def cmd_miner_status(user, args, chat_id, message_id):
    profit_per_collect = user["miners"] * cfg("MINER_PROFIT_PER_UNIT")
    next_price = cfg("MINER_BASE_PRICE") * (user["miners"] + 1)
    text = card(
        "⛏️ ماینرهای شما",
        [
            f"⛏️ تعداد ماینر: {user['miners']}",
            f"💵 سود هر برداشت: {fmt(profit_per_collect)} تومان",
            f"🛒 قیمت ماینر بعدی: {fmt(next_price)} تومان",
        ],
        f"⏱ هر {cfg("MINER_COLLECT_COOLDOWN_HOURS")} ساعت یک‌بار می‌تونی سود بگیری («ماینر بگیر»)",
    )
    reply(chat_id, message_id, text)


def cmd_miner_buy(user, args, chat_id, message_id):
    base_price = cfg("MINER_BASE_PRICE")
    balance = user["balance"]
    miners = user["miners"]
    arg0 = args[0] if args else None
    max_mode = arg0 in ("حداکثر", "max")
    if max_mode:
        target_count = None
    else:
        target_count = parse_int(arg0) if arg0 else 1
        if target_count is None or target_count <= 0:
            reply(chat_id, message_id, error_card("تعداد ماینر رو درست وارد کن.", "یا بنویس: حداکثر"))
            return

    bought = 0
    total_cost = 0
    while target_count is None or bought < target_count:
        next_price = base_price * (miners + 1)
        if balance < next_price:
            break
        balance -= next_price
        total_cost += next_price
        miners += 1
        bought += 1

    if bought == 0:
        next_price = base_price * (user["miners"] + 1)
        text = card(
            "❌ خرید ناموفق",
            [
                "💔 سکه کافی نداری!",
                f"💵 قیمت ماینر بعدی: {fmt(next_price)} تومان",
                f"🏦 موجودی تو: {fmt(user['balance'])}",
            ],
            "💡 برو شرط‌بندی کن یا گردونه رو بچرخون تا سکه جمع کنی!",
        )
        reply(chat_id, message_id, text)
        return
    new_balance = db.update_balance(user["user_id"], -total_cost)
    new_count = db.update_miners(user["user_id"], bought)
    text = card(
        "🛒 خرید موفق",
        [f"⛏️ {bought} ماینر خریدی!", f"💸 هزینه‌ی کل: {fmt(total_cost)} تومان"],
        f"🏦 موجودی جدید: {fmt(new_balance)}\n⛏️ تعداد ماینر: {new_count}",
    )
    reply(chat_id, message_id, text)


def cmd_miner_collect(user, args, chat_id, message_id):
    if user["miners"] <= 0:
        reply(chat_id, message_id, error_card(
            "هنوز هیچ ماینری نداری.", "اول با «خرید ماینر» یکی بخر."
        ))
        return
    hours = db.hours_since(user["last_miner_collect"])
    remaining = remaining_hours_text(hours, cfg("MINER_COLLECT_COOLDOWN_HOURS"))
    if remaining:
        text = card(
            "⏰ صبر کن!",
            [
                "⛏️ سود ماینرهاتو گرفتی",
                f"⏰ زمان باقی‌مونده: {remaining}",
            ],
        )
        reply(chat_id, message_id, text)
        return
    profit = user["miners"] * cfg("MINER_PROFIT_PER_UNIT")
    new_balance = db.update_balance(user["user_id"], profit)
    db.set_timestamp_field(user["user_id"], "last_miner_collect")
    text = card(
        "⛏️ درآمد ماینرها",
        [
            f"⛏️ ماینرها: {user['miners']}",
            f"💵 درآمد: {fmt(profit)} تومان",
        ],
        f"🏦 موجودی جدید: {fmt(new_balance)}\n⏰ درآمد بعدی: {cfg("MINER_COLLECT_COOLDOWN_HOURS")} ساعت دیگه",
    )
    reply(chat_id, message_id, text)


def cmd_miner_transfer(user, args, chat_id, message_id):
    if len(args) < 2:
        reply(chat_id, message_id, error_card(
            "فرمت درست: انتقال ماینر <لقب> <تعداد>"
        ))
        return
    amount = resolve_amount(args[-1], user["miners"])
    nickname = " ".join(args[:-1]).strip()
    if amount is None or amount <= 0:
        reply(chat_id, message_id, error_card("تعداد ماینر رو درست وارد کن.", "می‌تونی از خمس/ربع/ثلث/نصف/کل یا کا/میل/بیل/تیل هم استفاده کنی"))
        return
    target = db.get_user_by_nickname(nickname)
    if not target:
        reply(chat_id, message_id, error_card("کاربری با این لقب پیدا نشد."))
        return
    if target["user_id"] == user["user_id"]:
        reply(chat_id, message_id, error_card("نمی‌تونی به خودت ماینر انتقال بدی."))
        return
    if user["miners"] < amount:
        text = card(
            "❌ انتقال ناموفق",
            [f"💔 تو فقط {user['miners']} ماینر داری.", f"⛏️ تعداد درخواستی: {amount}"],
        )
        reply(chat_id, message_id, text)
        return
    db.update_miners(user["user_id"], -amount)
    db.update_miners(target["user_id"], amount)
    text = card(
        "📤 انتقال ماینر موفق",
        [f"👤 گیرنده: {target['nickname']}", f"⛏️ تعداد: {amount}"],
    )
    reply(chat_id, message_id, text)


# ------------------------------------------------------------------
# شغل و درآمد
# ------------------------------------------------------------------

def cmd_jobs_list(user, args, chat_id, message_id):
    lines = []
    for name, income in config.JOBS.items():
        lines.append(f"• {name} — {fmt(income)} تومان")
    text = card("💼 لیست شغل‌ها", lines, "برای انتخاب شغل بنویس: شغل <نام شغل>")
    reply(chat_id, message_id, text)


def cmd_choose_job(user, args, chat_id, message_id):
    if not args:
        reply(chat_id, message_id, error_card(
            "اسم شغل رو بنویس.", "برای دیدن لیست شغل‌ها: مشاغل"
        ))
        return
    job_name = " ".join(args).strip()
    if job_name not in config.JOBS:
        reply(chat_id, message_id, error_card(
            "همچین شغلی وجود نداره.", "لیست شغل‌ها: مشاغل"
        ))
        return
    db.set_job(user["user_id"], job_name)
    text = card("✅ شغل انتخاب شد", [f"💼 شغل جدیدت: «{job_name}»"])
    reply(chat_id, message_id, text)


def cmd_job_income(user, args, chat_id, message_id):
    if not user["job"]:
        reply(chat_id, message_id, error_card(
            "هنوز شغلی انتخاب نکردی.", "لیست شغل‌ها: مشاغل"
        ))
        return
    hours = db.hours_since(user["last_job_income"])
    remaining = remaining_hours_text(hours, cfg("JOB_INCOME_COOLDOWN_HOURS"))
    if remaining:
        text = card(
            "⏰ صبر کن!",
            [
                "💼 درآمد شغلتو گرفتی",
                f"⏰ زمان باقی‌مونده: {remaining}",
            ],
        )
        reply(chat_id, message_id, text)
        return
    income = config.JOBS[user["job"]]
    new_balance = db.update_balance(user["user_id"], income)
    db.set_timestamp_field(user["user_id"], "last_job_income")
    text = card(
        "💼 درآمد شغلی",
        [
            f"💼 شغل: {user['job']}",
            f"💵 درآمد: {fmt(income)} تومان",
        ],
        f"🏦 موجودی جدید: {fmt(new_balance)}\n⏰ درآمد بعدی: {cfg("JOB_INCOME_COOLDOWN_HOURS")} ساعت دیگه",
    )
    reply(chat_id, message_id, text)


# ------------------------------------------------------------------
# انتقال سکه
# ------------------------------------------------------------------

def cmd_transfer_coin(user, args, chat_id, message_id):
    if len(args) < 2:
        reply(chat_id, message_id, error_card("فرمت درست: انتقال سکه <لقب> <مبلغ>"))
        return
    amount = resolve_amount(args[-1], user["balance"])
    nickname = " ".join(args[:-1]).strip()
    if amount is None or amount <= 0:
        reply(chat_id, message_id, error_card("مبلغ رو درست وارد کن.", "می‌تونی از خمس/ربع/ثلث/نصف/کل یا کا/میل/بیل/تیل هم استفاده کنی"))
        return
    target = db.get_user_by_nickname(nickname)
    if not target:
        reply(chat_id, message_id, error_card("کاربری با این لقب پیدا نشد."))
        return
    if target["user_id"] == user["user_id"]:
        reply(chat_id, message_id, error_card("نمی‌تونی به خودت سکه انتقال بدی."))
        return
    if user["balance"] < amount:
        text = card(
            "❌ انتقال ناموفق",
            [
                "💔 سکه کافی نداری!",
                f"🏦 موجودی تو: {fmt(user['balance'])}",
                f"💵 مبلغ درخواستی: {fmt(amount)}",
            ],
        )
        reply(chat_id, message_id, text)
        return
    new_balance = db.update_balance(user["user_id"], -amount)
    db.update_balance(target["user_id"], amount)
    text = card(
        "📤 انتقال موفق",
        [f"👤 گیرنده: {target['nickname']}", f"💵 مبلغ: {fmt(amount)} تومان"],
        f"🏦 موجودی تو: {fmt(new_balance)}",
    )
    reply(chat_id, message_id, text)


# ------------------------------------------------------------------
# فروشگاه (ماشین، خانه، گوشی)
# ------------------------------------------------------------------

CATEGORY_CATALOGS = {
    "ماشین": config.CARS,
    "خانه": config.HOUSES,
    "گوشی": config.PHONES,
}
CATEGORY_EMOJI = {"ماشین": "🚗", "خانه": "🏠", "گوشی": "📱"}


def cmd_shop_list(category, chat_id, message_id):
    catalog = CATEGORY_CATALOGS[category]
    emoji = CATEGORY_EMOJI[category]
    lines = [f"• {name} — {fmt(price)} تومان" for name, price in catalog.items()]
    text = card(
        f"{emoji} فروشگاه {category}",
        lines,
        f"برای خرید بنویس: خرید {category} <اسم دقیق>",
    )
    reply(chat_id, message_id, text)


def cmd_shop_buy(user, category, args, chat_id, message_id):
    catalog = CATEGORY_CATALOGS[category]
    emoji = CATEGORY_EMOJI[category]
    if not args:
        reply(chat_id, message_id, error_card(
            f"اسم {category} رو بنویس.", f"لیست قیمت‌ها: {category} ها"
        ))
        return
    item_name = " ".join(args).strip()
    if item_name not in catalog:
        reply(chat_id, message_id, error_card(
            f"همچین {category}ی توی فروشگاه نیست.", f"لیست قیمت‌ها: {category} ها"
        ))
        return
    price = catalog[item_name]
    if user["balance"] < price:
        text = card(
            "❌ خرید ناموفق",
            [
                "💔 سکه کافی نداری!",
                f"💵 قیمت: {fmt(price)} تومان",
                f"🏦 موجودی تو: {fmt(user['balance'])}",
            ],
        )
        reply(chat_id, message_id, text)
        return
    added = db.add_item(user["user_id"], category, item_name)
    if not added:
        reply(chat_id, message_id, error_card(f"قبلاً همین {category} رو داری!"))
        return
    new_balance = db.update_balance(user["user_id"], -price)
    text = card(
        f"{emoji} خرید موفق",
        [f"{emoji} {item_name} خریدی!", f"💸 هزینه: {fmt(price)} تومان"],
        f"🏦 موجودی جدید: {fmt(new_balance)}",
    )
    reply(chat_id, message_id, text)


def cmd_shop_owned(user, category, chat_id, message_id):
    items = db.get_items(user["user_id"], category)
    emoji = CATEGORY_EMOJI[category]
    if not items:
        text = card(
            f"{emoji} {category}‌های شما",
            [f"هنوز هیچ {category}ی نداری."],
            f"فروشگاه: {category} ها",
        )
        reply(chat_id, message_id, text)
        return
    lines = [f"• {name}" for name in items]
    text = card(f"{emoji} {category}‌های شما", lines)
    reply(chat_id, message_id, text)


# ------------------------------------------------------------------
# سیستم کشورها (جنگ/کشورگیری)
# ------------------------------------------------------------------

BUILD_TYPES = {
    "کارخانه": {"field": "factories", "price_key": "FACTORY_PRICE", "emoji": "🏭"},
    "پایگاه": {"field": "bases", "price_key": "BASE_PRICE", "emoji": "🎯"},
    "مدرسه": {"field": "schools", "price_key": "SCHOOL_PRICE", "emoji": "🏫"},
    "پدافند": {"field": "defenses", "price_key": "DEFENSE_PRICE", "emoji": "🛡"},
}

DESTROYED_FIELD_MAP = {
    "factories": "destroyed_factories",
    "schools": "destroyed_schools",
    "bases": "destroyed_bases",
    "defenses": "destroyed_defenses",
}

BUILD_PRICE_KEY_BY_FIELD = {
    "factories": "FACTORY_PRICE",
    "schools": "SCHOOL_PRICE",
    "bases": "BASE_PRICE",
    "defenses": "DEFENSE_PRICE",
}

BUILD_LABEL_BY_FIELD = {
    "factories": "کارخانه",
    "schools": "مدرسه",
    "bases": "پایگاه",
    "defenses": "پدافند",
}


def _country_hours_since_claim(country):
    return db.hours_since(country["claimed_at"])


def _country_can_fight(country):
    """True اگه بشه بهش حمله کرد یا باهاش حمله کرد (گذشتن از کول‌داون گرفتن کشور)."""
    return _country_hours_since_claim(country) >= cfg("ATTACK_COOLDOWN_HOURS")


def _country_ceasefire_active(country):
    if not country.get("last_ceasefire"):
        return False
    return db.hours_since(country["last_ceasefire"]) < cfg("CEASEFIRE_HOURS")


def _country_repair_cost(country):
    return (
        country["destroyed_factories"] * cfg("FACTORY_PRICE")
        + country["destroyed_schools"] * cfg("SCHOOL_PRICE")
        + country["destroyed_bases"] * cfg("BASE_PRICE")
        + country["destroyed_defenses"] * cfg("DEFENSE_PRICE")
        + country["cash_damage"]
    )


def _country_value(country):
    return (
        country["missiles"] * cfg("MISSILE_PRICE")
        + country["factories"] * cfg("FACTORY_PRICE")
        + country["schools"] * cfg("SCHOOL_PRICE")
        + country["bases"] * cfg("BASE_PRICE")
        + country["defenses"] * cfg("DEFENSE_PRICE")
        - _country_repair_cost(country)
    )


def cmd_country_list(user, args, chat_id, message_id):
    names = db.list_unclaimed_countries()
    if not names:
        reply(chat_id, message_id, card("🌍 کشورهای آزاد", ["فعلاً هیچ کشور آزادی نمونده!"]))
        return
    lines = [f"• {n}" for n in names]
    text = card(
        "🌍 کشورهای آزاد",
        lines,
        f"برای گرفتن یک کشور: خرید کشور <اسم>\n💵 قیمت: {fmt(cfg("COUNTRY_PRICE"))} تومان",
    )
    reply(chat_id, message_id, text)


def cmd_country_claimed_list(user, args, chat_id, message_id):
    countries = db.list_owned_countries()
    if not countries:
        reply(chat_id, message_id, card("🏳️ کشورهای گرفته‌شده", ["هنوز هیچ کشوری تصاحب نشده."]))
        return
    owner_ids = [c["owner_id"] for c in countries]
    nickname_map = db.get_user_nickname_map(owner_ids)
    countries.sort(key=lambda c: c["name"])
    lines = [f"• {c['name']} ← {nickname_map.get(c['owner_id'], '؟')}" for c in countries]
    text = card("🏳️ کشورهای گرفته‌شده", lines)
    reply(chat_id, message_id, text)


def cmd_country_buy(user, args, chat_id, message_id):
    existing = db.get_country_by_owner(user["user_id"])
    if existing:
        reply(chat_id, message_id, error_card(
            f"تو از قبل کشور «{existing['name']}» رو داری!",
            "هر کاربر فقط یک کشور می‌تونه داشته باشه.",
        ))
        return
    if not args:
        reply(chat_id, message_id, error_card("اسم کشور رو بنویس.", "لیست کشورهای آزاد: کشور ها"))
        return
    name = " ".join(args).strip()
    country = db.get_country(name)
    if not country:
        reply(chat_id, message_id, error_card("همچین کشوری وجود نداره.", "لیست کشورهای آزاد: کشور ها"))
        return
    if country["owner_id"] is not None:
        reply(chat_id, message_id, error_card("این کشور قبلاً گرفته شده و دیگه قابل تصاحب نیست."))
        return
    if user["balance"] < cfg("COUNTRY_PRICE"):
        text = card(
            "❌ خرید ناموفق",
            [
                "💔 سکه کافی نداری!",
                f"💵 قیمت کشور: {fmt(cfg("COUNTRY_PRICE"))} تومان",
                f"🏦 موجودی تو: {fmt(user['balance'])}",
            ],
        )
        reply(chat_id, message_id, text)
        return
    if not db.claim_country(name, user["user_id"]):
        reply(chat_id, message_id, error_card("یکی دیگه همین الان این کشور رو گرفت! یه کشور دیگه انتخاب کن."))
        return
    new_balance = db.update_balance(user["user_id"], -cfg("COUNTRY_PRICE"))
    text = card(
        "🌍 کشور گرفته شد!",
        [
            f"🏳️ کشور: {name}",
            f"💸 هزینه: {fmt(cfg("COUNTRY_PRICE"))} تومان",
            f"⏰ تا {cfg("ATTACK_COOLDOWN_HOURS")} ساعت آینده نه می‌تونی حمله کنی نه بهت حمله میشه",
            "🔒 این کشور برای همیشه مال توئه؛ کسی نمی‌تونه ازت بگیرتش.",
        ],
        f"🏦 موجودی جدید: {fmt(new_balance)}",
    )
    reply(chat_id, message_id, text)


def cmd_country_status(user, args, chat_id, message_id):
    country = db.get_country_by_owner(user["user_id"])
    if not country:
        reply(chat_id, message_id, error_card("هنوز کشوری نداری!", "لیست کشورهای آزاد: کشور ها"))
        return
    can_fight = _country_can_fight(country)
    ceasefire = _country_ceasefire_active(country)
    repair_cost = _country_repair_cost(country)
    lines = [
        f"🏳️ کشور: {country['name']}",
        f"🚀 موشک: {country['missiles']}",
        f"🏭 کارخانه: {country['factories']}   🏫 مدرسه: {country['schools']}",
        f"🎯 پایگاه: {country['bases']}   🛡 پدافند: {country['defenses']}",
    ]
    if repair_cost > 0:
        lines.append(f"💥 خسارت (نیاز به ترمیم): {fmt(repair_cost)} تومان")
    if not can_fight:
        remaining = remaining_hours_text(_country_hours_since_claim(country), cfg("ATTACK_COOLDOWN_HOURS"))
        if remaining:
            lines.append(f"⏰ تا فعال شدن جنگ: {remaining}")
    if ceasefire:
        lines.append(f"🕊 تحت آتش‌بسی (تا {cfg("CEASEFIRE_HOURS")} ساعت از فعال‌سازی، حمله‌پذیر نیستی)")
    text = card("🌍 وضعیت کشور من", lines, "درآمد کشور: درآمد کشور  |  ترمیم: ترمیم کشور")
    reply(chat_id, message_id, text)


def cmd_country_build(user, build_key, args, chat_id, message_id):
    country = db.get_country_by_owner(user["user_id"])
    if not country:
        reply(chat_id, message_id, error_card("اول باید یه کشور بگیری!", "لیست کشورهای آزاد: کشور ها"))
        return
    info = BUILD_TYPES[build_key]
    price = cfg(info["price_key"])
    arg0 = args[0] if args else None
    if arg0 in ("حداکثر", "max"):
        count = user["balance"] // price if price > 0 else 0
        if count <= 0:
            reply(chat_id, message_id, error_card(f"سکه کافی برای حتی یک {build_key} هم نداری."))
            return
    else:
        count = parse_int(arg0) if arg0 else 1
        if count is None or count <= 0:
            reply(chat_id, message_id, error_card(f"تعداد {build_key} رو درست وارد کن.", "یا بنویس: حداکثر"))
            return
    cost = price * count
    if user["balance"] < cost:
        text = card(
            "❌ خرید ناموفق",
            [
                "💔 سکه کافی نداری!",
                f"💵 هزینه‌ی {count} تا {build_key}: {fmt(cost)} تومان",
                f"🏦 موجودی تو: {fmt(user['balance'])}",
            ],
        )
        reply(chat_id, message_id, text)
        return
    db.adjust_country(country["name"], **{info["field"]: count})
    new_balance = db.update_balance(user["user_id"], -cost)
    text = card(
        f"{info['emoji']} خرید موفق",
        [f"{info['emoji']} {count} تا {build_key} برای «{country['name']}» ساخته شد", f"💸 هزینه: {fmt(cost)} تومان"],
        f"🏦 موجودی جدید: {fmt(new_balance)}",
    )
    reply(chat_id, message_id, text)


def cmd_country_buy_missile(user, args, chat_id, message_id):
    country = db.get_country_by_owner(user["user_id"])
    if not country:
        reply(chat_id, message_id, error_card("اول باید یه کشور بگیری!", "لیست کشورهای آزاد: کشور ها"))
        return
    price = cfg("MISSILE_PRICE")
    arg0 = args[0] if args else None
    if arg0 in ("حداکثر", "max"):
        count = user["balance"] // price if price > 0 else 0
        if count <= 0:
            reply(chat_id, message_id, error_card("سکه کافی برای حتی یک موشک هم نداری."))
            return
    else:
        count = parse_int(arg0) if arg0 else 1
        if count is None or count <= 0:
            reply(chat_id, message_id, error_card("تعداد موشک رو درست وارد کن.", "یا بنویس: حداکثر"))
            return
    cost = price * count
    if user["balance"] < cost:
        text = card(
            "❌ خرید ناموفق",
            [
                "💔 سکه کافی نداری!",
                f"💵 هزینه‌ی {count} موشک: {fmt(cost)} تومان",
                f"🏦 موجودی تو: {fmt(user['balance'])}",
            ],
        )
        reply(chat_id, message_id, text)
        return
    db.adjust_country(country["name"], missiles=count)
    new_balance = db.update_balance(user["user_id"], -cost)
    text = card(
        "🚀 خرید موفق",
        [f"🚀 {count} موشک برای «{country['name']}» ساخته شد", f"💸 هزینه: {fmt(cost)} تومان"],
        f"🏦 موجودی جدید: {fmt(new_balance)}",
    )
    reply(chat_id, message_id, text)


def cmd_country_income(user, args, chat_id, message_id):
    country = db.get_country_by_owner(user["user_id"])
    if not country:
        reply(chat_id, message_id, error_card("اول باید یه کشور بگیری!", "لیست کشورهای آزاد: کشور ها"))
        return
    hours = db.hours_since(country["last_income"])
    remaining = remaining_hours_text(hours, cfg("COUNTRY_INCOME_COOLDOWN_HOURS"))
    if remaining:
        text = card(
            "⏰ صبر کن!",
            ["💰 درآمد کشورت رو گرفتی", f"⏰ زمان باقی‌مونده: {remaining}"],
        )
        reply(chat_id, message_id, text)
        return
    income = country["factories"] * cfg("FACTORY_INCOME") + country["schools"] * cfg("SCHOOL_INCOME")
    missiles_gained = country["bases"] * cfg("BASE_MISSILE_YIELD")
    new_balance = db.update_balance(user["user_id"], income)
    if missiles_gained:
        db.adjust_country(country["name"], missiles=missiles_gained)
    db.set_country_field(country["name"], "last_income", db._now())
    text = card(
        "💰 درآمد کشور",
        [
            f"🏭 درآمد کارخانه‌ها + 🏫 مدارس: {fmt(income)} تومان",
            f"🚀 موشک تولیدشده توسط پایگاه‌ها: {missiles_gained}",
        ],
        f"🏦 موجودی جدید: {fmt(new_balance)}\n⏰ درآمد بعدی: {cfg("COUNTRY_INCOME_COOLDOWN_HOURS")} ساعت دیگه",
    )
    reply(chat_id, message_id, text)


def cmd_country_repair(user, args, chat_id, message_id):
    country = db.get_country_by_owner(user["user_id"])
    if not country:
        reply(chat_id, message_id, error_card("اول باید یه کشور بگیری!", "لیست کشورهای آزاد: کشور ها"))
        return
    cost = _country_repair_cost(country)
    if cost <= 0:
        reply(chat_id, message_id, error_card("کشورت خسارتی نداره که نیاز به ترمیم باشه."))
        return
    if user["balance"] < cost:
        text = card(
            "❌ ترمیم ناموفق",
            ["💔 سکه کافی نداری!", f"💵 هزینه‌ی ترمیم: {fmt(cost)} تومان", f"🏦 موجودی تو: {fmt(user['balance'])}"],
        )
        reply(chat_id, message_id, text)
        return
    db.adjust_country(
        country["name"],
        factories=country["destroyed_factories"],
        schools=country["destroyed_schools"],
        bases=country["destroyed_bases"],
        defenses=country["destroyed_defenses"],
        destroyed_factories=-country["destroyed_factories"],
        destroyed_schools=-country["destroyed_schools"],
        destroyed_bases=-country["destroyed_bases"],
        destroyed_defenses=-country["destroyed_defenses"],
    )
    db.set_country_field(country["name"], "cash_damage", 0)
    new_balance = db.update_balance(user["user_id"], -cost)
    text = card(
        "🛠 ترمیم انجام شد",
        [f"🏳️ کشور: {country['name']}", f"💸 هزینه: {fmt(cost)} تومان", "✅ همه‌ی ساختمان‌ها بازسازی شدن"],
        f"🏦 موجودی جدید: {fmt(new_balance)}",
    )
    reply(chat_id, message_id, text)


def cmd_country_ceasefire(user, args, chat_id, message_id):
    country = db.get_country_by_owner(user["user_id"])
    if not country:
        reply(chat_id, message_id, error_card("اول باید یه کشور بگیری!", "لیست کشورهای آزاد: کشور ها"))
        return
    hours = db.hours_since(country["last_ceasefire"])
    remaining = remaining_hours_text(hours, cfg("CEASEFIRE_COOLDOWN_HOURS"))
    if remaining:
        text = card(
            "⏰ صبر کن!",
            ["🕊 آتش‌بس رو قبلاً فعال کردی", f"⏰ زمان باقی‌مونده تا فعال‌سازی دوباره: {remaining}"],
        )
        reply(chat_id, message_id, text)
        return
    db.set_country_field(country["name"], "last_ceasefire", db._now())
    text = card(
        "🕊 آتش‌بس فعال شد",
        [f"🏳️ کشور: {country['name']}", f"⏰ مدت: {cfg("CEASEFIRE_HOURS")} ساعت", "🛡 در این مدت کسی نمی‌تونه بهت حمله کنه"],
    )
    reply(chat_id, message_id, text)


def cmd_country_espionage(user, args, chat_id, message_id):
    if not args:
        reply(chat_id, message_id, error_card("اسم کشوری که می‌خوای جاسوسی کنی رو بنویس.", "مثال: جاسوسی ایران"))
        return
    name = " ".join(args).strip()
    target = db.get_country(name)
    if not target or target["owner_id"] is None:
        reply(chat_id, message_id, error_card("همچین کشور تصاحب‌شده‌ای وجود نداره."))
        return
    if target["owner_id"] == user["user_id"]:
        reply(chat_id, message_id, error_card("این که کشور خودته! نیازی به جاسوسی نیست."))
        return
    if user["balance"] < cfg("ESPIONAGE_PRICE"):
        text = card(
            "❌ ناموفق",
            ["💔 سکه کافی نداری!", f"💵 هزینه‌ی جاسوسی: {fmt(cfg("ESPIONAGE_PRICE"))} تومان"],
        )
        reply(chat_id, message_id, text)
        return
    new_balance = db.update_balance(user["user_id"], -cfg("ESPIONAGE_PRICE"))
    repair_cost = _country_repair_cost(target)
    lines = [
        f"🏳️ کشور: {target['name']}",
        f"🚀 موشک: {target['missiles']}",
        f"🏭 کارخانه: {target['factories']}   🏫 مدرسه: {target['schools']}",
        f"🎯 پایگاه: {target['bases']}   🛡 پدافند: {target['defenses']}",
        f"💥 خسارت فعلی: {fmt(repair_cost)} تومان",
    ]
    text = card("🕵️ گزارش جاسوسی", lines, f"🏦 موجودی جدید: {fmt(new_balance)}")
    reply(chat_id, message_id, text)


def cmd_country_attack(user, args, chat_id, message_id):
    attacker = db.get_country_by_owner(user["user_id"])
    if not attacker:
        reply(chat_id, message_id, error_card("اول باید یه کشور بگیری!", "لیست کشورهای آزاد: کشور ها"))
        return
    if len(args) < 2:
        reply(chat_id, message_id, error_card("فرمت درست: حمله <اسم کشور> <تعداد موشک>"))
        return
    missile_count = parse_int(args[-1])
    target_name = " ".join(args[:-1]).strip()
    if missile_count is None or missile_count <= 0:
        reply(chat_id, message_id, error_card("تعداد موشک رو درست وارد کن."))
        return
    target = db.get_country(target_name)
    if not target or target["owner_id"] is None:
        reply(chat_id, message_id, error_card("همچین کشور تصاحب‌شده‌ای وجود نداره."))
        return
    if target["name"] == attacker["name"]:
        reply(chat_id, message_id, error_card("نمی‌تونی به کشور خودت حمله کنی!"))
        return
    if not _country_can_fight(attacker):
        remaining = remaining_hours_text(_country_hours_since_claim(attacker), cfg("ATTACK_COOLDOWN_HOURS"))
        reply(chat_id, message_id, error_card(
            "کشورت هنوز تازه‌ست و نمی‌تونه حمله کنه.", f"⏰ باقی‌مونده: {remaining}"
        ))
        return
    if not _country_can_fight(target):
        remaining = remaining_hours_text(_country_hours_since_claim(target), cfg("ATTACK_COOLDOWN_HOURS"))
        reply(chat_id, message_id, error_card(
            "این کشور هنوز تازه‌ست و قابل حمله نیست.", f"⏰ باقی‌مونده: {remaining}"
        ))
        return
    if _country_ceasefire_active(target):
        reply(chat_id, message_id, error_card("این کشور الان تحت آتش‌بسه و نمی‌تونی بهش حمله کنی."))
        return
    if attacker["missiles"] < missile_count:
        reply(chat_id, message_id, error_card(
            "به این تعداد موشک نداری!", f"🚀 موشک‌های تو: {attacker['missiles']}"
        ))
        return

    db.adjust_country(attacker["name"], missiles=-missile_count)

    absorbed = min(target["defenses"], missile_count)
    if absorbed:
        db.adjust_country(target["name"], defenses=-absorbed)
    breakthrough = missile_count - absorbed

    destroyed_report = []
    remaining_missiles = breakthrough
    for field in ("factories", "schools", "bases"):
        if remaining_missiles <= 0:
            break
        take = min(target[field], remaining_missiles)
        if take > 0:
            db.adjust_country(target["name"], **{field: -take, DESTROYED_FIELD_MAP[field]: take})
            destroyed_report.append(f"{BUILD_LABEL_BY_FIELD[field]}: {take} تا")
            remaining_missiles -= take

    cash_damage_dealt = 0
    if remaining_missiles > 0:
        cash_damage_dealt = remaining_missiles * cfg("MISSILE_CASH_DAMAGE")
        db.adjust_country(target["name"], cash_damage=cash_damage_dealt)

    lines = [
        f"🏳️ هدف: {target['name']}",
        f"🚀 موشک شلیک‌شده: {missile_count}",
        f"🛡 خنثی‌شده توسط پدافند: {absorbed}",
        f"💥 موشک عبورکرده: {breakthrough}",
    ]
    if destroyed_report:
        lines.append("🔥 نابودشده‌ها: " + "، ".join(destroyed_report))
    if cash_damage_dealt:
        lines.append(f"💰 خسارت نقدی وارد‌شده: {fmt(cash_damage_dealt)} تومان")
    text = card("⚔️ نتیجه حمله", lines)
    reply(chat_id, message_id, text)

    # اطلاع‌رسانی به صاحب کشور مورد حمله
    defender_lines = [
        f"⚠️ کشورت «{target['name']}» مورد حمله قرار گرفت!",
        f"🚀 موشک شلیک‌شده: {missile_count}",
        f"🛡 خنثی‌شده: {absorbed}",
    ]
    if destroyed_report:
        defender_lines.append("🔥 نابودشده‌ها: " + "، ".join(destroyed_report))
    if cash_damage_dealt:
        defender_lines.append(f"💰 خسارت نقدی: {fmt(cash_damage_dealt)} تومان")
    defender_lines.append("💡 برای بازسازی: ترمیم کشور")
    try:
        api.send_message(target["owner_id"], card("🚨 هشدار حمله", defender_lines))
    except Exception:
        pass


def cmd_country_rank(user, args, chat_id, message_id):
    countries = db.list_owned_countries()
    if not countries:
        reply(chat_id, message_id, card("🏆 رتبه کشورها", ["هنوز هیچ کشوری تصاحب نشده."]))
        return
    owner_ids = [c["owner_id"] for c in countries]
    nickname_map = db.get_user_nickname_map(owner_ids)
    scored = sorted(countries, key=_country_value, reverse=True)
    lines = []
    for i, c in enumerate(scored[:10], start=1):
        owner_name = nickname_map.get(c["owner_id"], "؟")
        lines.append(f"{i}. {c['name']} (صاحب: {owner_name}) — ارزش: {fmt(_country_value(c))}")
    text = card("🏆 رتبه‌بندی کشورها", lines)
    reply(chat_id, message_id, text)



# ------------------------------------------------------------------
# اسلات و تاس
# ------------------------------------------------------------------

def resolve_bet_amount(user, amount_text, chat_id, message_id, example_cmd):
    """اعتبارسنجی شرط - بدون محدودیت حداقل/حداکثر، فقط باید مثبت باشه.
    از میانبرهای خمس/ربع/ثلث/نصف/کل هم پشتیبانی می‌کنه."""
    amount = resolve_amount(amount_text, user["balance"])
    if amount is None or amount <= 0:
        reply(chat_id, message_id, error_card(
            "مقدار شرط نامعتبره!",
            f"مثال: {example_cmd} 50000  یا  {example_cmd} نصف  یا  {example_cmd} 5میل",
        ))
        return None
    if user["balance"] < amount:
        text = card(
            "💔 سکه کافی نیست",
            [f"🏦 موجودی تو: {fmt(user['balance'])}", f"💵 شرط: {fmt(amount)}"],
            "💡 یه شرط کمتر بزن",
        )
        reply(chat_id, message_id, text)
        return None
    return amount


def _pick_slot_multiplier():
    weights = config.SLOT_MULTIPLIER_WEIGHTS
    choices = list(weights.keys())
    probs = list(weights.values())
    return random.choices(choices, weights=probs, k=1)[0]


SLOT_WIN_SYMBOLS = {
    4: ("💎 | 💎 | 💎", "💎 وضعیت: پولت ۴ برابر شد! 💎"),
    3: ("🍋 | 🍋 | 🍋", "🍋 وضعیت: پولت ۳ برابر شد!"),
    2: ("🍒 | 🍒 | 🍇", "🍒 وضعیت: پولت ۲ برابر شد!"),
}
SLOT_LOSE_SYMBOLS = ["🍇 | 🍊 | 🍎", "🍊 | 🍎 | 🍋", "🍎 | 🍇 | 🍒"]


def cmd_slot(user, args, chat_id, message_id):
    if not args:
        reply(chat_id, message_id, error_card(
            "مقدار شرط رو بنویس.", "مثال: اسلات 50000"
        ))
        return
    amount = resolve_bet_amount(user, args[0], chat_id, message_id, "اسلات")
    if amount is None:
        return

    db.update_balance(user["user_id"], -amount)

    win = random.random() < cfg("WIN_CHANCE")
    if not win:
        symbols = random.choice(SLOT_LOSE_SYMBOLS)
        new_balance = db.get_user(user["user_id"])["balance"]
        text = (
            f"🎰 ماشین شانس\n"
            f"{SLOT_BOX_TOP}\n"
            f"┃ {symbols} ┃\n"
            f"{SLOT_BOX_BOTTOM}\n"
            f"🔥 نتیجه عملیات:\n"
            f"{SLOT_SEP}\n"
            f"💸 مبلغ ورودی: {fmt(amount)}\n"
            f"💔 وضعیت: باختی!\n"
            f"📉 ضرر: {fmt(amount)}\n"
            f"{SLOT_SEP}\n"
            f"🏦 موجودی کل: {fmt(new_balance)}"
        )
        reply(chat_id, message_id, text)
        return

    multiplier = _pick_slot_multiplier()
    payout = amount * multiplier
    new_balance = db.update_balance(user["user_id"], payout)
    symbols, status_line = SLOT_WIN_SYMBOLS[multiplier]
    text = (
        f"🎰 ماشین شانس\n"
        f"{SLOT_BOX_TOP}\n"
        f"┃ {symbols} ┃\n"
        f"{SLOT_BOX_BOTTOM}\n"
        f"🔥 نتیجه عملیات:\n"
        f"{SLOT_SEP}\n"
        f"💸 مبلغ ورودی: {fmt(amount)}\n"
        f"{status_line}\n"
        f"📈 سود خالص: {fmt(payout)}\n"
        f"{SLOT_SEP}\n"
        f"🏦 موجودی کل: {fmt(new_balance)}"
    )
    reply(chat_id, message_id, text)


DICE_FACES_WIN = ["⚃", "⚄", "⚅"]
DICE_FACES_LOSE = ["⚀", "⚁", "⚂"]


def cmd_dice(user, args, chat_id, message_id):
    if not args:
        reply(chat_id, message_id, error_card(
            "مقدار شرط رو بنویس.", "مثال: تاس 50000"
        ))
        return
    amount = resolve_bet_amount(user, args[0], chat_id, message_id, "تاس")
    if amount is None:
        return

    db.update_balance(user["user_id"], -amount)

    win = random.random() < cfg("WIN_CHANCE")
    face = random.choice(DICE_FACES_WIN if win else DICE_FACES_LOSE)

    if not win:
        new_balance = db.get_user(user["user_id"])["balance"]
        text = (
            f"🎲 تاس\n"
            f"{DICE_BOX_TOP}\n"
            f"┃  {face}   ┃\n"
            f"{DICE_BOX_BOTTOM}\n"
            f"🔥 نتیجه:\n"
            f"{SLOT_SEP}\n"
            f"💸 ورودی: {fmt(amount)}\n"
            f"❌ وضعیت: باختی!\n"
            f"📉 ضرر: {fmt(amount)}\n"
            f"{SLOT_SEP}\n"
            f"🏦 موجودی: {fmt(new_balance)}"
        )
        reply(chat_id, message_id, text)
        return

    payout = amount * 2
    new_balance = db.update_balance(user["user_id"], payout)
    text = (
        f"🎲 تاس\n"
        f"{DICE_BOX_TOP}\n"
        f"┃  {face}   ┃\n"
        f"{DICE_BOX_BOTTOM}\n"
        f"🔥 نتیجه:\n"
        f"{SLOT_SEP}\n"
        f"💸 ورودی: {fmt(amount)}\n"
        f"✅ وضعیت: بردی! پولت ۲ برابر شد!\n"
        f"📈 سود خالص: {fmt(payout)}\n"
        f"{SLOT_SEP}\n"
        f"🏦 موجودی: {fmt(new_balance)}"
    )
    reply(chat_id, message_id, text)


# ------------------------------------------------------------------
# شیر یا خط
# ------------------------------------------------------------------

def cmd_coinflip(user, args, chat_id, message_id):
    if not args:
        reply(chat_id, message_id, error_card(
            "مقدار شرط رو بنویس.", "مثال: شیر یا خط 50000"
        ))
        return
    amount = resolve_bet_amount(user, args[0], chat_id, message_id, "شیر یا خط")
    if amount is None:
        return

    db.update_balance(user["user_id"], -amount)
    side = random.choice(["🦁 شیر", "✍️ خط"])
    win = random.random() < cfg("WIN_CHANCE")

    if not win:
        new_balance = db.get_user(user["user_id"])["balance"]
        text = card(
            "🪙 شیر یا خط",
            [
                f"🪙 سکه افتاد رو: {side}",
                f"💸 ورودی: {fmt(amount)}",
                "❌ وضعیت: باختی!",
            ],
            f"🏦 موجودی: {fmt(new_balance)}",
        )
        reply(chat_id, message_id, text)
        return

    payout = amount * 2
    new_balance = db.update_balance(user["user_id"], payout)
    text = card(
        "🪙 شیر یا خط",
        [
            f"🪙 سکه افتاد رو: {side}",
            f"💸 ورودی: {fmt(amount)}",
            "✅ وضعیت: بردی! پولت ۲ برابر شد!",
        ],
        f"🏦 موجودی: {fmt(new_balance)}",
    )
    reply(chat_id, message_id, text)


# ------------------------------------------------------------------
# پنل مدیریت (فقط ادمین‌ها) - همه‌چیز زیر یک دستور: «ادمین»
# ------------------------------------------------------------------

def is_admin(user_id):
    return user_id in config.ADMIN_IDS


ADMIN_ITEM_CATEGORIES = {"ماشین": "ماشین", "خانه": "خانه", "گوشی": "گوشی"}


def cmd_admin_help(chat_id, message_id):
    text = card(
        "🛡️ پنل ادمین",
        [
            "دادن سکه <لقب> <مقدار>      (مقدار می‌تونه منفی هم باشه)",
            "دادن ماینر <لقب> <مقدار>",
            "تغییر لقب <لقب_فعلی> <لقب_جدید>",
            "هدیه <لقب> <ماشین/خانه/گوشی> <اسم>",
            "هدیه همگانی <ماشین/خانه/گوشی> <اسم>",
            "سکه همگانی <مقدار>      (منفی = کسر از همه)",
            "دادن کشور <لقب> <کشور>",
            "آزاد کشور <کشور>",
            "تنظیم <کلید> <مقدار>",
            "تنظیمات",
            "پیام همگانی <متن>              (به همه‌جا: پی‌وی/گروه/کانال)",
            "بن <لقب>                      (مسدود کردن کامل یک کاربر)",
            "رفع بن <لقب>",
        ],
    )
    reply(chat_id, message_id, text)


def cmd_admin_coin(args, chat_id, message_id):
    if len(args) < 2:
        reply(chat_id, message_id, error_card("فرمت: دادن سکه <لقب> <مقدار>"))
        return
    amount = parse_int(args[-1])
    nickname = " ".join(args[:-1]).strip()
    if amount is None or amount == 0:
        reply(chat_id, message_id, error_card("مقدار رو درست وارد کن."))
        return
    target = db.get_user_by_nickname(nickname)
    if not target:
        reply(chat_id, message_id, error_card("کاربری با این لقب پیدا نشد."))
        return
    new_val = db.update_balance(target["user_id"], amount)
    text = card("✅ انجام شد", [f"👤 کاربر: {nickname}", f"💰 موجودی جدید: {fmt(new_val)}"])
    reply(chat_id, message_id, text)


def cmd_admin_miner(args, chat_id, message_id):
    if len(args) < 2:
        reply(chat_id, message_id, error_card("فرمت: دادن ماینر <لقب> <مقدار>"))
        return
    amount = parse_int(args[-1])
    nickname = " ".join(args[:-1]).strip()
    if amount is None or amount == 0:
        reply(chat_id, message_id, error_card("مقدار رو درست وارد کن."))
        return
    target = db.get_user_by_nickname(nickname)
    if not target:
        reply(chat_id, message_id, error_card("کاربری با این لقب پیدا نشد."))
        return
    new_val = db.update_miners(target["user_id"], amount)
    text = card("✅ انجام شد", [f"👤 کاربر: {nickname}", f"⛏️ ماینر جدید: {new_val}"])
    reply(chat_id, message_id, text)


def cmd_admin_nickname(args, chat_id, message_id):
    if len(args) < 2:
        reply(chat_id, message_id, error_card("فرمت: تغییر لقب <لقب_فعلی> <لقب_جدید>"))
        return
    old_nick, new_nick = args[0], args[1]
    target = db.get_user_by_nickname(old_nick)
    if not target:
        reply(chat_id, message_id, error_card("کاربری با این لقب پیدا نشد."))
        return
    if not db.set_nickname(target["user_id"], new_nick):
        reply(chat_id, message_id, error_card("این لقب قبلاً برای یکی دیگه استفاده شده."))
        return
    text = card("✅ انجام شد", [f"👤 {old_nick} → {new_nick}"])
    reply(chat_id, message_id, text)


def cmd_admin_ban(args, chat_id, message_id):
    if not args:
        reply(chat_id, message_id, error_card("فرمت: بن <لقب>"))
        return
    nickname = " ".join(args).strip()
    target = db.get_user_by_nickname(nickname)
    if not target:
        reply(chat_id, message_id, error_card("کاربری با این لقب پیدا نشد."))
        return
    db.set_banned(target["user_id"], True)
    text = card(
        "🚫 مسدود شد",
        [f"👤 کاربر: {nickname}", "از این به بعد نمی‌تونه هیچ دستوری بزنه."],
    )
    reply(chat_id, message_id, text)


def cmd_admin_unban(args, chat_id, message_id):
    if not args:
        reply(chat_id, message_id, error_card("فرمت: رفع بن <لقب>"))
        return
    nickname = " ".join(args).strip()
    target = db.get_user_by_nickname(nickname)
    if not target:
        reply(chat_id, message_id, error_card("کاربری با این لقب پیدا نشد."))
        return
    db.set_banned(target["user_id"], False)
    text = card(
        "✅ رفع مسدودیت شد",
        [f"👤 کاربر: {nickname}", "دوباره می‌تونه بازی کنه."],
    )
    reply(chat_id, message_id, text)


def cmd_admin_gift(args, chat_id, message_id):
    if len(args) < 3:
        reply(chat_id, message_id, error_card("فرمت: هدیه <لقب> <ماشین/خانه/گوشی> <اسم>"))
        return
    nickname, category = args[0], args[1]
    item_name = " ".join(args[2:]).strip()
    if category not in ADMIN_ITEM_CATEGORIES:
        reply(chat_id, message_id, error_card("دسته باید یکی از این‌ها باشه: ماشین، خانه، گوشی"))
        return
    target = db.get_user_by_nickname(nickname)
    if not target:
        reply(chat_id, message_id, error_card("کاربری با این لقب پیدا نشد."))
        return
    db.add_item(target["user_id"], category, item_name)
    text = card("🎁 هدیه داده شد", [f"👤 کاربر: {nickname}", f"📦 {category}: {item_name}"])
    reply(chat_id, message_id, text)


def cmd_admin_gift_all(args, chat_id, message_id):
    if len(args) < 2:
        reply(chat_id, message_id, error_card("فرمت: هدیه همگانی <ماشین/خانه/گوشی> <اسم>"))
        return
    category = args[0]
    item_name = " ".join(args[1:]).strip()
    if category not in ADMIN_ITEM_CATEGORIES:
        reply(chat_id, message_id, error_card("دسته باید یکی از این‌ها باشه: ماشین، خانه، گوشی"))
        return
    ids = db.all_user_ids()
    for uid in ids:
        db.add_item(uid, category, item_name)
    text = card("🎁 هدیه‌ی همگانی داده شد", [f"👥 تعداد کاربر: {len(ids)}", f"📦 {category}: {item_name}"])
    reply(chat_id, message_id, text)


def cmd_admin_broadcast_coin_signed(args, chat_id, message_id):
    if not args:
        reply(chat_id, message_id, error_card("فرمت: سکه همگانی <مقدار>"))
        return
    amount = parse_int(args[0])
    if amount is None or amount == 0:
        reply(chat_id, message_id, error_card("مقدار رو درست وارد کن."))
        return
    ids = db.all_user_ids()
    for uid in ids:
        db.update_balance(uid, amount)
    verb = "اضافه شد به" if amount > 0 else "کسر شد از"
    text = card(
        "📢 انجام شد",
        [f"👥 تعداد کاربر: {len(ids)}", f"💵 {fmt(abs(amount))} تومان {verb} همه"],
        "💡 موجودی هیچ‌کس منفی نمیشه (حداقل صفر می‌مونه)",
    )
    reply(chat_id, message_id, text)


def cmd_admin_country_grant(args, chat_id, message_id):
    if len(args) < 2:
        reply(chat_id, message_id, error_card("فرمت: دادن کشور <لقب> <کشور>"))
        return
    nickname = args[0]
    country_name = " ".join(args[1:]).strip()
    target = db.get_user_by_nickname(nickname)
    if not target:
        reply(chat_id, message_id, error_card("کاربری با این لقب پیدا نشد."))
        return
    if not db.get_country(country_name):
        reply(chat_id, message_id, error_card("همچین کشوری وجود نداره."))
        return
    db.admin_force_claim_country(country_name, target["user_id"])
    text = card("✅ انجام شد", [f"🏳️ کشور «{country_name}» به {nickname} داده شد"])
    reply(chat_id, message_id, text)


def cmd_admin_country_free(args, chat_id, message_id):
    if not args:
        reply(chat_id, message_id, error_card("فرمت: آزاد کشور <کشور>"))
        return
    country_name = " ".join(args).strip()
    if not db.admin_reset_country(country_name):
        reply(chat_id, message_id, error_card("همچین کشوری وجود نداره."))
        return
    text = card("✅ انجام شد", [f"🏳️ کشور «{country_name}» کاملاً آزاد و صفر شد"])
    reply(chat_id, message_id, text)


def cmd_admin_setting_set(args, chat_id, message_id):
    if len(args) < 2:
        reply(chat_id, message_id, error_card("فرمت: تنظیم <کلید> <مقدار>", "لیست کلیدها: تنظیمات"))
        return
    key = args[0]
    if key not in TUNABLE_SETTINGS:
        reply(chat_id, message_id, error_card("همچین کلیدی وجود نداره.", "لیست کلیدها: تنظیمات"))
        return
    default = getattr(config, key)
    raw_value = args[1]
    try:
        value = float(raw_value) if isinstance(default, float) else int(raw_value)
    except ValueError:
        reply(chat_id, message_id, error_card("مقدار عددی درست وارد کن."))
        return
    db.set_setting(key, value)
    text = card("✅ تنظیم شد", [f"⚙️ {key} = {value}"])
    reply(chat_id, message_id, text)


def cmd_admin_setting_list(chat_id, message_id):
    lines = []
    for key in TUNABLE_SETTINGS:
        current = cfg(key)
        overridden = db.get_setting(key) is not None
        mark = " (تغییریافته)" if overridden else ""
        lines.append(f"{key} = {current}{mark}")
    text = card("⚙️ تنظیمات قابل‌تغییر بازی", lines, "برای تغییر: تنظیم <کلید> <مقدار>")
    reply(chat_id, message_id, text)


def cmd_admin_broadcast_message(args, chat_id, message_id):
    if not args:
        reply(chat_id, message_id, error_card("فرمت: پیام همگانی <متن>"))
        return
    message_text = " ".join(args)
    chat_ids = db.all_chat_ids()
    broadcast_text = card("📨 پیام از مدیریت", [message_text])
    sent_count = 0
    for cid in chat_ids:
        try:
            api.send_message(cid, broadcast_text)
            sent_count += 1
        except Exception:
            pass
    text = card("✅ پیام همگانی ارسال شد", [f"📍 تعداد مقصد (پی‌وی/گروه/کانال): {sent_count}"])
    reply(chat_id, message_id, text)



# ------------------------------------------------------------------
# معرفی سازنده
# ------------------------------------------------------------------

CREATOR_ID = "@User_COCA"


def cmd_creator(user, args, chat_id, message_id):
    text = card(
        "👨‍💻 سازنده ربات",
        [f"آیدی سازنده: {CREATOR_ID}"],
    )
    reply(chat_id, message_id, text)


# ------------------------------------------------------------------
# مسیریابی دستورات (Command Router)
# ------------------------------------------------------------------

def route_message(sender_id, chat_id, text, message_id):
    text = (text or "").strip()
    if not text:
        return

    db.record_chat(chat_id)
    user = db.get_user(sender_id)

    if user.get("banned"):
        reply(chat_id, message_id, error_card(
            "🚫 دسترسیت به بازی مسدود شده.", "برای رفع مسدودیت با سازنده در ارتباط باش."
        ))
        return

    parts = text.split()
    p0 = parts[0] if len(parts) > 0 else ""
    p1 = parts[1] if len(parts) > 1 else ""
    p2 = parts[2] if len(parts) > 2 else ""

    # کاربر جدید حتماً باید اول لقب بذاره - تا وقتی نذاشته، هیچ
    # دستور دیگه‌ای (جز خود «لقب») اجرا نمیشه.
    if user["nickname"] is None:
        if p0 == "لقب":
            return cmd_nickname(user, parts[1:], chat_id, message_id)
        text_msg = card(
            "👋 خوش اومدی!",
            ["برای شروع بازی، اول باید یه لقب برای خودت انتخاب کنی."],
            "مثال: لقب علی_شاه",
        )
        reply(chat_id, message_id, text_msg)
        return

    if p0 == "شیر" and p1 == "یا" and p2 == "خط":
        return cmd_coinflip(user, parts[3:], chat_id, message_id)

    if p0 == "شیر" and p1 == "خط":
        return cmd_coinflip(user, parts[2:], chat_id, message_id)

    if p0 == "خرید" and p1 == "کشور":
        return cmd_country_buy(user, parts[2:], chat_id, message_id)

    if p0 == "کشور" and p1 == "ها":
        return cmd_country_list(user, [], chat_id, message_id)

    if text == "کشورهای گرفته شده" or text == "کشورهای گرفته‌شده":
        return cmd_country_claimed_list(user, [], chat_id, message_id)

    if p0 == "کشور" and p1 == "من":
        return cmd_country_status(user, [], chat_id, message_id)

    if p0 == "خرید" and p1 == "موشک":
        return cmd_country_buy_missile(user, parts[2:], chat_id, message_id)

    if p0 == "خرید" and p1 in BUILD_TYPES:
        return cmd_country_build(user, p1, parts[2:], chat_id, message_id)

    if text == "درآمد کشور":
        return cmd_country_income(user, [], chat_id, message_id)

    if text == "ترمیم کشور":
        return cmd_country_repair(user, [], chat_id, message_id)

    if text in ("آتش بس", "آتش‌بس", "صلح"):
        return cmd_country_ceasefire(user, [], chat_id, message_id)

    if p0 == "جاسوسی":
        return cmd_country_espionage(user, parts[1:], chat_id, message_id)

    if p0 == "حمله":
        return cmd_country_attack(user, parts[1:], chat_id, message_id)

    if text == "رتبه کشورها":
        return cmd_country_rank(user, [], chat_id, message_id)

    if p0 == "خرید" and p1 == "ماشین":
        return cmd_shop_buy(user, "ماشین", parts[2:], chat_id, message_id)

    if p0 == "خرید" and p1 == "خانه":
        return cmd_shop_buy(user, "خانه", parts[2:], chat_id, message_id)

    if p0 == "خرید" and p1 == "گوشی":
        return cmd_shop_buy(user, "گوشی", parts[2:], chat_id, message_id)

    if p0 == "ماشین" and p1 == "ها":
        return cmd_shop_list("ماشین", chat_id, message_id)

    if p0 == "خانه" and p1 == "ها":
        return cmd_shop_list("خانه", chat_id, message_id)

    if p0 == "گوشی" and p1 == "ها":
        return cmd_shop_list("گوشی", chat_id, message_id)

    if p0 == "ماشین" and p1 == "های" and p2 == "من":
        return cmd_shop_owned(user, "ماشین", chat_id, message_id)

    if p0 == "خانه" and p1 == "های" and p2 == "من":
        return cmd_shop_owned(user, "خانه", chat_id, message_id)

    if p0 == "گوشی" and p1 == "های" and p2 == "من":
        return cmd_shop_owned(user, "گوشی", chat_id, message_id)

    if p0 == "دادن" and p1 == "سکه":
        if not is_admin(sender_id):
            return
        return cmd_admin_coin(parts[2:], chat_id, message_id)

    if p0 == "دادن" and p1 == "ماینر":
        if not is_admin(sender_id):
            return
        return cmd_admin_miner(parts[2:], chat_id, message_id)

    if p0 == "تغییر" and p1 == "لقب":
        if not is_admin(sender_id):
            return
        return cmd_admin_nickname(parts[2:], chat_id, message_id)

    if p0 == "هدیه" and p1 == "همگانی":
        if not is_admin(sender_id):
            return
        return cmd_admin_gift_all(parts[2:], chat_id, message_id)

    if p0 == "هدیه":
        if not is_admin(sender_id):
            return
        return cmd_admin_gift(parts[1:], chat_id, message_id)

    if p0 == "سکه" and p1 == "همگانی":
        if not is_admin(sender_id):
            return
        return cmd_admin_broadcast_coin_signed(parts[2:], chat_id, message_id)

    if p0 == "دادن" and p1 == "کشور":
        if not is_admin(sender_id):
            return
        return cmd_admin_country_grant(parts[2:], chat_id, message_id)

    if p0 == "آزاد" and p1 == "کشور":
        if not is_admin(sender_id):
            return
        return cmd_admin_country_free(parts[2:], chat_id, message_id)

    if text == "تنظیمات":
        if not is_admin(sender_id):
            return
        return cmd_admin_setting_list(chat_id, message_id)

    if p0 == "تنظیم":
        if not is_admin(sender_id):
            return
        return cmd_admin_setting_set(parts[1:], chat_id, message_id)

    if p0 == "پیام" and p1 == "همگانی":
        if not is_admin(sender_id):
            return
        return cmd_admin_broadcast_message(parts[2:], chat_id, message_id)

    if p0 == "رفع" and p1 == "بن":
        if not is_admin(sender_id):
            return
        return cmd_admin_unban(parts[2:], chat_id, message_id)

    if p0 == "بن":
        if not is_admin(sender_id):
            return
        return cmd_admin_ban(parts[1:], chat_id, message_id)

    if text == "راهنمای مدیریت":
        if not is_admin(sender_id):
            return
        return cmd_admin_help(chat_id, message_id)

    if p0 == "خرید" and p1 == "ماینر":
        return cmd_miner_buy(user, parts[2:], chat_id, message_id)

    if p0 == "ماینر" and p1 == "بگیر":
        return cmd_miner_collect(user, parts[2:], chat_id, message_id)

    if p0 == "انتقال" and p1 == "ماینر":
        return cmd_miner_transfer(user, parts[2:], chat_id, message_id)

    if p0 == "انتقال" and p1 == "سکه":
        return cmd_transfer_coin(user, parts[2:], chat_id, message_id)

    if p0 == "اسلات":
        return cmd_slot(user, parts[1:], chat_id, message_id)

    if p0 == "تاس":
        return cmd_dice(user, parts[1:], chat_id, message_id)

    if p0 == "لقب":
        return cmd_nickname(user, parts[1:], chat_id, message_id)

    if p0 == "اطلاعات":
        return cmd_profile(user, parts[1:], chat_id, message_id)

    if p0 == "شغل":
        return cmd_choose_job(user, parts[1:], chat_id, message_id)

    if text == "موجودی":
        return cmd_balance(user, [], chat_id, message_id)

    if text == "ماینر":
        return cmd_miner_status(user, [], chat_id, message_id)

    if text == "گردونه":
        return cmd_wheel(user, [], chat_id, message_id)

    if text == "سازنده":
        return cmd_creator(user, [], chat_id, message_id)

    if text == "رتبه":
        return cmd_rank(user, [], chat_id, message_id)

    if text == "راهنما" or text == "/start" or text == "شروع":
        return cmd_help(user, [], chat_id, message_id)

    if text == "راهنما کشورها" or text == "راهنما جنگ":
        return cmd_help_countries(user, [], chat_id, message_id)

    if text == "مشاغل":
        return cmd_jobs_list(user, [], chat_id, message_id)

    if text == "درآمد":
        return cmd_job_income(user, [], chat_id, message_id)

    # دستور ناشناخته - چیزی نمی‌فرستیم که ربات توی گروه شلوغ نشه


# ------------------------------------------------------------------
# استخراج اطلاعات از هر آپدیت (پیام) دریافتی از روبیکا
# ------------------------------------------------------------------

def extract_message(update_item):
    """
    هر آیتم داخل آرایه‌ی updates ممکنه یکی از این دو شکل رو داشته باشه:
    1) { "type": "NewMessage", "chat_id": ..., "new_message": {...} }
    2) { "update": { "type": "NewMessage", "chat_id": ..., "new_message": {...} } }
    این تابع هر دو حالت رو پشتیبانی می‌کنه.
    خروجی: (sender_id, chat_id, text, message_id)
    """
    node = update_item.get("update", update_item)
    if node.get("type") != "NewMessage":
        return None
    chat_id = node.get("chat_id")
    new_message = node.get("new_message") or {}
    text = new_message.get("text")
    sender_id = new_message.get("sender_id")
    message_id = new_message.get("message_id")
    if not chat_id or not sender_id or text is None:
        return None
    return sender_id, chat_id, text, message_id


# ------------------------------------------------------------------
# حلقه‌ی اصلی (Polling)
# ------------------------------------------------------------------

def load_offset():
    if os.path.exists(config.OFFSET_PATH):
        with open(config.OFFSET_PATH, "r", encoding="utf-8") as f:
            content = f.read().strip()
            return content or None
    return None


def save_offset(offset_id):
    with open(config.OFFSET_PATH, "w", encoding="utf-8") as f:
        f.write(offset_id or "")


def skip_backlog(offset_id):
    """
    پیام‌هایی که قبل از روشن شدن ربات جمع شدن (چه اولین بار اجرا میشه،
    چه موقعی که خاموش بوده) رو بدون جواب دادن، فقط رد می‌کنه و آفست رو
    میاره جلو. بعد از این، ربات فقط به پیام‌های واقعاً جدید جواب میده.
    """
    print("در حال رد کردن پیام‌های قبل از روشن شدن (بدون پاسخ) ...")
    skipped = 0
    while True:
        result = api.get_updates(offset_id=offset_id, limit=100)
        if not result or "data" not in result:
            break
        data = result["data"]
        updates = data.get("updates", [])
        next_offset = data.get("next_offset_id")
        skipped += len(updates)
        if next_offset:
            offset_id = next_offset
            save_offset(offset_id)
        if not updates:
            break
    print(f"✅ {skipped} پیام قدیمی رد شد. از الان فقط به پیام‌های جدید جواب میدم.")
    return offset_id


def run_bot():
    """حلقه‌ی اصلی ربات - این تابع در یک Thread جدا اجرا میشه."""
    print("=" * 60)
    print("در حال راه‌اندازی ربات...")
    db.init_db()

    me = api.get_me()
    if me and me.get("data", {}).get("bot"):
        bot_info = me["data"]["bot"]
        print(f"✅ ربات با موفقیت متصل شد: {bot_info}")
    else:
        print("⚠️ نتونستیم اطلاعات ربات رو بگیریم. توکن رو توی تنظیمات بالای فایل یا Environment Variables چک کن.")
        print(f"پاسخ سرور: {me}")

    offset_id = load_offset()
    offset_id = skip_backlog(offset_id)

    print("✅ ربات روشن شد و منتظر پیام‌های جدیده...")
    print("=" * 60)

    while True:
        try:
            result = api.get_updates(offset_id=offset_id, limit=100)
            if not result or "data" not in result:
                time.sleep(2)
                continue

            data = result["data"]
            updates = data.get("updates", [])
            next_offset = data.get("next_offset_id")

            for item in updates:
                parsed = extract_message(item)
                if not parsed:
                    continue
                sender_id, chat_id, text, message_id = parsed
                print(f"[{datetime.now().strftime('%H:%M:%S')}] پیام از {sender_id}: {text}")
                try:
                    route_message(sender_id, chat_id, text, message_id)
                except Exception as e:
                    print(f"[خطا در پردازش دستور] {e}")
                    reply(chat_id, message_id, error_card("یه خطا پیش اومد، دوباره امتحان کن."))

            if next_offset:
                offset_id = next_offset
                save_offset(offset_id)

            if not updates:
                time.sleep(1.5)

        except Exception as e:
            print(f"[خطای کلی حلقه] {e}")
            time.sleep(3)


if __name__ == "__main__":
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class HealthCheckHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write("ربات روشنه ✅".encode("utf-8"))

        def log_message(self, format, *args):
            pass

    def run_health_server():
        port = int(os.environ.get("PORT", 10000))
        server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
        print(f"🌐 سرور health-check روی پورت {port} روشن شد.")
        server.serve_forever()

    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()

    try:
        run_health_server()
    except KeyboardInterrupt:
        print("\nربات متوقف شد.")
