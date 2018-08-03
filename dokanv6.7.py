import requests
import sqlite3
import random
import uuid
import sys
import base64
import hmac
import hashlib
import time
import traceback
import os
import json
import threading
import sys
import pickle
import cv2

try:
    from urllib.parse import urlparse
except ImportError:
     from urlparse import urlparse
from datetime import datetime, timedelta
from queue import Queue
from pprint import pprint
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains

import settings
settings.init()
import sampleCollector


DBVERSION = 4

if not os.path.isfile("config.json"):
    with open("config.json", "w") as configfile:
        configfile.write(
            '{"proxy_for_acct_creation":false, "proxy_for_gift_collect":false, "proxy_list":"proxies.txt"}')

with open("config.json", "r") as configfile:
    config = json.load(configfile)

try:
    with open("cardnames.json", "r") as cardnamesfile:
        cardnames = json.load(cardnamesfile)
except:
    print("There is an error with cardnames.json file. Ignoring card names")
    cardnames = {}

use_proxy_1 = config["proxy_for_acct_creation"]
use_proxy_2 = config["proxy_for_gift_collect"]
proxy_file = config["proxy_list"]

if use_proxy_1 or use_proxy_2:
    with open(proxy_file, "r") as pfile:
        proxy_list = pfile.readlines()


def proxy(w):
    if w == 1 and use_proxy_1:
        p = random.choice(proxy_list)
    elif w == 2 and use_proxy_2:
        p = random.choice(proxy_list)
    else:
        return None

    if p.startswith('socks5'):
        return {'http': 'socks5://' + p.strip(), 'https': 'socks5://' + p.strip()}
    else:
        return {'http': 'http://' + p.strip(), 'https': 'https://' + p.strip()}

def proxy2():
    if use_proxy_1 or use_proxy_2:
        p = random.choice(proxy_list)
        return p.strip()
    else:
        return None

def cardname(cardid):
    try:
        return cardnames[str(cardid)]
    except:
        return None

def cardid(cardname):
    cardids = []
    try:
        for k, v in cardnames.items():
            if cardname in v:
                cardids.append(k)
    except:
        pass

    return cardids

def location_menu():
    while True:
        try:
            print("==================================")
            print("Location Menu:")
            print("\t1- US")
            print("\t2- JP")

            lm = int(input("Select > "))
            [1, 2].index(lm)
            break
        except:
            pass
    return lm


def operation_menu():
    while True:
        try:
            print("==================================")
            print("Operation Menu:")
            print("\t1- Create a new accounts")
            print("\t2- Signin and collect gifts")
            print("\t3- Transfer account _to_ real device")
            print("\t4- Transfer account _from_ real device")
            print("\t5- Create accounts and open packs")
            print("\t6- Signin and open packs")
            print("\t7- Import csv")
            print("\t8- Export csv")
            print("\t9- Print user database")
            print("\t10- Print card users database")
            print("\t11- Print stones")
            print("\t12- Search users with card name")
            print("\t20- Schedule")
            print("\t61- Convert accounts from Android to iOS")
            print("\t62- Convert accounts from iOS to Android")
            print("\t71- Import from dokan v6.3")
            print("\t72- Merge data from another db")
            print("\t123654789- Delete user from database")
            print("\t147852369- Reset user database")
            print("\t0- Exit")

            om = int(input("Select > "))
            break
        except:
            pass

    return om


def platform_menu(a=False):
    while True:
        try:
            print("==================================")
            print("Platform Menu:")
            print("Platform:")
            print("\t1- Android")
            print("\t2- iOS")
            if a:
                print("\t3- All")
            pm = int(input("Select > "))
            break
        except:
            pass

    if int(pm) == 1:
        platform = 'android'
    elif int(pm) == 2:
        platform = 'ios'
    elif int(pm) == 3 and a:
        platform = 'all'
    else:
        print("Invalid Selection!")
        return platform_menu(a)
    return platform


def generate_device(Platform):
    if Platform == "android":
        device, device_model, os = random.choice([
            ('HUAWEI', 'HUAWEI RIO-CL00', '4.4.2'),
            ('Samsung', 'Samsung SM-G9500', '6.1'),
            ('Samsung', 'Samsung SM-T820', '6.1'),
            ('Samsung', 'Samsung SM-A7200', '6.1'),
            ('Samsung', 'Samsung SM-A3200', '6.1'),
            ('Samsung', 'Samsung SM-C7010', '6.1'),
            ('Samsung', 'Samsung SM-A8100', '6.1'),
            ('Samsung', 'Samsung SM-J310F', '6.1'),
            ('Samsung', 'Samsung SM-C7000', '6.1'),
            ('Samsung', 'Samsung SM-A5300', '6.1'),
            ('Samsung', 'Samsung SM-J7270', '6.1')
        ])
    else:
        device, device_model, os = random.choice([
            ('iphone', '4s', '9.0.1')
        ])

    return (device, device_model, os)


def generate_ad_id():
    return str(uuid.uuid4()).lower()


def generate_unique_id():
    return generate_ad_id() + ':' + generate_ad_id().replace('-', '')[-16:]


