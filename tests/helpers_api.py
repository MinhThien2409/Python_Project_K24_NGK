# -*- coding: utf-8 -*-
"""Tiện ích dùng chung cho các file test nhóm 2 trở đi (đặt cùng thư mục với file test)."""
import json
import os

import pymysql
import pytest
import requests

URL = os.environ.get("POBBY_URL", "http://localhost:5000")
MK = "123456"
KET_QUA = {}          # { "TC-001": {"actual": "...", "pass": True/False} }


# ───────────────────────── tiện ích ─────────────────────────
def db():
    return pymysql.connect(
        host=os.environ.get("POBBY_DB_HOST", "localhost"),
        port=int(os.environ.get("POBBY_DB_PORT", 3306)),
        user=os.environ.get("POBBY_DB_USER", "root"),
        password=os.environ.get("POBBY_DB_PASSWORD", "12345"),
        database=os.environ.get("POBBY_DB_NAME", "PobbyDB"),
        charset="utf8mb4", autocommit=True,
        cursorclass=pymysql.cursors.DictCursor)


def truy_van(sql, args=()):
    c = db()
    try:
        with c.cursor() as cur:
            cur.execute(sql, args)
            return cur.fetchall()
    finally:
        c.close()


def thuc_thi(sql, args=()):
    c = db()
    try:
        with c.cursor() as cur:
            cur.execute(sql, args)
    finally:
        c.close()


class Ghi:
    """Gom các bước của một TC thành chuỗi Actual result."""
    def __init__(self, tc):
        self.tc, self.dong, self.ok = tc, [], True

    def goi(self, s, method, path, nhan="", **kw):
        r = s.request(method, URL + path, **kw)
        try:
            j = r.json()
        except ValueError:
            j = {}
        txt = f"{method} {path}"
        if "json" in kw:
            gon = {k: (v[:12] + f"…({len(v)} ký tự)" if isinstance(v, str) and len(v) > 40 else v)
                   for k, v in kw["json"].items()}
            txt += " " + json.dumps(gon, ensure_ascii=False)
        txt += f" -> HTTP {r.status_code}, status={j.get('status')}, message=\"{j.get('message', '')}\""
        self.dong.append((nhan + ": " if nhan else "") + txt)
        return r, j

    def ghi_chu(self, text):
        self.dong.append(text)

    def kiem(self, dieu_kien, mo_ta):
        self.dong.append(("[ĐÚNG] " if dieu_kien else "[SAI] ") + mo_ta)
        self.ok = self.ok and bool(dieu_kien)
        return dieu_kien

    def xong(self):
        KET_QUA[self.tc] = {"actual": "\n".join(self.dong), "pass": self.ok}
        assert self.ok, f"{self.tc} FAIL:\n" + "\n".join(self.dong)


def dang_nhap(user, mk=MK):
    s = requests.Session()
    r = s.post(URL + "/api/dang-nhap", json={"tendangnhap": user, "mat_khau": mk})
    return s, r.json()


