#include <eosio/eosio.hpp>
#include <eosio/print.hpp>
#include <eosio/asset.hpp>
#include <eosio/system.hpp>
#include <eosio/transaction.hpp>

// #include <vector>
// #include <functional>
// #include <map>

using namespace eosio;

typedef std::function<void(const uint64_t*, const name*, const name*)> notify_func;

// class observer
// {
//   public:
//
//     void add_func(const std::string& channel, const notify_func& func)
//     {
//       observer_channels[channel].push_back(func);
//     }
//     void notify_channel(const std::string& channel, const uint64_t* id, const name* employer, const name* worker)
//     {
//       auto target = observer_channels[channel];
//       for (auto& func : target) {
//         func(id, employer, worker);
//       }
//     }
//   private:
//     std::map<std::string, std::vector<notify_func>> observer_channels;
// };

class [[eosio::contract("wageservice")]] wageservice : public eosio::contract {
  private:
    // observer observer;
    const symbol wage_symbol;
    const asset MIN;
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
     MIN(1.0000, this->wage_symbol), table_wage(_self, _self.value) {
      using namespace std;
      // Preset everything
      // string placed_post = "placewage";
      // observer.add_func(placed_post, [&](const uint64_t* id, const name* employer, const name* worker) {
      //    this->notify_user(*employer, std::string(" Your wage is successfully placed! Charge it in 1 day. id: ") + to_string(*id));
      // });
      // string charge_post = "chargewage";
      // observer.add_func(charge_post, [&](const uint64_t* id, const name* employer, const name* worker) {
      //   this->notify_user(*employer, std::string(" Your wage is successfully charged. Waiting for worker to accept"));
      // });
      // observer.add_func(charge_post, [&](const uint64_t* id, const name* employer, const name* worker) {
      //   std::string notification = std::string(" Employer placed job for you! Employer: ") + name{*employer}.to_string() + ", jobId: " + std::to_string(*id);
      //   this->notify_user(*worker, notification);
      // });
      // string closed_post = "closewage";
      // observer.add_func(closed_post, [&](const uint64_t* id, const name* employer, const name* worker) {
      //   this->notify_user(*worker, std::string("Your wage contract is closed by employer. All your work days will be paid"));
      // });
      // string workday_post = "addworkday";
      // observer.add_func(workday_post, [&](const uint64_t* id, const name* employer, const name* worker) {
      //   print("You've successfully added a day to the wage contract!");
      //   this->notify_user(*worker, std::string("Employer successfully added your work day!"));
      // });
      // string claimed_post = "claimwage";
      // string accepted_post = "acceptwage_accepted";
      // observer.add_func(accepted_post, [&](const uint64_t* id, const name* employer, const name* worker) {
      //   print("Job is successfully accepted! Job starts at this moment");
      //   notify_user(*employer, std::string(" the wage contract is accepted by worker. Job is started. Worker: ")
      //   + worker->to_string()
      //   + ", id: " + std::to_string(*id));
      // });
      //
      // string declined_post = "acceptwage_declined";
      // observer.add_func(declined_post, [&](const uint64_t* id, const name* employer, const name* worker) {
      //   print("You have declined the job. Come back if you've changed your mind");
      //   notify_user(*employer, std::string(" the wage contract is declined by worker. Close wage or try to change his mind.")
      //    + worker->to_string()
      //    + ", id: " + std::to_string(*id));
      // });
    }

    [[eosio::action]]
    void placewage(const name& employer, const uint64_t& id, const name& worker,  const uint32_t& days) {
      require_auth(employer);
      check(is_account(worker), "Worker's account doesn't exist");
      check(days >= 1 && days <= 90, "Wage must be minimum for 1 day and maximum for 90 days");
      auto wage = table_wage.find(id);
      check(wage != table_wage.end(), "This wage doesn't exist");
      check(wage->employer == employer, "This is not your wage");
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
        uint64_t primary_key = table_wage.available_primary_key();
        table_wage.emplace(get_self(), [&](auto &row) {
          // int64_t whole_wage = wage_per_day * days;
          row.id = primary_key;
          row.employer = employer;
          row.worker = employer;
          row.wage_frozen = quantity;
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
    void closewage(const name& employer, const uint64_t& id) {
      require_auth(employer);
      auto wage = table_wage.find(id);
      check(wage != table_wage.end(), "This wage doesn't exist");
      check(wage->employer == employer, "This is not your wage");
      cash_out_transaction(wage, table_wage);
      cancel_deferred(wage->id);
      // observer.notify_channel(__func__, &wage->id, &wage->employer, &wage->worker);

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
    void claimwage(const name& worker, const name& employer, const uint64_t& id) {
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
      check(wage->worker == worker, "You are not worker");
      check(wage->is_specified == true, "The wage contract isn't charged. Contract must be charge before accepted");
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
        // observer.notify_channel(std::string(__func__) + "_accepted", &wage->id, &wage->employer, &wage->worker);
      } else {
        // observer.notify_channel(std::string(__func__) + "_declined", &wage->id, &wage->employer, &wage->worker);
      }
    }

    [[eosio::action]]
    void notify(const name& user, const std::string& msg) {
      require_auth(get_self());
      require_recipient(user);
    }

    [[eosio::action]]
    void autocashout(const uint64_t& id) {
      require_auth(get_self());
      auto wage = table_wage.find(id);

      check(wage != table_wage.end(), "There's no wage contract with such an id");
      check(wage->is_accepted == true, "The wage contract isn't accepted");

      cash_out_transaction(wage, table_wage);
    }

  private:
    void send_auto_cashout(const uint64_t& id, const uint32_t& delay) {
      eosio::transaction deferred;

      deferred.actions.emplace_back (
        permission_level{get_self(), "active"_n},
        get_self(), "autocashout"_n,
        std::make_tuple(id)
      );
      deferred.delay_sec = delay;
      deferred.send(id, get_self());
    }

    void notify_user(const name& user, const std::string& message) {
      action(
        permission_level{get_self(), "active"_n},
        get_self(),
        "notify"_n,
        std::make_tuple(user, name{user}.to_string() + message)
      ).send();
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
