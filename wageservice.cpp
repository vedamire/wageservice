#include <eosio/eosio.hpp>
#include <eosio/print.hpp>
#include <eosio/asset.hpp>
#include <eosio/system.hpp>
#include <eosio/transaction.hpp>
#include <eosio/singleton.hpp>

using namespace eosio;

class [[eosio::contract("wageservice")]] wageservice : public eosio::contract {
  private:
    // observer observer;
    const symbol wage_symbol;
    const asset MIN;
    const asset FEE;

    struct counter {
     uint64_t deferid;
   };

   typedef eosio::singleton<"counter"_n, counter> counter_table;
   counter_table counters;

    struct [[eosio::table]] wage_v1
    {
      uint64_t id;
      name employer;
      name worker;
      eosio::asset wage_frozen;
      eosio::asset wage_per_day;
      bool is_specified;
      uint32_t term_days;
      uint32_t worked_days;
      bool is_accepted;
      uint32_t start_date;
      uint32_t end_date;
      uint64_t primary_key() const { return id; }
      uint64_t get_secondary_1() const { return employer.value;}

    };
    typedef eosio::multi_index<"wagev1"_n, wage_v1, indexed_by<"byemployer"_n, const_mem_fun<wage_v1, uint64_t, &wage_v1::get_secondary_1>>> wage_table;

    wage_table table_wage;

    uint32_t now() {
      return current_time_point().sec_since_epoch();
    }


  public:
    using contract::contract;
    wageservice(name receiver, name code, datastream<const char *> ds) : contract(receiver, code, ds), wage_symbol("EOS", 4),
     MIN(10000, this->wage_symbol), FEE(300, this->wage_symbol), table_wage(_self, _self.value), counters(_self, _self.value)  {}


     [[eosio::on_notify("eosio.token::transfer")]]
     void chargewage(const name& employer, const name& to, const eosio::asset& quantity, const std::string& memo)
     {
       if (to != get_self() || employer == get_self())
       {
         print("These are not the droids you are looking for.");
         return;
       }

       check(quantity.amount > 0, "When pigs fly");
       check(quantity.symbol == wage_symbol, "These are not the droids you are looking for.");

       if(memo == "placewage") {
         print("Quantity: ", quantity, " ");
         print("MIN: ", MIN, " ");
         print("FEE: ", FEE, " ");
         const asset minfee = MIN + FEE;
         print("minfee: ", minfee, " ");
         check(quantity >= minfee, "Full wage must be at least 1.0300 EOS");
         uint64_t primary_key = table_wage.available_primary_key();
         table_wage.emplace(get_self(), [&](auto &row) {
           // int64_t whole_wage = wage_per_day * days;
           row.id = primary_key;
           row.employer = employer;
           row.worker = employer;
           row.wage_frozen = quantity - FEE;
           row.wage_per_day = eosio::asset(0, wage_symbol);
           row.is_specified = false;
           row.term_days = NULL;
           row.worked_days = 0;
           row.is_accepted = false;
           row.start_date = NULL;
           row.end_date = NULL;
         });
       } else {
         check(memo == "replenish", "Wrong memo. To transfer money here use ether 'placewage' or 'replenish' memo");
         print("Account is successfully replenished");
       }
     }

    [[eosio::action]]
    void placewage(const name& employer, const uint64_t& id, const name& worker,  const uint32_t& days) {
      require_auth(employer);
      check(is_account(worker), "Worker's account doesn't exist");
      check(days >= 1 && days <= 90, "Wage must be minimum for 1 day and maximum for 90 days");
      auto wage = table_wage.find(id);
      check(wage != table_wage.end(), "This wage id doesn't exist");
      check(wage->employer == employer, "This is not your wage");
      check(wage->is_specified == false, "This wage is already specified");
      const int64_t converted_days = (int64_t) days;
      const asset wage_per_day = wage->wage_frozen / converted_days;
      check(wage_per_day >= MIN, "Wage per day must be at least 1 eos");
      table_wage.modify(wage, get_self(), [&](auto& row) {
        row.is_specified = true;
        row.worker = worker;
        row.term_days = days;
        row.wage_per_day = wage_per_day;
      });
    }

    [[eosio::action]]
    void closewage(const name& employer, const uint64_t& id) {
      require_auth(employer);
      auto wage = table_wage.find(id);
      check(wage != table_wage.end(), "This wage doesn't exist");
      check(wage->employer == employer, "This is not your wage");
      cash_out_transaction(wage, table_wage);
    }

