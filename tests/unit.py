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
create_account("wageservice1", master, account_name="wageservice1")


token = Contract(token_host, "/home/ally/contracts/eosio.contracts/contracts/eosio.token")
wage = Contract(wageservice, "/home/ally/contracts/wageservice")
wage1 = Contract(wageservice1, "/home/ally/contracts/wageservice")

wageservice.set_account_permission(Permission.ACTIVE, add_code=True)
wageservice1.set_account_permission(Permission.ACTIVE, add_code=True)
token_host.set_account_permission(Permission.ACTIVE, add_code=True)
create_account("charlie", master)
create_account("bob", master)
create_account("zoro", master)
token.deploy()
wage.deploy()
wage1.deploy()
token_host.push_action(
    "create",
        {
        "issuer": zoro,
        "maximum_supply": "1000000000.0000 EOS",
        "can_freeze": "0",
        "can_recall": "0",
        "can_whitelist": "0"
    }, [zoro, token_host])

token_host.push_action(
    "issue",
    {
        "to": zoro, "quantity": "100000.0000 EOS", "memo": ""
    },
    permission=(zoro, Permission.ACTIVE))

token_host.push_action(
    "transfer",
    {
        "from": zoro, "to": charlie,
        "quantity": "50.0000 EOS", "memo":""
    },
    zoro)
token_host.push_action(
    "transfer",
    {
        "from": zoro, "to": bob,
        "quantity": "50.0000 EOS", "memo":""
    },
    zoro)
FEE = 0.03

def getBase(body):
    str_charl = str(body);
    dots = str_charl[str_charl.find(".") + 1:];
    ch_base = " EOS"
    for i in range(4 - len(dots)):
        ch_base = "0" + ch_base;
    return ch_base;
def afterFee(quantity):
    afterfee = float(quantity.replace(" EOS", "")) - FEE;
    return str(afterfee) + getBase(afterfee)
def toFloat(quantity):
    return float(quantity.replace(" EOS", ""));
def toStr(quantity):
    return str(quantity) + getBase(quantity);
def Balance(name):
    return token_host.table("accounts", name).json["rows"][0]["balance"]
def Rows(contract):
    return contract.table("wagev1", contract).json["rows"];
def now():
    return int(time.time())

