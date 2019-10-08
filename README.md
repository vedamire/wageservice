# Wage service
EOS smart contract that allows you to create a wage contract and manage payments.

Actions:
1. Place wage (placewage). Requires:
eosio::name employer (who pushes the action),
eosio::name worker,
wage per day,
term of contract in days.
Creates wage contract in table. You have to transfer to contract wageperday * days to charge it. This wage must be charged during 1 day after placement. Otherwise a deferred transaction will clean it.

2. Charge wage (chargewage). Requires: none.
Charging wage. This is actually not an action. This is event on transfer tokens to smart contract. If quantity of transfer matches charge amount and sender matches employer, the wage will be successfully charged.

3. Accept wage (acceptwage). Requires:
eosio::name worker (who pushes the action),
wage id,
bool isAccepted. Worker accepts wage contract. After the wage contract is charged a worker should accept to start contract. If worker accepts wage, contract sends deferred action that automaticly will pay worker for all his worked days and send the rest to employer. It is called "cashout".

4. Add work day (addworkday). Requires:
eosio::name employer (who pushes the action),
wage id. Employer adds work day to wage contract and confirms that a worker has worked this day.

5. Claim wage (claimwage). Requires:
eosio::name worker (who pushes the action),
eosio::name employer,
wage id. If automatic deferred action is failed to execute worker can manually claim his wage after contract term is expired.

6. Close wage (closewage). Requires:
eosio::name employer (who pushes the action),
wage id. Closes wage contract ahead of schedule. If wage contract is already charged or even accepted, the contract will transfer wage for all worked days to worker, the rest will be sent back to employer.
