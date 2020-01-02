from eosfactory.eosf import *
reset()

create_master_account("master")

create_account("wageservice", master)
timer = Contract(wageservice, "/home/ally/contracts/wageservice")

timer.build()

stop()