class TestStringMethods(unittest.TestCase):
    def setUp(self):
        time.sleep(1);

        # print(chb)
        balance = Balance(charlie)
        # self.assertEqual(table.json["rows"][0]["board"][0], 0)
        # amount = table.json["rows"][0].balance; table.json["rows"][0]["balance"],
        token_host.push_action(
            "transfer",
            {
                "from": charlie, "to": zoro,
                "quantity": balance, "memo":""
            },
            charlie)
        balance = Balance(bob);
        token_host.push_action(
            "transfer",
            {
                "from": zoro, "to": charlie,
                "quantity": "50.0000 EOS", "memo":""
            },
            zoro)
        token_host.push_action(
            "transfer",
            {
                "from": bob, "to": zoro,
                "quantity": balance, "memo":""
            },
            bob)
        token_host.push_action(
            "transfer",
            {
                "from": zoro, "to": bob,
                "quantity": "50.0000 EOS", "memo":""
            },
            zoro)

    def test_single(self):
        time.sleep(1);

    def test_multiple(self):
        # time.sleep(10)
        quantity = "5.0000 EOS";
        times = 5;
        for i in range(times):
            time.sleep(0.5);
            token_host.push_action(
                "transfer",
                {
                    "from": charlie, "to": wageservice1,
                    "quantity": quantity, "memo":"placewage"
                },
                charlie);
        # arr = captureConsole(lambda _: wageservice1.table("wagev1", wageservice1))["rows"];
        arr = Rows(wageservice1);
        for i in range(times):
            self.assertEqual(arr[i]["id"], i);
            self.assertEqual(arr[i]["is_specified"], False);
        for i in range(times):
            wageservice1.push_action(
                "placewage",
                {
                    "employer": charlie,
                    "id": i,
                    "worker": bob,
                    "days": 4
                },
                permission=(charlie, Permission.ACTIVE))
        arr = Rows(wageservice1);
        for i in range(times):
            self.assertEqual(arr[i]["is_accepted"], False);
            self.assertEqual(arr[i]["is_specified"], True);
            # self.assertEqual(arr[i]["worker"], bob);
        for i in range(times):
            wageservice1.push_action(
                "acceptwage",
                {
                    "worker": bob,
                    "id": i,
                    "isaccepted": True
                },
                permission=(bob, Permission.ACTIVE))
        arr = Rows(wageservice1)
        for i in range(times):
            # self.assertEqual(arr[i]["id"], i);
            self.assertEqual(arr[i]["is_accepted"], True);
        for i in range(times):
            for r in range(4):
                time.sleep(0.5)
                wageservice1.push_action(
                    "addworkday",
                    {
                        "employer": charlie,
                        "id": i
                    },
                    permission=(charlie, Permission.ACTIVE));
        arr = Rows(wageservice1);
        for i in range(times):
            # self.assertEqual(arr[i]["id"], i);
            self.assertEqual(arr[i]["worked_days"], 4);
        for i in range(times):
            wageservice1.push_action(
                "closewage",
                {
                    "employer": charlie,
                    "id": i
                },
                permission=(charlie, Permission.ACTIVE))
        res = toStr(toFloat("50.0000 EOS") + (toFloat(afterFee(quantity)) * times));
        self.assertEqual(Balance(bob), res)

    def test_partial(self):
        quantity = "5.0000 EOS";
        times = 8;
        for i in range(times):
            time.sleep(0.5);
            token_host.push_action(
                "transfer",
                {
                    "from": charlie, "to": wageservice1,
                    "quantity": quantity, "memo":"placewage"
                },
                charlie);
        # arr = captureConsole(lambda _: wageservice1.table("wagev1", wageservice1))["rows"];
        arr = Rows(wageservice1);
        for i in range(times):
            self.assertEqual(arr[i]["id"], i);
            self.assertEqual(arr[i]["is_specified"], False);
        for i in range(times):
            wageservice1.push_action(
                "placewage",
                {
                    "employer": charlie,
                    "id": i,
                    "worker": bob,
                    "days": 4
                },
                permission=(charlie, Permission.ACTIVE))
        arr = Rows(wageservice1);
        for i in range(times):
            self.assertEqual(arr[i]["is_accepted"], False);
            self.assertEqual(arr[i]["is_specified"], True);
            # self.assertEqual(arr[i]["worker"], bob);
        for i in range(times):
            wageservice1.push_action(
                "acceptwage",
                {
                    "worker": bob,
                    "id": i,
                    "isaccepted": True
                },
                permission=(bob, Permission.ACTIVE))
        arr = Rows(wageservice1)
        for i in range(times):
            # self.assertEqual(arr[i]["id"], i);
            self.assertEqual(arr[i]["is_accepted"], True);
        for i in range(times):
            for r in range(2):
                time.sleep(0.5)
                wageservice1.push_action(
                    "addworkday",
                    {
                        "employer": charlie,
                        "id": i
                    },
                    permission=(charlie, Permission.ACTIVE));
        arr = Rows(wageservice1);
        for i in range(times):
            self.assertEqual(arr[i]["worked_days"], 2);
        for i in range(times):
            wageservice1.push_action(
                "closewage",
                {
                    "employer": charlie,
                    "id": i
                },
                permission=(charlie, Permission.ACTIVE))

        res = toFloat("50.0000 EOS") + (toFloat(afterFee(quantity)) * (times / 2))
        charlie_balance = toFloat("50.0000 EOS") - (toFloat(quantity) * (times / 2)) - (FEE * (times / 2));
        self.assertEqual(Balance(bob), toStr(res))
        self.assertEqual(Balance(charlie), toStr(charlie_balance))

    def test_cancel(self):
        quantity = "5.0000 EOS";
        times = 6;
        for i in range(times):
            time.sleep(0.5);
            token_host.push_action(
                "transfer",
                {
                    "from": charlie, "to": wageservice1,
                    "quantity": quantity, "memo":"placewage"
                },
                charlie);
        # arr = captureConsole(lambda _: wageservice1.table("wagev1", wageservice1))["rows"];
        arr = Rows(wageservice1);
        for i in range(times):
            self.assertEqual(arr[i]["id"], i);
            self.assertEqual(arr[i]["is_specified"], False);

        for i in range(times):
            wageservice1.push_action(
                "closewage",
                {
                    "employer": charlie,
                    "id": i
                },
                permission=(charlie, Permission.ACTIVE))
        res = toFloat("50.0000 EOS") - FEE * times;
        self.assertEqual(Balance(charlie), toStr(res))

if __name__ == '__main__':
    unittest.main()

stop()