    [[eosio::action]]
    void addworkday(const name& employer, const uint64_t& id) {
      require_auth(employer);
      auto wage = table_wage.find(id);

      check(wage != table_wage.end(), "No wage contract found with this id");
      check(wage->employer == employer, "This is not your wage");
      check(wage->is_accepted == true, "This wage contract isn't accepted");

      table_wage.modify(wage, get_self(), [&](auto& row) {
        row.worked_days = row.worked_days + 1;
      });
    }

    [[eosio::action]]
    void claimwage(const name& worker, const uint64_t& id) {
      require_auth(worker);
      auto wage = table_wage.find(id);

      check(wage != table_wage.end(), "There's no wage contract with such an id");
      check(wage->worker == worker, "You are not the worker of this wage contract");
      check(wage->is_accepted == true, "The wage contract isn't accepted");
      check(wage->end_date < now(), "The contract isn't ended");

      cash_out_transaction(wage, table_wage);
    }

    [[eosio::action]]
    void acceptwage(const name& worker, const uint64_t& id, const bool& isaccepted) {
      require_auth(worker);

      auto wage = table_wage.find(id);
      check(wage != table_wage.end(), "There's no wage contract with such an id");
      check(wage->is_specified == true, "The wage contract isn't specified yet");
      check(wage->worker == worker, "You are not worker");
      check(wage->is_accepted == false, "The wage contract is already accepted");

      if(isaccepted) {
        table_wage.modify(wage, get_self(), [&](auto& row) {
          uint32_t start = now();
          uint32_t end = start + (86400 * row.term_days);
          row.is_accepted = true;
          row.start_date = start;
          row.end_date = end;
          send_auto_cashout(id, end - start);
        });
      } else {
      }
    }

    [[eosio::action]]
    void defertxn(const uint32_t& delay, const uint64_t& _id) {
        require_auth(get_self());
        eosio::transaction deferred;
        uint32_t max_delay = 3888000; //max delay supported by EOS 3888000
        if (delay <= max_delay) {
          deferred.actions.emplace_back (
            permission_level{get_self(), "active"_n},
            get_self(), "autocashout"_n,
            std::make_tuple(_id)
          );
          deferred.delay_sec = delay;
          deferred.send(updateId(), get_self());
        //perform your transaction here
        }
        else{
            uint32_t remaining_delay = delay - max_delay;
            // transaction to update the delay
            deferred.actions.emplace_back(
                eosio::permission_level{get_self(), "active"_n},
                get_self(),
                "defertxn"_n,
                std::make_tuple(remaining_delay, _id));
            deferred.delay_sec = max_delay; // here we set the new delay which is maximum until remaining_delay is less the max_delay
            deferred.send(updateId(), get_self());
        }
    }

    [[eosio::action]]
    void autocashout(const uint64_t& id) {
      require_auth(get_self());
      auto wage = table_wage.find(id);

      check(wage != table_wage.end(), "There's no wage contract with such an id");
      check(wage->is_accepted == true, "The wage contract isn't accepted");
      check(wage->end_date < now(), "The contract isn't ended");

      cash_out_transaction(wage, table_wage);
    }

  private:

    void send_auto_cashout(const uint64_t& id, const uint32_t& delay) {
      action (
        permission_level(get_self(),"active"_n),
        get_self(),
        "defertxn"_n,
        std::make_tuple(delay, id)
      ).send();
    }


    uint64_t updateId() {
      if(!counters.exists()) {
        uint64_t initial = 1000;
        counters.set(counter{initial}, get_self());
        return initial;
      }
      counter count = counters.get();
      counter newcounter = counter{count.deferid + (uint64_t) 1};
      counters.set(newcounter, get_self());
      return newcounter.deferid;
    }

    // const in wage_table probably overloaded because it causes an error
    void cash_out_transaction(const wage_table::const_iterator& wage, wage_table& table) {
      eosio::asset fullwage = wage->wage_per_day * wage->worked_days;
      eosio::asset rest = wage->wage_frozen - fullwage;
      table.erase(wage);

      if(fullwage.amount > 0) {
        action{
          permission_level{get_self(), "active"_n},
          "eosio.token"_n,
          "transfer"_n,
          std::make_tuple(get_self(), wage->worker, fullwage, std::string("You have got your wage! Congratulations"))
        }.send();
      }
      if(rest.amount > 0) {
        action{
          permission_level{get_self(), "active"_n},
          "eosio.token"_n,
          "transfer"_n,
          std::make_tuple(get_self(), wage->employer, rest, std::string("You have got the rest of wage money"))
        }.send();
      }
    }
};
