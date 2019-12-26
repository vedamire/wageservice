from eosfactory.eosf import *
import time
import unittest
import sys, io
import json
import string
stdout = sys.stdout

reset()
create_master_account("master")

create_account("token_host", master, account_name="eosio.token")
create_account("wageservice", master, account_name="wageservice")

token = Contract(token_host, "/home/ally/contracts/eosio.contracts/contracts/eosio.token")
wage = Contract(wageservice, "/home/ally/contracts/wageservice")

wageservice.set_account_permission(Permission.ACTIVE, add_code=True)
token_host.set_account_permission(Permission.ACTIVE, add_code=True)
create_account("charlie", master)
create_account("bob", master)
create_account("zoro", master)
token.deploy()
wage.deploy()

token_host.push_action(
    "create",
        {
        "issuer": charlie,
        "maximum_supply": "1000000000.0000 EOS",
        "can_freeze": "0",
        "can_recall": "0",
        "can_whitelist": "0"
    }, [charlie, token_host])

token_host.push_action(
    "issue",
    {
        "to": charlie, "quantity": "100.0000 EOS", "memo": ""
    },
    charlie)

token_host.push_action(
    "transfer",
    {
        "from": charlie, "to": bob,
        "quantity": "50.0000 EOS", "memo":""
    },
    charlie)

def now():
    return int(time.time())

def lockConsole():
    sys.stdout = io.StringIO()
def getVal():
    val = sys.stdout.getvalue()
    sys.stdout = stdout
    return val
def correct(val):
    line = " ".join(val.split())
    printable = set(string.printable)
    line = ''.join(filter(lambda x: x in printable, line))
    in1 = line.index('{')
    in2 = line.rindex('}') + 1
    line = line[in1:-(len(line) - in2)]
    return json.loads(line)

def captureConsole(func):
    lockConsole()
    func(None)
    return correct(getVal())

class TestStringMethods(unittest.TestCase):
    def test_single(self):
        token_host.push_action(
            "transfer",
            {
                "from": charlie, "to": wageservice,
                "quantity": "5.0000 EOS", "memo":"placewage"
            },
            charlie)
        # js = captureConsole(lambda _:wageservice.table("wagev1", wageservice))["rows"][0];
        # print(js)
        # self.assertEqual(js["wage_frozen"], "5.0000 EOS")
        wageservice.push_action(
            "placewage",
            {
                "employer": charlie,
                "id": 0,
                "worker": bob,
                "days": 3
            },
            permission=(charlie, Permission.ACTIVE))
        # js = captureConsole(lambda _:wageservice.table("wagev1", wageservice))["rows"][0];
        # print(js);
        # self.assertEqual(js["wage_per_day"],  "2.0000 EOS")
        wageservice.push_action(
            "acceptwage",
            {
                "worker": bob,
                "id": 0,
                "isaccepted": True
            },
            permission=(bob, Permission.ACTIVE));
        wageservice.push_action(
            "addworkday",
            {
                "employer": charlie,
                "id": 0
            },
            permission=(charlie, Permission.ACTIVE));
        wageservice.push_action(
            "addworkday",
            {
                "employer": charlie,
                "id": 0
            },
            permission=(charlie, Permission.OWNER));
        time.sleep(1);
        wageservice.push_action(
            "addworkday",
            {
                "employer": charlie,
                "id": 0
            },
            permission=(charlie, Permission.ACTIVE));
        js = captureConsole(lambda _:wageservice.table("wagev1", wageservice))["rows"][0];
        print(js);
        js = captureConsole(lambda _:token_host.table("accounts", charlie));
        print(js);
        js = captureConsole(lambda _:token_host.table("accounts", bob));
        print(js);
        wageservice.push_action(
            "closewage",
            {
                "employer": charlie,
                "id": 0
            },
            permission=(charlie, Permission.ACTIVE));
        js = captureConsole(lambda _:token_host.table("accounts", wageservice));
        print(js);
        js = captureConsole(lambda _:token_host.table("accounts", charlie));
        print(js);
        js = captureConsole(lambda _:token_host.table("accounts", bob));
        print(js);
if __name__ == '__main__':
    unittest.main()

stop()
