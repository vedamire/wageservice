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
create_account("wageservice2", master, account_name="wageservice2")


token = Contract(token_host, "/home/ally/contracts/eosio.contracts/contracts/eosio.token")
wage = Contract(wageservice, "/home/ally/contracts/wageservice")
wage1 = Contract(wageservice1, "/home/ally/contracts/wageservice")
wage2 = Contract(wageservice2, "/home/ally/contracts/wageservice")

wageservice.set_account_permission(Permission.ACTIVE, add_code=True)
wageservice1.set_account_permission(Permission.ACTIVE, add_code=True)
wageservice2.set_account_permission(Permission.ACTIVE, add_code=True)
token_host.set_account_permission(Permission.ACTIVE, add_code=True)
create_account("charlie", master)
create_account("bob", master)
create_account("zoro", master)
token.deploy()
wage.deploy()
wage1.deploy()
wage2.deploy()
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
                    "from": charlie, "to": wageservice,
                    "quantity": quantity, "memo":"placewage"
                },
                charlie);
        # arr = captureConsole(lambda _: wageservice1.table("wagev1", wageservice1))["rows"];
        arr = Rows(wageservice);
        for i in range(times):
            self.assertEqual(arr[i]["id"], i);
            self.assertEqual(arr[i]["is_specified"], False);

        for i in range(times):
            wageservice.push_action(
                "closewage",
                {
                    "employer": charlie,
                    "id": i
                },
                permission=(charlie, Permission.ACTIVE))
        res = toFloat("50.0000 EOS") - FEE * times;
        self.assertEqual(Balance(charlie), toStr(res))

    def test_ext_errors(self):
        token_host.push_action(
            "transfer",
            {
                "from": charlie, "to": wageservice2,
                "quantity": "7.0000 EOS", "memo":"placewage"
            },
            charlie);
        wageservice2.push_action(
            "placewage",
            {
                "employer": charlie,
                "id": 0,
                "worker": bob,
                "days": 4
            },
            permission=(charlie, Permission.ACTIVE));
        token_host.push_action(
            "transfer",
            {
                "from": charlie, "to": wageservice2,
                "quantity": "5.0000 EOS", "memo":"placewage"
            },
            charlie);
        token_host.push_action(
            "transfer",
            {
                "from": charlie, "to": wageservice2,
                "quantity": "8.0000 EOS", "memo":"placewage"
            },
            charlie);
        wageservice2.push_action(
            "placewage",
            {
                "employer": charlie,
                "id": 2,
                "worker": bob,
                "days": 4
            },
            permission=(charlie, Permission.ACTIVE));
        wageservice2.push_action(
            "acceptwage",
            {
                "worker": bob,
                "id": 2,
                "isaccepted": True
            },
            permission=(bob, Permission.ACTIVE))
        try:
            token_host.push_action(
                "transfer",
                {
                    "from": charlie, "to": wageservice2,
                    "quantity": "5.0000 EOS", "memo":""
                },
                charlie);
            self.assertEqual("Placing with wrong memo", "");
        except Error as err:
            self.assertTrue("Wrong memo. To transfer money here use ether 'placewage' or 'replenish' memo" in err.message)
            print("memo passed");
        try:
            token_host.push_action(
                "transfer",
                {
                    "from": charlie, "to": wageservice2,
                    "quantity": "0.5000 EOS", "memo":"placewage"
                },
                charlie);
            self.assertEqual("wage < 1. eos", "");
        except Error as err:
            self.assertTrue("Full wage must be at least 1.0300 EOS" in err.message)
            print("min passed");
        try:
            wageservice2.push_action(
                "placewage",
                {
                    "employer": charlie,
                    "id": 1,
                    "worker": bob,
                    "days": 4
                },
                permission=(bob, Permission.ACTIVE));
            self.assertEqual("place without auth", "");
        except Error as err:
            self.assertTrue("missing authority of charlie" in err.message)
            print("place auth passed");
        try:
            wageservice2.push_action(
                "placewage",
                {
                    "employer": charlie,
                    "id": 1,
                    "worker": "poro",
                    "days": 4
                },
                permission=(charlie, Permission.ACTIVE));
            self.assertEqual("place not worker", "");
        except Error as err:
            self.assertTrue("Worker's account doesn't exist" in err.message)
            print("place worker passed");
        try:
            wageservice2.push_action(
                "placewage",
                {
                    "employer": charlie,
                    "id": 1,
                    "worker": wageservice2,
                    "days": 4
                },
                permission=(charlie, Permission.ACTIVE));
            self.assertEqual("place contract worker", "");
        except Error as err:
            self.assertTrue("Can't set this account as worker" in err.message)
            print("place contract passed");
        try:
            wageservice2.push_action(
                "placewage",
                {
                    "employer": charlie,
                    "id": 1,
                    "worker": bob,
                    "days": 0
                },
                permission=(charlie, Permission.ACTIVE));
            self.assertEqual("place days bad", "");
        except Error as err:
            self.assertTrue("Wage must be minimum for 1 day and maximum for 90 days" in err.message)
            print("place days passed");
        try:
            wageservice2.push_action(
                "placewage",
                {
                    "employer": charlie,
                    "id": 1,
                    "worker": bob,
                    "days": 100
                },
                permission=(charlie, Permission.ACTIVE));
            self.assertEqual("place days bad", "");
        except Error as err:
            self.assertTrue("Wage must be minimum for 1 day and maximum for 90 days" in err.message)
            print("place days passed");
        try:
            wageservice2.push_action(
                "placewage",
                {
                    "employer": charlie,
                    "id": 106,
                    "worker": bob,
                    "days": 4
                },
                permission=(charlie, Permission.ACTIVE));
            self.assertEqual("place not id", "");
        except Error as err:
            self.assertTrue("This wage id doesn't exist" in err.message)
            print("place id passed");
        try:
            wageservice2.push_action(
                "placewage",
                {
                    "employer": bob,
                    "id": 1,
                    "worker": bob,
                    "days": 4
                },
                permission=(bob, Permission.ACTIVE));
            self.assertEqual("place not owner", "");
        except Error as err:
            self.assertTrue("This is not your wage" in err.message)
            print("place owner passed");
        try:
            wageservice2.push_action(
                "placewage",
                {
                    "employer": charlie,
                    "id": 0,
                    "worker": bob,
                    "days": 4
                },
                permission=(charlie, Permission.ACTIVE));
            self.assertEqual("place already specified", "");
        except Error as err:
            self.assertTrue("This wage is already specified" in err.message)
            print("place specified passed");
        try:
            wageservice2.push_action(
                "placewage",
                {
                    "employer": charlie,
                    "id": 1,
                    "worker": bob,
                    "days": 10
                },
                permission=(charlie, Permission.ACTIVE));
            self.assertEqual("place wage per day < min", "");
        except Error as err:
            self.assertTrue("Wage per day must be at least 1 eos" in err.message)
            print("place per day min passed");
        try:
            wageservice2.push_action(
                "closewage",
                {
                    "employer": charlie,
                    "id": 1
                },
                permission=(bob, Permission.ACTIVE));
            self.assertEqual("close without auth", "");
        except Error as err:
            self.assertTrue("missing authority of charlie" in err.message)
            print("close auth passed");
        try:
            wageservice2.push_action(
                "closewage",
                {
                    "employer": charlie,
                    "id": 100
                },
                permission=(charlie, Permission.ACTIVE));
            self.assertEqual("close with wrong id", "");
        except Error as err:
            self.assertTrue("This wage doesn't exist" in err.message)
            print("close id passed");
        try:
            wageservice2.push_action(
                "closewage",
                {
                    "employer": bob,
                    "id": 1
                },
                permission=(bob, Permission.ACTIVE));
            self.assertEqual("close not owner", "");
        except Error as err:
            self.assertTrue("This is not your wage" in err.message)
            print("close owner passed");
        try:
            wageservice2.push_action(
                "addworkday",
                {
                    "employer": charlie,
                    "id": 2
                },
                permission=(bob, Permission.ACTIVE));
            self.assertEqual("addworkday auth", "");
        except Error as err:
            self.assertTrue("missing authority of charlie" in err.message)
            print("addworkday auth passed");
        try:
            wageservice2.push_action(
                "addworkday",
                {
                    "employer": charlie,
                    "id": 102
                },
                permission=(charlie, Permission.ACTIVE));
            self.assertEqual("addworkday with wrong id", "");
        except Error as err:
            self.assertTrue("No wage contract found with this id" in err.message)
            print("addworkday wrong id passed");
        try:
            wageservice2.push_action(
                "addworkday",
                {
                    "employer": bob,
                    "id": 2
                },
                permission=(bob, Permission.ACTIVE));
            self.assertEqual("addworkday not owner", "");
        except Error as err:
            self.assertTrue("This is not your wage" in err.message)
            print("addworkday owner passed");
        try:
            wageservice2.push_action(
                "addworkday",
                {
                    "employer": charlie,
                    "id": 0
                },
                permission=(charlie, Permission.ACTIVE));
            self.assertEqual("addworkday not accepted", "");
        except Error as err:
            self.assertTrue("This wage contract isn't accepted" in err.message)
            print("addworkday accepted passed");
        try:
            wageservice2.push_action(
                "claimwage",
                {
                    "worker": bob,
                    "id": 2
                },
                permission=(charlie, Permission.ACTIVE));
            self.assertEqual("claimwage auth not", "");
        except Error as err:
            self.assertTrue("missing authority of bob" in err.message)
            print("claimwage auth passed");
        try:
            wageservice2.push_action(
                "claimwage",
                {
                    "worker": bob,
                    "id": 104
                },
                permission=(bob, Permission.ACTIVE));
            self.assertEqual("claimwage wrong id", "");
        except Error as err:
            self.assertTrue("There's no wage contract with such an id" in err.message)
            print("claimwage id passed");

        try:
            wageservice2.push_action(
                "claimwage",
                {
                    "worker": charlie,
                    "id": 2
                },
                permission=(charlie, Permission.ACTIVE));
            self.assertEqual("claimwage not worker", "");
        except Error as err:
            self.assertTrue("You are not the worker of this wage contract" in err.message)
            print("claimwage owner passed");
        try:
            wageservice2.push_action(
                "claimwage",
                {
                    "worker": bob,
                    "id": 0
                },
                permission=(bob, Permission.ACTIVE));
            self.assertEqual("claimwage not accepted", "");
        except Error as err:
            self.assertTrue("The wage contract isn't accepted" in err.message)
            print("claimwage accepted passed");

        try:
            wageservice2.push_action(
                "claimwage",
                {
                    "worker": bob,
                    "id": 2
                },
                permission=(bob, Permission.ACTIVE));
            self.assertEqual("claimwage not ended", "");
        except Error as err:
            self.assertTrue("The contract isn't ended" in err.message)
            print("claimwage ended passed");
        try:
            wageservice2.push_action(
                "acceptwage",
                {
                    "worker": charlie,
                    "id": 0,
                    "isaccepted": True
                },
                permission=(bob, Permission.ACTIVE));
            self.assertEqual("acceptwage auth", "");
        except Error as err:
            self.assertTrue("missing authority of charlie" in err.message)
            print("acceptwage auth passed");
        try:
            wageservice2.push_action(
                "acceptwage",
                {
                    "worker": bob,
                    "id": 187,
                    "isaccepted": True
                },
                permission=(bob, Permission.ACTIVE));
            self.assertEqual("acceptwage not id", "");
        except Error as err:
            self.assertTrue("There's no wage contract with such an id" in err.message)
            print("acceptwage id passed");
        try:
            wageservice2.push_action(
                "acceptwage",
                {
                    "worker": charlie,
                    "id": 0,
                    "isaccepted": True
                },
                permission=(charlie, Permission.ACTIVE));
            self.assertEqual("acceptwage not worker", "");
        except Error as err:
            self.assertTrue("You are not worker" in err.message)
            print("acceptwage ownership passed");
        try:
            wageservice2.push_action(
                "acceptwage",
                {
                    "worker": bob,
                    "id": 1,
                    "isaccepted": True
                },
                permission=(bob, Permission.ACTIVE));
            self.assertEqual("acceptwage not specified", "");
        except Error as err:
            self.assertTrue("The wage contract isn't specified yet" in err.message)
            print("acceptwage specified passed");
        try:
            wageservice2.push_action(
                "acceptwage",
                {
                    "worker": bob,
                    "id": 2,
                    "isaccepted": True
                },
                permission=(bob, Permission.ACTIVE));
            self.assertEqual("acceptwage already accepted", "");
        except Error as err:
            self.assertTrue("The wage contract is already accepted" in err.message)
            print("acceptwage accepted passed");
    def test_int_errors(self):
        try:
            wageservice2.push_action(
                "defertxn",
                {
                    "delay": 100,
                    "_id": 2
                },
                permission=(bob, Permission.ACTIVE));
            self.assertEqual("defertxn auth", "");
        except Error as err:
            self.assertTrue("missing authority of wageservice2" in err.message)
            print("defertxn auth passed");
        try:
            wageservice2.push_action(
                "autocashout",
                {
                    "id": 2
                },
                permission=(bob, Permission.ACTIVE));
            self.assertEqual("autocashout auth", "");
        except Error as err:
            self.assertTrue("missing authority of wageservice2" in err.message)
            print("autocashout auth passed");
        try:
            wageservice2.push_action(
                "autocashout",
                {
                    "id": 82
                },
                permission=(wageservice2, Permission.ACTIVE));
            self.assertEqual("autocashout wrong id", "");
        except Error as err:
            self.assertTrue("There's no wage contract with such an id" in err.message)
            print("autocashout id passed");

        try:
            wageservice2.push_action(
                "autocashout",
                {
                    "id": 0
                },
                permission=(wageservice2, Permission.ACTIVE));
            self.assertEqual("autocashout not accepted", "");
        except Error as err:
            self.assertTrue("The wage contract isn't accepted" in err.message)
            print("autocashout accepted passed");
        try:
            wageservice2.push_action(
                "autocashout",
                {
                    "id": 2
                },
                permission=(wageservice2, Permission.ACTIVE));
            self.assertEqual("autocashout not ended", "");
        except Error as err:
            self.assertTrue("The contract isn't ended" in err.message)
            print("autocashout ended passed");
if __name__ == '__main__':
    unittest.main()

stop()
