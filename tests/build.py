from eosfactory.eosf import *
reset()

create_master_account("master")

create_account("locktimer", master)
timer = Contract(locktimer, "/home/ally/contracts/wageservice")

timer.build()

stop()