def generate_mac(method, url, mac_secret, mac_id):
    uri = urlparse(url)
    ts = str((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds()).split(".")[0]
    nonse = str(ts) + ":" + str(uuid.uuid4().hex)
    value = str(ts) + "\n" + str(nonse) + "\n" + str(method) + "\n" + str(uri.path) + str(uri.query) + "\n" + str(
        uri.hostname) + "\n" + str(3001) + "\n\n"
    key = mac_secret.encode()
    value = value.encode()
    mac = base64.standard_b64encode(hmac.new(key, value, hashlib.sha256).digest())
    return """id="{}", nonce="{}", ts="{}", mac="{}\"""".format(mac_id, nonse, ts, mac.decode())


def import_csv():
    print("File format:")
    print("ad_id,unique_id,identifier,platform")
    filename = input("Enter file> ")
    if not os.path.isfile(filename):
        print("File not found")
        return False

    checklogin = input("Check login? 1-True 2-False >")
    users = []
    with open(filename, "r") as csvfile:
        for line in csvfile.readlines():
            try:
                ad_id, unique_id, identifier, platform = line.strip().split(',')
                users.append((ad_id, unique_id, identifier, platform))
            except:
                print("Failed to process line: {}".format(line.strip()))

    for ad_id, unique_id, identifier, platform in users:
        try:
            if checklogin == "1":
                resp = sign_in((ad_id, unique_id, platform, country, currency, identifier, None, None))
                try:
                    resp["secret"]
                except:
                    print("Login failure for {}".format(str((ad_id, unique_id, identifier, platform))))
                    continue
                resp3 = user((ad_id, unique_id, platform, country, currency, identifier, None, None), resp)
                user_id = resp3['user']['id']
                name = resp3['user']['name']
            else:
                country = None
                currency = None
                name = None
                user_id = None
            idx = save_user_data2(ad_id, unique_id, platform, country, currency, identifier, name, user_id)
        except:
            print("Login failure with this user:{}".format(str((ad_id, unique_id, identifier, platform))))
            print(traceback.format_exc())

    print("..Finish")


def import_from_63():
    if lm == 2:
        userdatafiles = ("userdata.jp", "userdata.jp.cards")
    elif lm == 1:
        userdatafiles = ("userdata", "userdata.cards")

    for datafile in userdatafiles:
        try:
            with open(datafile, "rb") as userdata:
                user_data = pickle.load(userdata)
        except:
            user_data = {'android': [], 'iOS': []}

        # ~ print(user_data)
        for k, v in user_data.items():
            for v_ in v:
                # ~ print(v_)
                if ".cards" not in datafile:
                    ad_id, unique_id, platform, country, currency, identifier, name, _id = v_
                    card_ids = set()
                else:
                    ad_id, unique_id, platform, country, currency, identifier, name, _id, card_ids = v_

                cards = ','.join(str(x) for x in card_ids)

                save_user_data2(ad_id, unique_id, platform, country, currency, identifier, name, _id, cards)


def export_csv():
    dbselection = input("Which used db do you want to export:\n\t1-General User DB\t2-Card Users DB\n\t\tSelect> ")
    mode = input(
        "1- Export All Users\n2- Export Selected Users\n3- Export by Card IDs\n4- Export by stone\nSelection > ")
    if dbselection == "1":
        carddb = False
    elif dbselection == "2":
        carddb = True
    else:
        return

    idxlist = []

    if mode == "2":
        userindexmap_, users_ = print_user_database(carddb=carddb)
        user_indexes = input("Enter user indexes (e.g. 43,125,21) > ")

        for index in user_indexes.split(','):
            idxlist.append(str(userindexmap_[int(index)]))
    elif mode == "3":
        cards = input("Enter cards ids (e.g. 2312313,3213131) > ")
        cardids = cards.strip().split(',')

    if mode in ["1", "2"]:
        user_data = load_user_data(carddb=carddb)
    elif mode in ["3"]:
        user_data = load_user_data_by_cardids(cardids)
    elif mode == "4":
        platform = platform_menu(a=True)
        userindexmap, userlist = print_user_database(p=False, platform=platform, carddb=carddb)
        threads = input("Enter number of parallel runs (Do not overcharge :) ) > ")
        stones = int(input("Enter minimum number of stones > "))

        ts = []
        q = Queue()
        for i in range(0, int(threads)):
            m = i * int(int(len(userlist)) / int(threads))
            mx = (i + 1) * int(int(len(userlist)) / int(threads)) if i != int(threads) - 1 else (i + 1) * int(
                int(len(userlist)) / int(threads)) + int(len(userlist)) % int(threads)
            usrs = userlist[m:mx]
            t = threading.Thread(target=load_users_with_stones, args=(usrs, q, stones))
            ts.append(t)
            t.start()

        ccc = 0
        while True:
            m = q.get()
            if m == None:
                ccc += 1
                if ccc == int(threads):
                    break
            else:
                print(m)
                idxlist.append(int(m))

        user_data = load_user_data(carddb=carddb)

    with open("userdata_export.csv", "w") as exportfile:
        for idx, ad_id, unique_id, platform, country, currency, identifier, name, _id, card_id, stones in user_data:
            if mode == "2" and str(idx) not in idxlist:
                continue
            elif mode == "4" and int(_id) not in idxlist:
                continue
            exportfile.write("{},{},{},{}\n".format(ad_id, unique_id, identifier, platform))
    if carddb:
        with open("userdata_export_with_card_info.csv", "w") as exportfile:
            for idx, ad_id, unique_id, platform, country, currency, identifier, name, _id, card_id in user_data:
                if mode == "2" and str(idx) not in idxlist:
                    continue
                elif mode == "4" and int(_id) not in idxlist:
                    continue
                exportfile.write("{};{};{};{};{}\n".format(ad_id, unique_id, identifier, platform, card_id))

    print("Check userdata_export.csv")
    if carddb:
        print("Check userdata_export_with_card_info.csv")


def merge_data_from_another_db():
    dbname = input("Enter full path of the other db >")
    conn = sqlite3.connect(userdatafile)
    conn.execute("attach '{}' as dba".format(dbname))
    conn.execute("begin")
    conn.execute(
        "insert or replace into userdata(ad_id,unique_id,platform,country,currency,identifier,name,id,cards) select ad_id,unique_id,platform,country,currency,identifier,name,id,cards from dba.userdata")
    conn.commit()
    conn.execute("detach database dba")


def save_user_data(q, store=True, qo=None):
    conn = sqlite3.connect(userdatafile)
    c = conn.cursor()
    created_accounts = []
    while True:
        t = q.get()
        if t == None:
            if qo:
                qo.put(None)
            break
        sign_up, sign_up_resp = t
        user_data = [sign_up['user_account']['ad_id'],
                     sign_up['user_account']['unique_id'],
                     sign_up['user_account']['platform'],
                     sign_up['user_account']['country'],
                     sign_up['user_account']['currency'],
                     sign_up_resp['identifier'],
                     sign_up_resp['user']['name'],
                     sign_up_resp['user']['id']]
        if store:
            c.execute('INSERT INTO userdata(ad_id,unique_id,platform,country,currency,identifier,name,id) \
                       VALUES (?,?,?,?,?,?,?,?)', (sign_up['user_account']['ad_id'],
                                                   sign_up['user_account']['unique_id'],
                                                   sign_up['user_account']['platform'],
                                                   sign_up['user_account']['country'],
                                                   sign_up['user_account']['currency'],
                                                   sign_up_resp['identifier'],
                                                   sign_up_resp['user']['name'],
                                                   sign_up_resp['user']['id']))

        created_accounts.append(user_data)
        if qo:
            qo.put(user_data)

        conn.commit()
    conn.close()
    return created_accounts


def save_user_data2(ad_id, unique_id, platform, country, currency, identifier, name, _id, card_id=None):
    conn = sqlite3.connect(userdatafile)
    c = conn.cursor()

    c.execute('INSERT or replace INTO userdata(ad_id,unique_id,platform,country,currency,identifier,name,id,cards) \
                       VALUES (?,?,?,?,?,?,?,?,?)',
              (ad_id, unique_id, platform, country, currency, identifier, name, _id, card_id))

    idx = c.lastrowid
    conn.commit()
    conn.close()

    return idx


def save_user_data3(q):
    conn = sqlite3.connect(userdatafile)
    c = conn.cursor()
    while True:
        item = q.get()
        # ~ print("----" + str(item))
        if item == None:
            break
        ad_id, unique_id, platform, country, currency, identifier, name, _id, card__ = item

        c.execute('SELECT * FROM userdata WHERE id=?', (_id,))
        res = c.fetchone()
        # ~ print(res)
        if res:
            a, b, cc, d, e, f, g, h, i, j, k = res
            if j:
                cards = j + ',' + str(card__)
            else:
                if card__:
                    cards = str(card__)
                else:
                    cards = None
            # ~ c.execute('update userdata set cards=? where ad_id=?', (cards, ad_id,))
        else:
            if card__:
                cards = str(card__)
            else:
                cards = None

        c.execute('INSERT or replace INTO userdata(ad_id,unique_id,platform,country,currency,identifier,name,id,cards) \
                    VALUES (?,?,?,?,?,?,?,?,?)',
                  (ad_id, unique_id, platform, country, currency, identifier, name, _id, cards))
        conn.commit()
    conn.close()


def delete_users_using_queue(q, qo):
    conn = sqlite3.connect(userdatafile)
    c = conn.cursor()

    while True:
        item = q.get()
        print(item)
        qo.put(item)
        if item == None:
            break
        ad_id, unique_id, platform, country, currency, identifier, name, id_, xxxx = item
        c.execute("delete from userdata where ad_id=?", (ad_id,))

    conn.commit()
    conn.close()


def delete_user_from_database():
    dbselection = input("Which used db do you want to export:\n\t1-General User DB\t2-Card Users DB\n\t\tSelect> ")

    if dbselection == "1":
        carddb = False
    elif dbselection == "2":
        carddb = True
    else:
        return

    user_data = load_user_data(carddb)
    platform = platform_menu()
    userindexmap_, users_ = print_user_database(platform=platform, carddb=carddb)

    print("Select mode:")
    print("1 - Enter user indexes to delete")
    print("2 - Enter user indexes to keep and delete others")
    mode = input("Selection > ")

    idx = input("Enter user indexes (e.g. 1,5,4,7) >")

    idxlist = []
    for index in idx.split(','):
        idxlist.append(str(userindexmap_[int(index)]))

    conn = sqlite3.connect(userdatafile)
    c = conn.cursor()
    if mode == "1":
        for i in idxlist:
            c.execute("delete from userdata where idx=?", (int(i),))
    elif mode == "2":
        donotdelete = str(tuple(idxlist))
        c.execute("delete from userdata where platform='" + platform + "' and idx not in " + donotdelete)
    conn.commit()
    conn.close()

    print_user_database(platform=platform, carddb=carddb)


def reset_user_data():
    conn = sqlite3.connect(userdatafile)
    c = conn.cursor()
    c.execute("delete from userdata")
    conn.commit()
    conn.close()


def load_user_data(carddb=False):
    conn = sqlite3.connect(userdatafile)
    c = conn.cursor()

    if carddb == 'all':
        c.execute("select * from userdata")
    elif carddb:
        c.execute("select * from userdata where cards is not null")
    else:
        c.execute("select * from userdata where cards is null")
    ress = c.fetchall()
    return ress


def load_user_data_by_cardids(cardids=[]):
    conn = sqlite3.connect(userdatafile)
    r = []
    for cardid in cardids:
        sql = "select * from userdata where cards like '%{}%'".format(str(cardid))
        c = conn.cursor()
        c.execute(sql)
        r.extend(c.fetchall())
    return list(set(r))


def print_user_database(p=True, platform=None, carddb=False):
    if not platform:
        platform = platform_menu(a=True)

    ress = load_user_data(carddb)
    users = []
    userindex = 1
    userindexmap = {}
    for res in ress:
        userid, ad_id, unique_id, platform_, country, currency, identifier, name, id_, card_id, stones = res
        if p and (platform == 'all' or platform_ == platform):
            userindexmap[userindex] = userid
            print("==============")
            print("[{}]============================".format(userindex))
            print("ad_id: {}".format(ad_id))
            print("unique_id: {}".format(unique_id))
            print("platform: {}".format(platform_))
            print("country: {}".format(country))
            print("currency: {}".format(currency))
            print("identifier: {}".format(identifier))
            print("name: {}".format(name))
            print("id: {}".format(id_))
            print("stones: {} (offline)".format(stones))
            if carddb:
                cids = []
                if card_id:
                    for cid in card_id.split(','):
                        if cid != "None":
                            cn = cardname(cid)
                            if cn:
                                cids.append("{}({})".format(cid, cn))
                            else:
                                cids.append(cid)

                print("card_id: {}".format(','.join(cids)))

            userindex += 1

        if platform == 'all':
            users.append((ad_id, unique_id, platform_, country, currency, identifier, name, id_))
        else:
            if platform == platform_:
                users.append((ad_id, unique_id, platform_, country, currency, identifier, name, id_))

    return userindexmap, users


def print_stones(userlist, q):
    for user_account in userlist:
        resp = sign_in(user_account)
        try:
            resp["secret"]
        except:
            print("Login failure for {}".format(str(user_account)))
            continue

        resp3 = user(user_account, resp)
        # ~ print(resp3)
        stone = resp3['user']['stone']
        update_user_stone(user_account, stone)
        ad_id, unique_id, platform, country, currency, identifier, name, id_ = user_account
        q.put("id: {}\nidentifier: {}\nstone: {} (online)\n-----\n".format(id_, identifier, stone))
    q.put(None)


def load_users_with_stones(userlist, q, stones):
    for user_account in userlist:
        resp = sign_in(user_account)
        try:
            resp["secret"]
        except:
            print("Login failure for {}".format(str(user_account)))
            continue

        resp3 = user(user_account, resp)
        # ~ print(resp3)
        stone = resp3['user']['stone']
        if int(stone) >= stones:
            ad_id, unique_id, platform, country, currency, identifier, name, id_ = user_account
            q.put(id_)
    q.put(None)


def transfer_account_to_real_device():
    dbselection = input("Which used db do you want to export:\n\t1-General User DB\t2-Card Users DB\n\t\tSelect> ")

    if dbselection == "1":
        carddb = False
    elif dbselection == "2":
        carddb = True
    else:
        return

    userindexmap, userlist = print_user_database(carddb=carddb)
    print("==================================")
    userid = input("Enter User Index: ")
    userid = userindexmap[int(userid)]
    # ~ user = userlist[int(userid)]

    conn = sqlite3.connect(userdatafile)
    c = conn.cursor()

    c.execute("select * from userdata where idx=?", (userid,))
    res = c.fetchone()
    print(res)
    idx, ad_id, unique_id, platform, country, currency, identifier, name, id_, cards, stones = res
    conn.commit()
    conn.close()

    user = (ad_id, unique_id, platform, country, currency, identifier, name, id_)
    resp = sign_in(user)
    try:
        resp["secret"]
    except:
        print("Login failure for {}".format(str(user)))
        return
    resp4 = auth_link_codes(user, resp)

    link_code, user_id = resp4['link_code'], id_

    users = userlist

    conn = sqlite3.connect(userdatafile)
    c = conn.cursor()

    c.execute("delete from userdata where idx=?", (userid,))
    conn.commit()
    conn.close()

    # ~ print_user_database(platform=platform, carddb=carddb)

    print("==================================")
    print("link_code={}".format(link_code))
    print("user_id={}".format(user_id))


def transfer_account_from_real_device():
    platform = platform_menu()
    print("==================================")
    link_code = input("Enter link code: ")
    user_id = input("Enter user id: ")
    resp = auth_link_codes_validate(link_code, user_id, platform)

    if not resp['link_code_is_valid']:
        print("Invalid link code!")
    elif not resp['user_is_valid']:
        print("Invalid user id")
    else:
        name = resp['user_name']

        ad_id, unique_id, identifier = auth_link_codes_after_transfer(link_code, platform)

        idx = save_user_data2(ad_id, unique_id, platform, country, currency, identifier, name, user_id)

        print("User transferred as User #{}".format(idx))


def convert_accounts(s, d):
    dbselection = input("Which used db do you want to export:\n\t1-General User DB\t2-Card Users DB\n\t\tSelect> ")

    if dbselection == "1":
        carddb = False
    elif dbselection == "2":
        carddb = True
    else:
        return

    userindexmap, userlist = print_user_database(carddb=carddb, platform=s, p=False)

    for user in userlist:
        ad_id, unique_id, platform, country, currency, identifier, name, id_ = user
        resp = sign_in(user)
        try:
            resp["secret"]
        except:
            print("Login failure for {}".format(str(id_)))
            continue
        resp4 = auth_link_codes(user, resp)

        link_code, user_id = resp4['link_code'], id_

        conn = sqlite3.connect(userdatafile)
        c = conn.cursor()

        c.execute("select * from userdata where id=?", (user_id,))
        res = c.fetchone()
        idx, ad_id, unique_id, platform, country, currency, identifier, name, id_, cards, stones = res

        c.execute("delete from userdata where id=?", (user_id,))
        conn.commit()
        conn.close()

        resp = auth_link_codes_validate(link_code, user_id, d)

        if not resp['link_code_is_valid']:
            print("Invalid link code!")
        elif not resp['user_is_valid']:
            print("Invalid user id")
        else:
            name = resp['user_name']

            ad_id, unique_id, identifier = auth_link_codes_after_transfer(link_code, d)

            idx = save_user_data2(ad_id, unique_id, d, country, currency, identifier, name, user_id, cards)

            print("User transferred as User #{}".format(idx))


def create_new_account(k, q, platform, account_count):
    headers1 = headers.copy()
    headers1['X-Platform'] = platform
    headers1['User-Agent'] = None

    created_accounts = []

    for i in range(0, account_count):
        time.sleep(1)
        print("Create account {}#{}".format(k, i + 1))
        try:
            ad_id = generate_ad_id()
            device, device_model, os_version = generate_device(platform)
            unique_id = generate_unique_id()

            if lm == 1:
                sign_up_data = {
                    "user_account": {
                        "ad_id": ad_id,
                        "country": country,
                        "currency": currency,
                        "device": device,
                        "device_model": device_model,
                        "os_version": os_version,
                        "platform": platform,
                        "unique_id": unique_id
                    }
                }
            elif lm == 2:
                sign_up_data = {
                    "user_account": {
                        "device": device,
                        "device_model": device_model,
                        "os_version": os_version,
                        "platform": platform,
                        "unique_id": unique_id
                    }
                }

            r = requests.post(host + '/auth/sign_up', json=sign_up_data, headers=headers1, proxies=proxy(1))
            # ~ pprint(r.json())
            if not r.ok:
                try:
                    if r.json()["reason"] == "Require Captcha":
                        captcha_url = r.json()["captcha_url"]
                        captcha_session_key = r.json()["captcha_session_key"]
                        chrome_options = webdriver.ChromeOptions()
                        chrome_options.add_argument("--start-maximized")
                        prx = proxy2()
                        if prx:
                            chrome_options.add_argument('--proxy-server=http://%s' % prx)

                        if(settings.BROWSER is None):    
                            settings.init_browser(chrome_options)
                        wd = settings.BROWSER
                        for kkkkk in range(0, 3):                 
                            sampleCollector.solveCaptcha(captcha_url)                            
                            text = None
                            tmout = 60
                            print("{}# Solve it in {} seconds".format(k, tmout))
                            for iiii in range(0, tmout):
                                try:
                                    text = wd.find_element_by_tag_name('pre').text
                                    break
                                except:
                                    print("{}# {}".format(k, tmout - iiii))
                                    time.sleep(1)

                            # wd.quit()

                            if not text:
                                continue

                            j = json.loads(text)
                            if j['captcha_result'] == 'success':
                                # wd.quit()
                                break

                        # try:
                        #     wd.quit()
                        # except:
                        #     pass

                        sign_up_data['captcha_session_key'] = captcha_session_key
                        r = requests.post(host + '/auth/sign_up', json=sign_up_data, headers=headers1, proxies=proxy(1))
                except:
                    print(r.json())
                    print(traceback.print_exc())
                    continue
            if lm == 2:
                sign_up_data["user_account"]["ad_id"] = None
                sign_up_data["user_account"]["country"] = None
                sign_up_data["user_account"]["currency"] = None

            try:
                r.json()['error']
                print("Account create error for user {}#{}".format(k, i + 1))
                print(r.json())
            except:
                q.put((sign_up_data, r.json()))
                print(
                    "Account created {}#{}: {}, {}".format(k, i + 1, r.json()['user']['name'], r.json()['user']['id']))
        except:
            if Error or debug:
                with open(os.path.join("errors", "account_create_error_{}_{}".format(k, i)), "w") as errfile:
                    errfile.write(str(sign_up_data))
                    traceback.print_exc(file=errfile)

    return created_accounts


def sign_in_and_open_pack(accounts=None, threads=None, platform=None, gasha_ids=None, card_ids=None, mode=None,
                          single=None, store_limit=None, loops=None, delete=False):
    if not accounts:
        threads = input("Enter number of parallel runs (Do not overcharge :) ) > ")
        platform = platform_menu()
        gasha_ids = input("Enter pack ids (e.g. 1234,1235,1236) > ")
        card_ids = input("Enter card ids (e.g. 4214,4324,5435) > ")
        mode = int(input("1- Ordinary\t2- Wanted >"))
        # ~ loop = input("How many times will the pack be opened (-1 for MAX value)> ")
        single = input("1- Single\t 2- Multi > ")
        store_limit = int(input("Enter lower limit of found cards to store account > "))

        loops = {}
        for gasha_id in gasha_ids.split(','):
            loops[gasha_id] = int(input("How many times will pack {} be opened? (-1 for MAX) > ".format(gasha_id)))

        dbselection = input("Which used db do you want to use:\n\t1-General User DB\t2-Card Users DB\n\t\tSelect> ")

        if dbselection == "1":
            userindexmap, accounts = print_user_database(p=False, platform=platform)
        elif dbselection == "2":
            userindexmap, accounts = print_user_database(p=False, platform=platform, carddb=True)
        else:
            return

    q = Queue()
    qo = Queue()

    # ~ t1 = threading.Thread(target=delete_users_using_queue, args=(q,qo,))
    # ~ t1.start()

    # ~ t2 = threading.Thread(target=save_user_data3, args=(qo,))
    t2 = threading.Thread(target=save_user_data3, args=(q,))
    t2.start()

    account_count = len(accounts)

    ts = []
    for i in range(0, int(threads)):
        m = i * int(int(account_count) / int(threads))
        mx = (i + 1) * int(int(account_count) / int(threads)) if i != int(threads) - 1 else (i + 1) * int(
            int(account_count) / int(threads)) + int(account_count) % int(threads)
        accts = accounts[m:mx]
        t = threading.Thread(target=collect_gifts, args=(
        i, accts, True, gasha_ids.split(','), card_ids, loops, single, q, store_limit, mode, delete,))
        ts.append(t)
        t.start()

    while True:
        b = True
        for t in ts:
            if t.is_alive():
                b = False
                time.sleep(1)
                break
        if b:
            break

    q.put(None)


def sign_in_and_collect():
    threads = input("Enter number of parallel runs (Do not overcharge :) ) > ")
    dbselection = input("Which used db do you want to use:\n\t1-General User DB\t2-Card Users DB\t3-Both DBs\n\t\tSelect> ")

    if dbselection == "1":
        userindexmap, users = print_user_database(p=False)
    elif dbselection == "2":
        userindexmap, users = print_user_database(p=False, carddb=True)
    elif dbselection == "3":
        userindexmap, users = print_user_database(p=False, carddb="all")
    else:
        return

    ts = []
    for i in range(0, int(threads)):
        m = i * int(len(users) / int(threads))
        mx = (i + 1) * int(len(users) / int(threads)) if i != int(threads) - 1 else (i + 1) * int(
            len(users) / int(threads)) + len(users) % int(threads)
        accts = users[m:mx]
        t = threading.Thread(target=collect_gifts, args=(i, accts,))
        ts.append(t)
        t.start()

    while True:
        b = True
        for t in ts:
            if t.is_alive():
                b = False
                time.sleep(1)
                break
        if b:
            break


def update_user_stone(user_account, stone):
    ad_id, unique_id, platform, country, currency, identifier, name, id_ = user_account
    conn = sqlite3.connect(userdatafile)
    c = conn.cursor()
    c.execute("update userdata set stone=? where id=?", (stone,id_,))
    conn.commit()
    conn.close()


def collect_gifts(k, user_accounts, open_pack=False, gasha_ids=[], card_ids=None, loops={}, single=1, q=None,
                  store_limit=1, mode=1, delete=False):
    for user_account in user_accounts:
        # ~ ad_id, unique_id, platform, country, currency, identifier, name, id_ = user_account
        # ~ q.put((ad_id, unique_id, platform, country, currency, identifier, name, id_, 111111111))
        # ~ continue
        resp8 = ""
        try:
            t = time.time()
            print("Collect for account {}#{}".format(k, user_accounts.index(user_account) + 1))
            collect_results = ""
            resp = sign_in(user_account)
            collect_results += '\nsign_in\n' + str(resp)
            try:
                resp["secret"]
            except:
                print("Login failure for {}".format(str(user_account)))
                continue
            resp2 = comeback_campaigns(user_account, resp)
            collect_results += '\ncomeback_campaigns\n' + str(resp2)
            resp3 = user(user_account, resp)
            collect_results += '\nuser\n' + str(resp3)
            resp4 = teams(user_account, resp)
            collect_results += '\nteams\n' + str(resp4)
            resp5 = cards(user_account, resp)
            collect_results += '\ncards\n' + str(resp5)
            resp8 = tutorial(user_account, resp, 20)
            collect_results += '\ntutorial\n' + str(resp8)
            resp8 = tutorial_gasha(user_account, resp)
            collect_results += '\ntutorial_gasha\n' + str(resp8)
            resp8 = tutorial(user_account, resp, 80)
            collect_results += '\ntutorial\n' + str(resp8)
            resp8 = tutorial_finish(user_account, resp)
            collect_results += '\ntutorial_finish\n' + str(resp8)
            if lm == 1:
                resp8 = user2(user_account, resp)
                collect_results += '\nuser2\n' + str(resp8)
            elif lm == 1:
                resp8 = user_put(user_account, resp)
                collect_results += '\nuser_put\n' + str(resp8)
            resp8 = user_areas(user_account, resp)
            collect_results += '\nuser_areas\n' + str(resp8)
            # ~ resp8 = missions_put_forward(user_account, resp)
            # ~ collect_results += '\nmission_put_forward\n' + str(resp8)
            resp8 = tutorial(user_account, resp, 90)
            collect_results += '\ntutorial\n' + str(resp8)
            resp8 = login_bonus_accept(user_account, resp)
            collect_results += '\nlogin_bonus_accept\n' + str(resp8)
            resp8 = apologies_accept(user_account, resp)
            collect_results += '\napogolies_accept\n' + str(resp8)
            resp8 = gifts(user_account, resp)
            collect_results += '\ngifts\n' + str(resp8)
            gift_list = []
            for gift in resp8['gifts']:
                gift_list.append(gift['id'])
            if len(gift_list) == 0:
                print("No gift to collect for user {}#{}".format(k, user_accounts.index(user_account) + 1))
                if not open_pack:
                    continue
            resp8 = gifts_accept(user_account, resp, gift_list)
            collect_results += '\ngift_accept\n' + str(resp8)
            if open_pack:
                if mode == 2:
                    try:
                        with open("cardlist.json", "r") as cardsfile:
                            listedcards = json.load(cardsfile)
                    except:
                        listedcards = {"cards": []}
                else:
                    listedcards = {"cards": []}
                listedcards_ = listedcards["cards"]

                found_cards = []
                ad_id, unique_id, platform, country, currency, identifier, name, id_ = user_account
                for gasha_id in gasha_ids:
                    loop = loops[gasha_id]
                    if int(loop) == -1:
                        loop = 9999

                    for i in range(0, int(loop)):
                        print("Open pack {} for {}#{}".format(gasha_id, k, user_accounts.index(user_account) + 1))
                        if lm == 1:
                            resp8 = cards2(user_account, resp)
                        elif lm == 2:
                            resp8 = cards(user_account, resp)

                        collect_results += '\ncards\n' + str(resp8)
                        resp8 = gashas(user_account, resp)
                        collect_results += '\ngashas\n' + str(resp8)
                        # ~ print(single)
                        if str(single) == "2":
                            resp8 = gasha_draw(user_account, resp, gasha_id, i)
                        elif str(single) == "1":
                            resp8 = gasha_draw1(user_account, resp, gasha_id, i)

                        collect_results += '\ngashadraw\n' + str(resp8)

                        try:
                            found = False
                            for gasha_item in resp8['gasha_items']:
                                if gasha_item['item_type'] == 'Card' and str(gasha_item['item_id']) in card_ids.split(
                                        ","):
                                    ad_id, unique_id, platform, country, currency, identifier, name, id_ = user_account
                                    itemname = cardname(gasha_item['item_id'])
                                    found = True
                                    if gasha_item['item_id'] not in found_cards:
                                        if itemname:
                                            print("Found item: {}({}) for {}#{} ({})".format(gasha_item['item_id'],
                                                                                             itemname, k,
                                                                                             user_accounts.index(
                                                                                                 user_account) + 1,
                                                                                             id_))
                                        else:
                                            print("Found item: {} for {}#{} ({})".format(gasha_item['item_id'], k,
                                                                                         user_accounts.index(
                                                                                             user_account) + 1, id_))
                                        found_cards.append(gasha_item['item_id'])
                                    if int(loop) == -1:
                                        break
                            if found:
                                if int(mode) == 2:
                                    for gasha_item in resp8['gasha_items']:
                                        if gasha_item['item_type'] == 'Card' and gasha_item['item_id'] in listedcards_:
                                            ad_id, unique_id, platform, country, currency, identifier, name, id_ = user_account
                                            itemname = cardname(gasha_item['item_id'])

                                            if gasha_item['item_id'] not in found_cards:
                                                if itemname:
                                                    print("Found item: {}({}) for {}#{} ({})".format(
                                                        gasha_item['item_id'], itemname, k,
                                                        user_accounts.index(user_account) + 1, id_))
                                                else:
                                                    print(
                                                        "Found item: {} for {}#{} ({})".format(gasha_item['item_id'], k,
                                                                                               user_accounts.index(
                                                                                                   user_account) + 1,
                                                                                               id_))
                                                found_cards.append(gasha_item['item_id'])
                                if int(loop) == -1:
                                    break

                        except:
                            print("There is no card for {}#{}".format(k, user_accounts.index(user_account) + 1))
                            # ~ print(resp8)
                        # ~ time.sleep(random.randint(2,10))
                        time.sleep(0.1)

                if len(found_cards) >= store_limit:
                    if store_limit <= 0 and len(found_cards) == 0:
                        found_cards = [None]
                    for card_id in found_cards:
                        q.put((ad_id, unique_id, platform, country, currency, identifier, name, id_, card_id))
                else:
                    if delete:
                        conn = sqlite3.connect(userdatafile)
                        c = conn.cursor()
                        c.execute("delete from userdata where ad_id=?", (ad_id,))
                        conn.commit()
                        conn.close()

            if debug:
                with open("debug_{}_{}.log".format(k, user_accounts.index(user_account) + 1), "wb") as dfile:
                    dfile.write(bytes(collect_results, "utf-8"))
            print("..Finish {}#{}. Cost {} seconds".format(k, user_accounts.index(user_account) + 1,
                                                           int(time.time() - t)))
        except Exception as e:
            print("Failure for account {}#{}".format(k, user_accounts.index(user_account) + 1))
            print("Got exception ", e)
            print(resp8)
            try:
                if Error or debug:
                    with open(
                            os.path.join("errors", "error_resp_{}_{}".format(k, user_accounts.index(user_account) + 1)),
                            "wb") as errfile:
                        errfile.write(bytes(collect_results, "utf-8"))
                    with open(
                            os.path.join("errors", "error_resp_{}_{}".format(k, user_accounts.index(user_account) + 1)),
                            "a") as errfile:
                        traceback.print_exc(file=errfile)
            except:
                print("Logfile creation failure")
                print(traceback.format_exc())


def sign_in(user_account):
    url = host + '/auth/sign_in'
    ad_id, unique_id, platform, country, currency, identifier, name, id_ = user_account

    pw_acc = base64.standard_b64decode(identifier)
    pw_acc = pw_acc.decode()
    acc_pw = pw_acc.split(':')[1] + ":" + pw_acc.split(":")[0]
    BasicPwd = base64.standard_b64encode(acc_pw.encode()).decode()

    headers2 = headers.copy()
    if country:
        headers2['X-UserCountry'] = country
        headers2['X-UserCurrency'] = currency
    headers2['X-Platform'] = platform
    headers2['Authorization'] = "Basic " + BasicPwd
    headers2['User-Agent'] = None

    sign_in_data = {'ad_id': ad_id,
                    'unique_id': unique_id}

    r = requests.post(url, json=sign_in_data, headers=headers2, proxies=proxy(2))
    if not r.ok:
        try:
            if r.json()["reason"] == "Require Captcha":
                captcha_url = r.json()["captcha_url"]
                captcha_session_key = r.json()["captcha_session_key"]
                chrome_options = webdriver.ChromeOptions()
                chrome_options.add_argument("--start-maximized")
                prx = proxy2()
                if prx:
                    chrome_options.add_argument('--proxy-server=http://%s' % prx)
                
                if(settings.BROWSER is None):
                    settings.init_browser(chrome_options)
                wd = settings.BROWSER
                for kkkkk in range(0, 3):
                    sampleCollector.solveCaptcha(captcha_url)
                    text = None
                    tmout = 60
                    print("{}# Solve it in {} seconds".format(id_, tmout))
                    for iiii in range(0, tmout):
                        print(wd.page_source)
                        try:
                            text = wd.find_element_by_tag_name('pre').text
                            break
                        except:
                            print("{}# {}".format(id_, tmout - iiii))
                            time.sleep(1)

                    # wd.quit()

                    if not text:
                        continue

                    j = json.loads(text)
                    if j['captcha_result'] == 'success':
                        # wd.quit()
                        break

                # try:
                #     wd.quit()
                # except:
                #     pass

                sign_in_data['captcha_session_key'] = captcha_session_key
                r = requests.post(url, json=sign_in_data, headers=headers2, proxies=proxy(2))
        except KeyError: 
            print("Unable to sign in!")
            print("Status: {}".format(r.status_code))
            print("Text: {}".format(r.text))
            try:
                if r.json()['error']['code'] == 'oauth2_mac_rails/client_transferred':
                    conn = sqlite3.connect(userdatafile)
                    c = conn.cursor()
                    c.execute("delete from userdata where id=?", (int(id_),))
                    conn.commit()
                    conn.close()
            except:
                pass
            return False
        except ValueError:
            print("Line:1227 Failed to decode response as json")
            print("Response was \'%s\'"%(r.text))
            return False

    return r.json()


def auth_link_codes(user_account, sign_in_response):
    url = host + '/auth/link_codes'
    ad_id, unique_id, platform, country, currency, identifier, name, id_ = user_account
    MAC = generate_mac('POST', url, sign_in_response['secret'], sign_in_response['access_token'])

    headers3 = headers.copy()
    headers3['X-Platform'] = platform

    headers3['X-AssetVersion'] = str(int(time.time()))
    headers3['X-RequestVersion'] = '3'
    headers3['X-DatabaseVersion'] = str(int(time.time()))
    headers3['Authorization'] = "MAC " + MAC
    headers3['User-Agent'] = None

    r = requests.post(url, json={'eternal': True}, headers=headers3, proxies=proxy(2))
    return r.json()


def auth_link_codes_validate(link_code, user_id, platform):
    url = host + '/auth/link_codes/{}/validate'.format(link_code)

    headers3 = headers.copy()
    headers3['X-Platform'] = platform

    r = requests.post(url, json={"eternal": True, "user_account": {"platform": platform, "user_id": int(user_id)}},
                      headers=headers3, proxies=proxy(2))
    return r.json()


def auth_link_codes_after_transfer(link_code, platform):
    url = host + '/auth/link_codes/{}'.format(link_code)

    headers3 = headers.copy()
    headers3['X-Platform'] = platform

    device, device_model, os_version = generate_device(platform)
    unique_id = generate_unique_id()
    ad_id = generate_ad_id()

    auth_data = {
        "eternal": True,
        "old_user_id": "",
        "user_account": {
            "device": device,
            "device_model": device_model,
            "os_version": os_version,
            "platform": platform,
            "unique_id": unique_id
        }
    }

    r = requests.put(url, json=auth_data, headers=headers3, proxies=proxy(2))
    identifier = r.json()['identifiers'].replace('\n', '')
    return (ad_id, unique_id, identifier)


def comeback_campaigns(user_account, sign_in_response):
    url = host + '/comeback_campaigns/entry'
    ad_id, unique_id, platform, country, currency, identifier, name, id_ = user_account
    MAC = generate_mac('POST', url, sign_in_response['secret'], sign_in_response['access_token'])

    headers3 = headers.copy()
    headers3['X-Platform'] = platform

    headers3['X-AssetVersion'] = str(int(time.time()))
    headers3['X-RequestVersion'] = '3'
    headers3['X-DatabaseVersion'] = str(int(time.time()))
    headers3['Authorization'] = "MAC " + MAC
    headers3['User-Agent'] = None

    r = requests.post(url, data=None, headers=headers3, proxies=proxy(2))
    return r.json()


def user(user_account, sign_in_response):
    url = host + '/user'
    ad_id, unique_id, platform, country, currency, identifier, name, id_ = user_account
    MAC = generate_mac('GET', url, sign_in_response['secret'], sign_in_response['access_token'])

    headers3 = headers.copy()
    headers3['X-Platform'] = platform

    headers3['X-AssetVersion'] = str(int(time.time()))
    headers3['X-RequestVersion'] = '4'
    headers3['X-DatabaseVersion'] = str(int(time.time()))
    headers3['Authorization'] = "MAC " + MAC
    headers3['User-Agent'] = None

    r = requests.get(url, headers=headers3, proxies=proxy(2))
    return r.json()


def user2(user_account, sign_in_response):
    url = host + '/user'
    ad_id, unique_id, platform, country, currency, identifier, name, id_ = user_account
    MAC = generate_mac('GET', url, sign_in_response['secret'], sign_in_response['access_token'])

    headers3 = headers.copy()
    headers3['X-Platform'] = platform

    headers3['X-ClientVersion'] = '////'
    headers3['X-AssetVersion'] = '////'
    headers3['X-RequestVersion'] = '6'
    headers3['X-DatabaseVersion'] = '////'
    headers3['Authorization'] = "MAC " + MAC
    headers3['User-Agent'] = None

    r = requests.get(url, headers=headers3)
    return r.json()


def user_put(user_account, sign_in_response):
    url = host + '/user'
    ad_id, unique_id, platform, country, currency, identifier, name, id_ = user_account
    MAC = generate_mac('PUT', url, sign_in_response['secret'], sign_in_response['access_token'])

    data = {"user": {"name": name}}

    headers3 = headers.copy()
    headers3['X-Platform'] = platform
    headers3['X-AssetVersion'] = '0'
    headers3['X-RequestVersion'] = '10'
    headers3['X-DatabaseVersion'] = '////'
    headers3['Authorization'] = "MAC " + MAC

    r = requests.put(url, json=data, headers=headers3)
    return r.json()


def teams(user_account, sign_in_response):
    url = host + '/teams'
    ad_id, unique_id, platform, country, currency, identifier, name, id_ = user_account
    MAC = generate_mac('GET', url, sign_in_response['secret'], sign_in_response['access_token'])

    headers3 = headers.copy()
    headers3['X-Platform'] = platform

    headers3['X-AssetVersion'] = str(int(time.time()))
    headers3['X-RequestVersion'] = '4'
    headers3['X-DatabaseVersion'] = str(int(time.time()))
    headers3['Authorization'] = "MAC " + MAC

    r = requests.get(url, headers=headers3, proxies=proxy(2))
    return r.json()


def cards(user_account, sign_in_response):
    url = host + '/cards'
    ad_id, unique_id, platform, country, currency, identifier, name, id_ = user_account
    MAC = generate_mac('GET', url, sign_in_response['secret'], sign_in_response['access_token'])

    headers3 = headers.copy()
    headers3['X-Platform'] = platform

    headers3['X-AssetVersion'] = str(int(time.time()))
    headers3['X-RequestVersion'] = '4'
    headers3['X-DatabaseVersion'] = str(int(time.time()))
    headers3['Authorization'] = "MAC " + MAC

    r = requests.get(url, headers=headers3, proxies=proxy(2))
    return r.json()


def cards2(user_account, sign_in_response):
    url = host + '/cards'
    ad_id, unique_id, platform, country, currency, identifier, name, id_ = user_account
    MAC = generate_mac('GET', url, sign_in_response['secret'], sign_in_response['access_token'])

    headers3 = headers.copy()
    headers3['X-Platform'] = platform

    headers3['X-AssetVersion'] = '////'
    headers3['X-RequestVersion'] = '16'
    headers3['X-DatabaseVersion'] = '////'
    headers3['X-ClientVersion'] = '////'
    headers3['Authorization'] = "MAC " + MAC

    r = requests.get(url, headers=headers3)
    return r.json()


def tutorial_gasha(user_account, sign_in_response):
    url = host + '/tutorial/gasha'
    ad_id, unique_id, platform, country, currency, identifier, name, id_ = user_account
    MAC = generate_mac('POST', url, sign_in_response['secret'], sign_in_response['access_token'])

    headers3 = headers.copy()
    headers3['X-Platform'] = platform

    headers3['X-AssetVersion'] = str(int(time.time()))
    headers3['X-RequestVersion'] = '6'
    headers3['X-DatabaseVersion'] = str(int(time.time()))
    headers3['Authorization'] = "MAC " + MAC

    r = requests.post(url, data=None, headers=headers3, proxies=proxy(2))
    return r.json()


def tutorial_finish(user_account, sign_in_response):
    url = host + '/tutorial/finish'
    ad_id, unique_id, platform, country, currency, identifier, name, id_ = user_account
    MAC = generate_mac('PUT', url, sign_in_response['secret'], sign_in_response['access_token'])

    headers3 = headers.copy()
    headers3['X-Platform'] = platform

    headers3['X-AssetVersion'] = str(int(time.time()))
    headers3['X-RequestVersion'] = '5'
    headers3['X-DatabaseVersion'] = str(int(time.time()))
    headers3['Authorization'] = "MAC " + MAC

    r = requests.put(url, data=None, headers=headers3, proxies=proxy(2))
    return r.json()


def user_areas(user_account, sign_in_response):
    url = host + '/user_areas'
    ad_id, unique_id, platform, country, currency, identifier, name, id_ = user_account
    MAC = generate_mac('GET', url, sign_in_response['secret'], sign_in_response['access_token'])

    headers3 = headers.copy()
    headers3['X-Platform'] = platform

    headers3['X-ClientVersion'] = '////'
    headers3['X-AssetVersion'] = '////'
    headers3['X-RequestVersion'] = '6'
    headers3['X-DatabaseVersion'] = '////'
    headers3['Authorization'] = "MAC " + MAC

    r = requests.get(url, headers=headers3, proxies=proxy(2))
    return r.json()


def missions_put_forward(user_account, sign_in_response):
    url = host + '/missions/put_forward'
    ad_id, unique_id, platform, country, currency, identifier, name, id_ = user_account
    MAC = generate_mac('PUT', url, sign_in_response['secret'], sign_in_response['access_token'])

    headers3 = headers.copy()
    headers3['X-Platform'] = platform

    headers3['X-ClientVersion'] = '////'
    headers3['X-AssetVersion'] = '////'
    headers3['X-RequestVersion'] = '7'
    headers3['X-DatabaseVersion'] = '////'
    headers3['Authorization'] = "MAC " + MAC

    r = requests.put(url, data=None, headers=headers3, proxies=proxy(2))
    return r.json()


def tutorial(user_account, sign_in_response, progress):
    url = host + '/tutorial'
    ad_id, unique_id, platform, country, currency, identifier, name, id_ = user_account
    MAC = generate_mac('PUT', url, sign_in_response['secret'], sign_in_response['access_token'])

    headers3 = headers.copy()
    headers3['X-Platform'] = platform

    headers3['X-AssetVersion'] = str(int(time.time()))
    headers3['X-RequestVersion'] = '9'
    headers3['X-DatabaseVersion'] = str(int(time.time()))
    headers3['Authorization'] = "MAC " + MAC

    r = requests.put(url, json={'progress': progress}, headers=headers3, proxies=proxy(2))
    return r.json()


def login_bonus_accept(user_account, sign_in_response):
    url = host + '/login_bonuses/accept'
    ad_id, unique_id, platform, country, currency, identifier, name, id_ = user_account
    MAC = generate_mac('POST', url, sign_in_response['secret'], sign_in_response['access_token'])

    headers3 = headers.copy()
    headers3['X-Platform'] = platform

    headers3['X-AssetVersion'] = str(int(time.time()))
    headers3['X-RequestVersion'] = '10'
    headers3['X-DatabaseVersion'] = str(int(time.time()))
    headers3['Authorization'] = "MAC " + MAC

    r = requests.post(url, data=None, headers=headers3, proxies=proxy(2))
    return r.json()


def apologies_accept(user_account, sign_in_response):
    url = host + '/apologies/accept'
    ad_id, unique_id, platform, country, currency, identifier, name, id_ = user_account
    MAC = generate_mac('PUT', url, sign_in_response['secret'], sign_in_response['access_token'])

    headers3 = headers.copy()
    headers3['X-Platform'] = platform

    headers3['X-AssetVersion'] = str(int(time.time()))
    headers3['X-RequestVersion'] = '10'
    headers3['X-DatabaseVersion'] = str(int(time.time()))
    headers3['Authorization'] = "MAC " + MAC

    r = requests.put(url, data=None, headers=headers3, proxies=proxy(2))
    return r.json()


def dragonball_sets(user_account, sign_in_response):
    url = host + '/dragonball_sets'
    ad_id, unique_id, platform, country, currency, identifier, name, id_ = user_account
    MAC = generate_mac('GET', url, sign_in_response['secret'], sign_in_response['access_token'])

    headers3 = headers.copy()
    headers3['X-Platform'] = platform

    headers3['X-AssetVersion'] = str(int(time.time()))
    headers3['X-RequestVersion'] = '11'
    headers3['X-DatabaseVersion'] = str(int(time.time()))
    headers3['Authorization'] = "MAC " + MAC

    r = requests.get(url, headers=headers3)
    return r.json()


def banners(user_account, sign_in_response):
    url = host + '/banners'
    ad_id, unique_id, platform, country, currency, identifier, name, id_ = user_account
    MAC = generate_mac('GET', url, sign_in_response['secret'], sign_in_response['access_token'])

    headers3 = headers.copy()
    headers3['X-Platform'] = platform

    headers3['X-AssetVersion'] = str(int(time.time()))
    headers3['X-RequestVersion'] = '11'
    headers3['X-DatabaseVersion'] = str(int(time.time()))
    headers3['Authorization'] = "MAC " + MAC

    r = requests.get(url, headers=headers3)
    return r.json()


def budokai(user_account, sign_in_response):
    url = host + '/budokai'
    ad_id, unique_id, platform, country, currency, identifier, name, id_ = user_account
    MAC = generate_mac('GET', url, sign_in_response['secret'], sign_in_response['access_token'])

    headers3 = headers.copy()
    headers3['X-Platform'] = platform

    headers3['X-AssetVersion'] = str(int(time.time()))
    headers3['X-RequestVersion'] = '11'
    headers3['X-DatabaseVersion'] = str(int(time.time()))
    headers3['Authorization'] = "MAC " + MAC

    r = requests.get(url, headers=headers3)
    return r.json()


def sns_campaign(user_account, sign_in_response):
    url = host + '/sns_campaign'
    ad_id, unique_id, platform, country, currency, identifier, name, id_ = user_account
    MAC = generate_mac('GET', url, sign_in_response['secret'], sign_in_response['access_token'])

    headers3 = headers.copy()
    headers3['X-Platform'] = platform

    headers3['X-AssetVersion'] = str(int(time.time()))
    headers3['X-RequestVersion'] = '11'
    headers3['X-DatabaseVersion'] = str(int(time.time()))
    headers3['Authorization'] = "MAC " + MAC

    r = requests.get(url, headers=headers3)
    return r.json()


def reward_campaigns(user_account, sign_in_response):
    url = host + '/shops/reward_campaigns/'
    ad_id, unique_id, platform, country, currency, identifier, name, id_ = user_account
    MAC = generate_mac('GET', url, sign_in_response['secret'], sign_in_response['access_token'])

    headers3 = headers.copy()
    headers3['X-Platform'] = platform

    headers3['X-AssetVersion'] = str(int(time.time()))
    headers3['X-RequestVersion'] = '11'
    headers3['X-DatabaseVersion'] = str(int(time.time()))
    headers3['Authorization'] = "MAC " + MAC

    r = requests.get(url, headers=headers3)
    return r.json()


def bonus_schedules(user_account, sign_in_response):
    url = host + '/bonus_schedules'
    ad_id, unique_id, platform, country, currency, identifier, name, id_ = user_account
    MAC = generate_mac('GET', url, sign_in_response['secret'], sign_in_response['access_token'])

    headers3 = headers.copy()
    headers3['X-Platform'] = platform

    headers3['X-AssetVersion'] = str(int(time.time()))
    headers3['X-RequestVersion'] = '11'
    headers3['X-DatabaseVersion'] = str(int(time.time()))
    headers3['Authorization'] = "MAC " + MAC

    r = requests.get(url, headers=headers3)
    return r.json()


def friendships(user_account, sign_in_response):
    url = host + '/friendships'
    ad_id, unique_id, platform, country, currency, identifier, name, id_ = user_account
    MAC = generate_mac('GET', url, sign_in_response['secret'], sign_in_response['access_token'])

    headers3 = headers.copy()
    headers3['X-Platform'] = platform

    headers3['X-AssetVersion'] = str(int(time.time()))
    headers3['X-RequestVersion'] = '11'
    headers3['X-DatabaseVersion'] = str(int(time.time()))
    headers3['Authorization'] = "MAC " + MAC

    r = requests.get(url, headers=headers3)
    return r.json()


def rtbattles(user_account, sign_in_response):
    url = host + '/rtbattles'
    ad_id, unique_id, platform, country, currency, identifier, name, id_ = user_account
    MAC = generate_mac('GET', url, sign_in_response['secret'], sign_in_response['access_token'])

    headers3 = headers.copy()
    headers3['X-Platform'] = platform

    headers3['X-AssetVersion'] = str(int(time.time()))
    headers3['X-RequestVersion'] = '14'
    headers3['X-DatabaseVersion'] = str(int(time.time()))
    headers3['Authorization'] = "MAC " + MAC

    r = requests.get(url, headers=headers3)
    return r.json()


def gifts(user_account, sign_in_response):
    url = host + '/gifts'
    ad_id, unique_id, platform, country, currency, identifier, name, id_ = user_account
    MAC = generate_mac('GET', url, sign_in_response['secret'], sign_in_response['access_token'])

    headers3 = headers.copy()
    headers3['X-Platform'] = platform

    headers3['X-AssetVersion'] = str(int(time.time()))
    headers3['X-RequestVersion'] = '11'
    headers3['X-DatabaseVersion'] = str(int(time.time()))
    headers3['Authorization'] = "MAC " + MAC

    r = requests.get(url, headers=headers3, proxies=proxy(2))
    return r.json()


def gifts_accept(user_account, sign_in_response, gift_list):
    url = host + '/gifts/accept'
    ad_id, unique_id, platform, country, currency, identifier, name, id_ = user_account
    MAC = generate_mac('POST', url, sign_in_response['secret'], sign_in_response['access_token'])

    headers3 = headers.copy()
    headers3['X-Platform'] = platform

    headers3['X-AssetVersion'] = str(int(time.time()))
    headers3['X-RequestVersion'] = '15'
    headers3['X-DatabaseVersion'] = str(int(time.time()))
    headers3['Authorization'] = "MAC " + MAC

    r = requests.post(url, json={'gift_ids': gift_list}, headers=headers3, proxies=proxy(2))
    return r.json()


def gashas(user_account, sign_in_response):
    url = host + '/gashas'
    ad_id, unique_id, platform, country, currency, identifier, name, id_ = user_account
    MAC = generate_mac('GET', url, sign_in_response['secret'], sign_in_response['access_token'])

    headers3 = headers.copy()
    headers3['X-Platform'] = platform

    headers3['X-AssetVersion'] = str(int(time.time()))
    headers3['X-RequestVersion'] = '16'
    headers3['X-DatabaseVersion'] = str(int(time.time()))
    headers3['Authorization'] = "MAC " + MAC

    r = requests.get(url, headers=headers3, proxies=proxy(2))
    return r.json()


def gasha_draw(user_account, sign_in_response, gasha_id, offset=0):
    url = host + '/gashas/{}/courses/2/draw'.format(gasha_id)
    ad_id, unique_id, platform, country, currency, identifier, name, id_ = user_account
    MAC = generate_mac('POST', url, sign_in_response['secret'], sign_in_response['access_token'])

    headers3 = headers.copy()
    headers3['X-Platform'] = platform

    headers3['X-AssetVersion'] = str(int(time.time()))
    headers3['X-RequestVersion'] = str(17 + offset)
    headers3['X-DatabaseVersion'] = str(int(time.time()))
    headers3['Authorization'] = "MAC " + MAC

    # ~ pprint(headers3)
    # ~ pprint(url)
    r = requests.post(url, json=None, headers=headers3, proxies=proxy(2))
    return r.json()


def gasha_draw1(user_account, sign_in_response, gasha_id, offset=0):
    url = host + '/gashas/{}/courses/1/draw'.format(gasha_id)
    ad_id, unique_id, platform, country, currency, identifier, name, id_ = user_account
    MAC = generate_mac('POST', url, sign_in_response['secret'], sign_in_response['access_token'])

    headers3 = headers.copy()
    headers3['X-Platform'] = platform
    headers3['X-AssetVersion'] = str(int(time.time()))
    headers3['X-RequestVersion'] = str(17 + offset)
    headers3['X-DatabaseVersion'] = str(int(time.time()))
    headers3['Authorization'] = "MAC " + MAC

    # ~ pprint(headers3)
    # ~ pprint(url)
    r = requests.post(url, json=None, headers=headers3, proxies=proxy(2))
    return r.json()


def gashas2(user_account, sign_in_response):
    url = host + '/gashas'
    ad_id, unique_id, platform, country, currency, identifier, name, id_ = user_account
    MAC = generate_mac('GET', url, sign_in_response['secret'], sign_in_response['access_token'])

    headers3 = headers.copy()
    headers3['X-Platform'] = platform

    headers3['X-AssetVersion'] = str(int(time.time()))
    headers3['X-RequestVersion'] = '18'
    headers3['X-DatabaseVersion'] = str(int(time.time()))
    headers3['Authorization'] = "MAC " + MAC

    r = requests.get(url, headers=headers3, proxies=proxy(2))
    return r.json()


def start_dash_gasha_status(user_account, sign_in_response):
    url = host + '/start_dash_gasha_status'
    ad_id, unique_id, platform, country, currency, identifier, name, id_ = user_account
    MAC = generate_mac('GET', url, sign_in_response['secret'], sign_in_response['access_token'])

    headers3 = headers.copy()
    headers3['X-Platform'] = platform

    headers3['X-AssetVersion'] = str(int(time.time()))
    headers3['X-RequestVersion'] = '18'
    headers3['X-DatabaseVersion'] = str(int(time.time()))
    headers3['Authorization'] = "MAC " + MAC

    r = requests.get(url, headers=headers3, proxies=proxy(2))
    return r.json()


Error = False
debug = False

try:
    if sys.argv[1] == "0":
        debug = True
    elif sys.argv[1] == "1":
        Error = True
except:
    pass

headers = {}
headers['Accept'] = '*/*'
headers['Content-Type'] = 'application/json'
headers['User-Agent'] = None

if Error or debug:
    if not os.path.isdir("errors"):
        os.makedirs("errors")

lm = location_menu()
if lm == 1:
    country, currency = "US", "USD"
    client_version = '3.11.0'
    host = 'https://ishin-global.aktsk.com'
    headers['X-Language'] = 'en'
    userdatafile = "dokan.db"
elif lm == 2:
    country, currency = None, None
    client_version = '3.13.0'
    host = 'https://ishin-production.aktsk.jp'
    userdatafile = "dokan.jp.db"

if not os.path.isfile(userdatafile):
    conn = sqlite3.connect(userdatafile)
    c = conn.cursor()
    c.execute(
        'CREATE TABLE "userdata" ( `idx` INTEGER PRIMARY KEY AUTOINCREMENT, `ad_id` TEXT, `unique_id` TEXT, `platform` TEXT, `country` TEXT, `currency` TEXT, `identifier` TEXT, `name` TEXT, `id` TEXT, `cards` TEXT, `stone` INTEGER )')
    c.execute('CREATE INDEX `idxcard` ON `userdata` ( `cards` ASC )')
    c.execute('CREATE INDEX `idxplatform` ON `userdata` ( `platform` ASC )')
    c.execute('CREATE unique INDEX `idxuserdata` ON `userdata` ( `ad_id` ASC )')
    c.execute('CREATE TABLE `dbversion` ( `version` INTEGER )')
    c.execute('insert into `dbversion` values(?)', (DBVERSION,))
    conn.commit()
    conn.close()


def upgrade_db(c, ver):
    if ver < 1:
        try:
            c.execute('CREATE TABLE `dbversion` ( `version` INTEGER )')
            c.execute('drop index idxuserdata')
            c.execute('CREATE unique INDEX `idxuserdata` ON `userdata` ( `ad_id` ASC )')
        except sqlite3.OperationalError:
            pass
    if ver < 3:
        try:
            try:
                c.execute("drop table userdata_backup")
            except:
                pass

            c.execute("create table userdata_backup as select * from userdata")
            c.execute("delete from userdata")
            c.execute(
                "insert into userdata SELECT idx, ad_id, unique_id, platform, country, currency, identifier, name, id, group_concat(cards) as cards FROM userdata_backup GROUP BY id")
            c.execute('CREATE unique INDEX `iduserdata` ON `userdata` ( `id` ASC )')
        except sqlite3.OperationalError:
            pass

    if ver < 4:
        try:
            c.execute("ALTER TABLE userdata ADD COLUMN stone integer")
        except sqlite3.OperationalError:
            pass

try:
    conn = sqlite3.connect(userdatafile)
    c = conn.cursor()
    c.execute("select * from dbversion")
    res = c.fetchone()
    ver = res[0]
    print("DB Version is {}".format(ver))
    if ver < DBVERSION:
        print("DB needs to be upgraded")
        upgrade_db(c, ver)
        c.execute('delete from `dbversion`')
        c.execute('insert into `dbversion` values(?)', (DBVERSION,))
        print("DB upgrade finished")
except:
    upgrade_db(c, 0)
    c.execute('delete from `dbversion`')
    c.execute('insert into `dbversion` values(?)', (DBVERSION,))

conn.commit()
conn.close()

headers['X-ClientVersion'] = client_version

while True:
    om = operation_menu()
    if om == 0:
        sys.exit(0)
    elif om == 1:
        threads = input("Enter number of parallel runs (Do not overcharge :) ) > ")
        platform = platform_menu()
        account_count = input("How many account do you want to create? ")

        q = Queue()
        qo = Queue()

        tt = threading.Thread(target=save_user_data, args=(q, True, qo,))
        tt.start()

        ts = []
        for i in range(0, int(threads)):
            acct_cnt = int(
                int(account_count) / int(threads) if i != int(threads) - 1 else int(account_count) / int(threads) + int(
                    account_count) % int(threads))
            t = threading.Thread(target=create_new_account, args=(i, q, platform, acct_cnt,))
            ts.append(t)
            t.start()

        while True:
            b = True
            for t in ts:
                if t.is_alive():
                    b = False
                    time.sleep(1)
                    break
            if b:
                break

        q.put(None)

        created_accounts = []
        while True:
            acct = qo.get()
            if acct == None:
                break
            created_accounts.append(acct)

        # ~ created_accounts = save_user_data(q)
        while True:
            answer = input("Would you like to sign in using new accounts and collect gifts? [Y/N] ")
            if answer.upper() in ['Y', 'N']:
                break

        ts = []
        if answer.upper() == 'Y':
            for i in range(0, int(threads)):
                m = i * int(int(account_count) / int(threads))
                mx = (i + 1) * int(int(account_count) / int(threads)) if i != int(threads) - 1 else (i + 1) * int(
                    int(account_count) / int(threads)) + int(account_count) % int(threads)
                accts = created_accounts[m:mx]
                t = threading.Thread(target=collect_gifts, args=(i, accts,))
                ts.append(t)
                t.start()

        while True:
            b = True
            for t in ts:
                if t.is_alive():
                    b = False
                    time.sleep(1)
                    break
            if b:
                break

    elif om == 2:
        sign_in_and_collect()
    elif om == 3:
        transfer_account_to_real_device()
    elif om == 4:
        transfer_account_from_real_device()
    elif om == 5:
        threads = input("Enter number of parallel runs (Do not overcharge :) ) > ")
        platform = platform_menu()
        account_count = input("How many account do you want to create? ")
        gasha_ids = input("Enter pack ids (e.g. 1234,1235,1236) > ")
        card_ids = input("Enter card ids (e.g. 4214,4324,5435) > ")
        mode = int(input("1- Ordinary\t2- Wanted >"))
        # ~ loop = input("How many times will the pack be opened > ")
        single = input("1- Single\t 2- Multi > ")
        store_limit = int(input("Enter lower limit of found cards to store account > "))

        loops = {}
        for gasha_id in gasha_ids.split(','):
            loops[gasha_id] = int(input("How many times will pack {} be opened? (-1 for MAX) > ".format(gasha_id)))

        q = Queue()
        qo = Queue()

        tt = threading.Thread(target=save_user_data, args=(q, False, qo,))
        tt.start()

        ts = []
        for i in range(0, int(threads)):
            acct_cnt = int(
                int(account_count) / int(threads) if i != int(threads) - 1 else int(account_count) / int(threads) + int(
                    account_count) % int(threads))
            t = threading.Thread(target=create_new_account, args=(i, q, platform, acct_cnt,))
            ts.append(t)
            t.start()

        while True:
            b = True
            for t in ts:
                if t.is_alive():
                    b = False
                    time.sleep(1)
                    break
            if b:
                break

        q.put(None)

        created_accounts = []
        while True:
            acct = qo.get()
            if acct == None:
                break
            created_accounts.append(acct)
        # ~ created_accounts = save_user_data(q, store=False)

        sign_in_and_open_pack(created_accounts, platform=platform, loops=loops, threads=threads, gasha_ids=gasha_ids,
                              card_ids=card_ids, mode=mode, single=single, store_limit=store_limit)
        # ~ ts = []
        # ~ for i in range(0, int(threads)):
        # ~ m = i*int(int(account_count)/int(threads))
        # ~ mx = (i+1)*int(int(account_count)/int(threads)) if i != int(threads) - 1 else (i+1)*int(int(account_count)/int(threads)) + int(account_count)%int(threads)
        # ~ accts = created_accounts[m:mx]
        # ~ t = threading.Thread(target=collect_gifts, args=(i, accts, True, gasha_ids.split(','), card_ids, loops, single, q, store_limit, mode,))
        # ~ ts.append(t)
        # ~ t.start()

        # ~ while True:
        # ~ b = True
        # ~ for t in ts:
        # ~ if t.is_alive():
        # ~ b = False
        # ~ time.sleep(1)
        # ~ break
        # ~ if b:
        # ~ break

        # ~ q.put(None)
        # ~ save_user_data3(q)

    elif om == 6:
        delete = input("1- Keep All Accounts\n2- Delete accounts if card is not found")
        if delete == "1":
            delete = False
        else:
            delete = True
        sign_in_and_open_pack(delete=delete)
    elif om == 7:
        import_csv()
    elif om == 8:
        export_csv()
    elif om == 9:
        print_user_database()
    elif om == 10:
        print_user_database(carddb=True)
    elif om == 11:
        platform = platform_menu(a=True)
        userindexmap, userlist = print_user_database(p=False, platform=platform, carddb='all')
        threads = input("Enter number of parallel runs (Do not overcharge :) ) > ")

        ts = []
        q = Queue()
        for i in range(0, int(threads)):
            m = i * int(int(len(userlist)) / int(threads))
            mx = (i + 1) * int(int(len(userlist)) / int(threads)) if i != int(threads) - 1 else (i + 1) * int(
                int(len(userlist)) / int(threads)) + int(len(userlist)) % int(threads)
            usrs = userlist[m:mx]
            t = threading.Thread(target=print_stones, args=(usrs, q,))
            ts.append(t)
            t.start()

        ccc = 0
        while True:
            m = q.get()
            if m == None:
                ccc += 1
                if ccc == int(threads):
                    break
            else:
                print(m)

    elif om == 12:
        keyword = input("Enter keyword for card name (e.g. LR) >")
        cardids = cardid(keyword)
        users = load_user_data_by_cardids(cardids)
        with open("output.txt","w") as out:
            for idx, ad_id, unique_id, platform, country, currency, identifier, name, _id, card_id, stones in users:
                c = []
                for card in card_id.split(','):
                    if card != "None":
                        c.append("{}({})".format(card, cardname(card)))
                out.write("id:{}\ncards:{}\n\n".format(_id, ', '.join(c)))

        print("Check output.txt")

    elif om == 20:
        startat = input("Enter start time (e.g. 03:30) > ")

        date = datetime.now().replace(hour=datetime.strptime(startat, '%H:%M').hour, minute=datetime.strptime(startat, '%H:%M').minute)
        if date < datetime.now():
            nextrun = date + timedelta(days=1)
        else:
            nextrun = date


        print("Select an operation to schedule:")
        print("1- Create new accounts")
        print("2- Signin and collect gifts")
        print("3- Create accounts and open packs")
        print("4- Signin and open packs")
        selection = input("Selection > ")
        if selection == "1":
            threads = input("Enter number of parallel runs (Do not overcharge :) ) > ")
            platform = platform_menu()
            account_count = input("How many account do you want to create? ")

            while True:
                if datetime.now() >= nextrun:
                    nextrun = datetime.now() + timedelta(days=1)

                    q = Queue()
                    qo = Queue()

                    tt = threading.Thread(target=save_user_data, args=(q, True, qo,))
                    tt.start()

                    ts = []
                    for i in range(0, int(threads)):
                        acct_cnt = int(
                            int(account_count) / int(threads) if i != int(threads) - 1 else int(account_count) / int(
                                threads) + int(account_count) % int(threads))
                        t = threading.Thread(target=create_new_account, args=(i, q, platform, acct_cnt,))
                        ts.append(t)
                        t.start()

                    while True:
                        b = True
                        for t in ts:
                            if t.is_alive():
                                b = False
                                time.sleep(1)
                                break
                        if b:
                            break
                    print("Next run is at {}".format(nextrun))

                time.sleep(60)

        if selection == "2":
            threads = input("Enter number of parallel runs (Do not overcharge :) ) > ")
            dbselection = input("Which used db do you want to use:\n\t1-General User DB\t2-Card Users DB\n\t\tSelect> ")

            if dbselection == "1":
                userindexmap, users = print_user_database(p=False)
            elif dbselection == "2":
                userindexmap, users = print_user_database(p=False, carddb=True)


            while True:
                if datetime.now() >= nextrun:
                    nextrun = datetime.now() + timedelta(days=1)
                    ts = []
                    for i in range(0, int(threads)):
                        m = i * int(len(users) / int(threads))
                        mx = (i + 1) * int(len(users) / int(threads)) if i != int(threads) - 1 else (i + 1) * int(
                            len(users) / int(threads)) + len(users) % int(threads)
                        accts = users[m:mx]
                        t = threading.Thread(target=collect_gifts, args=(i, accts,))
                        ts.append(t)
                        t.start()

                    while True:
                        b = True
                        for t in ts:
                            if t.is_alive():
                                b = False
                                time.sleep(1)
                                break
                        if b:
                            break
                    print("Next run is at {}".format(nextrun))
                time.sleep(60)
        if selection == "3":
            threads = input("Enter number of parallel runs (Do not overcharge :) ) > ")
            platform = platform_menu()
            account_count = input("How many account do you want to create? ")
            gasha_ids = input("Enter pack ids (e.g. 1234,1235,1236) > ")
            card_ids = input("Enter card ids (e.g. 4214,4324,5435) > ")
            mode = int(input("1- Ordinary\t2- Wanted >"))
            # ~ loop = input("How many times will the pack be opened > ")
            single = input("1- Single\t 2- Multi > ")
            store_limit = int(input("Enter lower limit of found cards to store account > "))

            loops = {}
            for gasha_id in gasha_ids.split(','):
                loops[gasha_id] = int(input("How many times will pack {} be opened? (-1 for MAX) > ".format(gasha_id)))


            while True:
                if datetime.now() >= nextrun:
                    nextrun = datetime.now() + timedelta(days=1)

                    q = Queue()
                    qo = Queue()

                    tt = threading.Thread(target=save_user_data, args=(q, False, qo,))
                    tt.start()

                    ts = []
                    for i in range(0, int(threads)):
                        acct_cnt = int(
                            int(account_count) / int(threads) if i != int(threads) - 1 else int(account_count) / int(
                                threads) + int(account_count) % int(threads))
                        t = threading.Thread(target=create_new_account, args=(i, q, platform, acct_cnt,))
                        ts.append(t)
                        t.start()

                    while True:
                        b = True
                        for t in ts:
                            if t.is_alive():
                                b = False
                                time.sleep(1)
                                break
                        if b:
                            break

                    q.put(None)

                    created_accounts = []
                    while True:
                        acct = qo.get()
                        if acct == None:
                            break
                        created_accounts.append(acct)
                    # ~ created_accounts = save_user_data(q, store=False)

                    sign_in_and_open_pack(created_accounts, platform=platform, loops=loops, threads=threads,
                                          gasha_ids=gasha_ids, card_ids=card_ids, mode=mode, single=single,
                                          store_limit=store_limit)

                    print("Next run is at {}".format(nextrun))
                time.sleep(60)
        if selection == "4":
            threads = input("Enter number of parallel runs (Do not overcharge :) ) > ")
            platform = platform_menu()
            gasha_ids = input("Enter pack ids (e.g. 1234,1235,1236) > ")
            card_ids = input("Enter card ids (e.g. 4214,4324,5435) > ")
            mode = int(input("1- Ordinary\t2- Wanted >"))
            # ~ loop = input("How many times will the pack be opened > ")
            single = input("1- Single\t 2- Multi > ")
            store_limit = int(input("Enter lower limit of found cards to store account > "))

            dbselection = input("Which used db do you want to use:\n\t1-General User DB\t2-Card Users DB\n\t\tSelect> ")

            if dbselection == "1":
                userindexmap, accounts = print_user_database(p=False, platform=platform)
            elif dbselection == "2":
                userindexmap, accounts = print_user_database(p=False, platform=platform, carddb=True)

            loops = {}
            for gasha_id in gasha_ids.split(','):
                loops[gasha_id] = int(input("How many times will pack {} be opened? (-1 for MAX) > ".format(gasha_id)))

            delete = input("1- Keep All Accounts\n2- Delete accounts if card is not found")
            if delete == "1":
                delete = False
            else:
                delete = True

            while True:
                if datetime.now() >= nextrun:
                    if dbselection == "1":
                        userindexmap, accounts = print_user_database(p=False, platform=platform)
                    elif dbselection == "2":
                        userindexmap, accounts = print_user_database(p=False, platform=platform, carddb=True)

                    nextrun = datetime.now() + timedelta(days=1)
                    sign_in_and_open_pack(accounts, platform=platform, loops=loops, threads=threads,
                                          gasha_ids=gasha_ids, card_ids=card_ids, mode=mode, single=single,
                                          store_limit=store_limit, delete=delete)
                    print("Next run is at {}".format(nextrun))
                time.sleep(60)

    elif om == 61:
        convert_accounts('android', 'ios')
    elif om == 62:
        convert_accounts('ios', 'android')
    elif om == 71:
        import_from_63()
    elif om == 72:
        merge_data_from_another_db()
    elif om == 123654789:
        delete_user_from_database()
    elif om == 147852369:
        reset_user_data()
