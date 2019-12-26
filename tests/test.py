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
        "to": zoro, "quantity": "1000000.0000 EOS", "memo": ""
    },
    zoro)

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

def getBalance(body):
    return float(captureConsole(lambda _: token_host.table("accounts", body))["rows"][0]["balance"].replace(" EOS", ""));
class TestStringMethods(unittest.TestCase):
    def setUp(self):
        time.sleep(1)
        bob_balance = getBalance(bob);
        charlie_balance = getBalance(charlie);
        print(str(charlie_balance)+"000 EOS");
        print(str(bob_balance)+"000 EOS");
        print(str(charlie_balance)+"000 EOS");
        print(str(bob_balance)+"000 EOS");
        token_host.push_action(
            "transfer",
            {
                "from": charlie, "to": zoro,
                "quantity": str(charlie_balance)+"000 EOS", "memo":""
            },
            charlie);
        token_host.push_action(
            "transfer",
            {
                "from": bob, "to": zoro,
                "quantity": str(bob_balance)+"000 EOS", "memo":""
            },
            bob);

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
        # time.sleep(3)

        print(getBalance(bob));
        print(getBalance(charlie));

    def test_single(self):

        token_host.push_action(
            "transfer",
            {
                "from": charlie, "to": wageservice,
                "quantity": "6.0000 EOS", "memo":"placewage"
            },
            charlie)
        js = captureConsole(lambda _:wageservice.table("wagev1", wageservice))["rows"][0];
        print(js);
        self.assertEqual(js["wage_frozen"], "6.0000 EOS")
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
        wageservice.push_action(
            "closewage",
            {
                "employer": charlie,
                "id": 0
            },
            permission=(charlie, Permission.ACTIVE));

        js = captureConsole(lambda _:token_host.table("accounts", bob));
        self.assertEqual(js["rows"][0]["balance"], '56.0000 EOS');
        # token_host.push_action(
        #     "transfer",
        #     {
        #         "from": bob, "to": charlie,
        #         "quantity": "6.0000 EOS", "memo":"placewage"
        #     },
        #     bob);
    def test_multiple(self):
        # time.sleep(10)
        for i in range(5):
            token_host.push_action(
                "transfer",
                {
                    "from": charlie, "to": wageservice1,
                    "quantity": "" + str(i+1) + ".0000 EOS", "memo":"placewage"
                },
                charlie);
        arr = captureConsole(lambda _: wageservice1.table("wagev1", wageservice1))["rows"];

        for i in range(5):
            self.assertEqual(arr[i]["id"], i);
            self.assertEqual(arr[i]["is_specified"], False);
        for i in range(5):
            wageservice1.push_action(
                "placewage",
                {
                    "employer": charlie,
                    "id": i,
                    "worker": bob,
                    "days": 4
                },
                permission=(charlie, Permission.ACTIVE))
        arr = captureConsole(lambda _: wageservice1.table("wagev1", wageservice1))["rows"];

        for i in range(5):
            self.assertEqual(arr[i]["is_accepted"], False);
            self.assertEqual(arr[i]["is_specified"], True);
            self.assertEqual(arr[i]["worker"], "bob");
        for i in range(5):
            wageservice1.push_action(
                "acceptwage",
                {
                    "worker": bob,
                    "id": i,
                    "isaccepted": True
                },
                permission=(bob, Permission.ACTIVE))
        arr = captureConsole(lambda _: wageservice1.table("wagev1", wageservice1))["rows"];
        for i in range(5):
            # self.assertEqual(arr[i]["id"], i);
            self.assertEqual(arr[i]["is_accepted"], True);
        for i in range(5):
            for r in range(4):
                time.sleep(0.5)
                wageservice1.push_action(
                    "addworkday",
                    {
                        "employer": charlie,
                        "id": i
                    },
                    permission=(charlie, Permission.ACTIVE));
        arr = captureConsole(lambda _: wageservice1.table("wagev1", wageservice1))["rows"];
        for i in range(5):
            # self.assertEqual(arr[i]["id"], i);
            self.assertEqual(arr[i]["worked_days"], 4);
        for i in range(5):
            wageservice1.push_action(
                "closewage",
                {
                    "employer": charlie,
                    "id": i
                },
                permission=(charlie, Permission.ACTIVE))
        # arr = captureConsole(lambda _: wageservice1.table("wagev1", wageservice1))["rows"];

        self.assertEqual(getBalance(wageservice1), 0);
        # print(js);
if __name__ == '__main__':
    unittest.main()

stop()
