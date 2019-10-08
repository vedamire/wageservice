# Wage service
EOS smart contract that allows you to create a wage contract and manage payments.

## Idea
When a worker and an employer agree to collaborate, they have a problem. Employer wants worker to work until term of work ends without leaving. Therefore he agrees only to pay his worker after a certain term. Worker wants to be payed. If employer wants to cheat worker, when job term will end, a worker will have no chance to get his wage. This contract solves this problem.

## Actions:

* Place wage (placewage). Requires:
  * eosio::name employer (who pushes the action),
  * eosio::name worker,
  * wage per day,
  * term of contract in days.

Creates wage contract in table. You have to transfer to contract wageperday * days to charge it. This wage must be charged during 1 day after placement. Otherwise a deferred transaction will clean it.

* Charge wage (chargewage). Requires: none.

Charging wage. This is actually not an action. This is event on transfer tokens to smart contract. If quantity of transfer matches charge amount and sender matches employer, the wage will be successfully charged.

* Accept wage (acceptwage). Requires:
  * eosio::name worker (who pushes the action),
  * wage id,
  * bool isAccepted.

Worker accepts wage contract. After the wage contract is charged a worker should accept to start contract. If worker accepts wage, contract sends deferred action that automaticly will pay worker for all his worked days and send the rest to employer. It is called "cashout".


* Add work day (addworkday). Requires:
  * eosio::name employer (who pushes the action),
  * wage id.

Employer adds work day to wage contract and confirms that a worker has worked this day.

* Claim wage (claimwage). Requires:
  * eosio::name worker (who pushes the action),
  * eosio::name employer,
  * wage id.

If automatic deferred action is failed to execute worker can manually claim his wage after contract term is expired.

* Close wage (closewage). Requires:
  * eosio::name employer (who pushes the action),
  * wage id.

Closes wage contract ahead of schedule. If wage contract is already charged or even accepted, the contract will transfer wage for all worked days to worker, the rest will be sent back to employer.

## License & Copyright
[GNU AGPL](https://github.com/vedamire/wageservice/blob/master/LICENSE)
Copyright © Vedamir Efanov 2019. All rights reserved.

