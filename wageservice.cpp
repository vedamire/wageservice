#include <eosio/eosio.hpp>
#include <eosio/print.hpp>
#include <eosio/asset.hpp>
#include <eosio/system.hpp>


#include <eosio/transaction.hpp>

using namespace eosio;

// typedef float amount;
// https://eosio.stackexchange.com/questions/371/how-can-i-create-a-deferred-transaction
// https://vc.ru/crypto/64813-3-poleznyh-resheniya-dlya-smart-kontraktov-na-eosio
class [[eosio::contract("wageservice")]] wageservice : public eosio::contract {
  private:
    const symbol wage_symbol;

    struct [[eosio::table]] wage_v1
    {
      uint64_t id;
      name employer;
      name worker;
      eosio::asset wage_amount;
      eosio::asset wage_frozen;
      eosio::asset wage_per_day;
      bool is_charged;
      uint32_t term_days;
      uint32_t worked_days;
      bool is_accepted;
      uint32_t start_date;
      uint32_t end_date;
      uint64_t primary_key() const { return id; }
    };
    using wage_table = eosio::multi_index<"wagev1"_n, wage_v1>;

    uint32_t now() {
      return current_time_point().sec_since_epoch();
    }


  public:
    using contract::contract;
    wageservice(name receiver, name code, datastream<const char *> ds) : contract(receiver, code, ds), wage_symbol("SYS", 4){}

    [[eosio::action]]
    void placewage(const name& employer, const name& worker, const int64_t& wage_per_day, const uint32_t& days) {
      require_auth(employer);
      check(is_account(worker), "Worker's account doesn't exist");
      check(wage_per_day > 0, "Wage must be positive");
      check(days >= 1, "Wage must be minimum for 1 day");

      wage_table wage_table(get_self(), employer.value);

      int primary_key = wage_table.available_primary_key();
      wage_table.emplace(get_self(), [&](auto &row) {
        int64_t whole_wage = wage_per_day * days;
        row.id = primary_key;
        row.employer = employer;
        row.worker = worker;
        row.wage_amount = eosio::asset(whole_wage, wage_symbol);
        row.wage_frozen = eosio::asset(0, wage_symbol);
        row.wage_per_day = eosio::asset(wage_per_day, wage_symbol);
        row.is_charged = false;
        row.term_days = days;
        row.worked_days = 0;
        row.is_accepted = false;
        row.start_date = NULL;
        row.end_date = NULL;
      });

// 86400
      send_expiration_cleaner(employer, primary_key, 86400);
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

      wage_table wage_table(get_self(), employer.value);
      auto wage = wage_table.begin();

      check(wage != wage_table.end(), "Not found any wage of this employer");
      check(wage->is_charged == false, "The wage is already charged");

      while(wage->wage_amount.amount != quantity.amount && wage != wage_table.end()) {
        wage++;
      }

      check(wage != wage_table.end(), "Not found any wage with this amount. Please check your placed wage.");
      wage_table.modify(wage, get_self(), [&](auto& raw) {
        // uint32_t start = now();
        // uint32_t end = start + (86400 * raw.term_days);
        raw.is_charged = true;
        raw.wage_frozen = quantity;
        // raw.start_date = start;
        // raw.end_date = end;
      });

      notify_user(employer, std::string(" Your wage is successfully chaged. Waiting for worker to accept"));
      std::string notification = std::string(" Employer placed job for you! Employer: ") + name{employer}.to_string() + ", jobId: " + std::to_string(wage->id);
      notify_user(wage->worker, notification);
    }

    [[eosio::action]]
    void closewage(const name& employer, const uint64_t& id) {
      require_auth(employer);
      wage_table wage_table(get_self(), employer.value);
      auto wage = wage_table.find(id);
      check(wage != wage_table.end(), "This wage doesn't exist");
      if(wage->is_charged == true) {
        notify_user(wage->worker, std::string("Your wage contract is closed by employer. All your work days will be paid"));
        cash_out_transaction(wage, wage_table);
      } else {
        wage_table.erase(wage);
      }
    }

    [[eosio::action]]
    void addworkday(const name& employer, const uint64_t& id) {
      require_auth(employer);

      wage_table wage_table(get_self(), employer.value);
      auto wage = wage_table.find(id);
      check(wage != wage_table.end(), "No wage contract found with this id");
      check(wage->is_accepted == true, "This wage contract isn't accepted");
      wage_table.modify(wage, get_self(), [&](auto& row) {
        row.worked_days = row.worked_days + 1;
      });
    }

    [[eosio::action]]
    void claimwage(const name& worker, const name& employer, const uint64_t& id) {
      require_auth(worker);
      check(is_account(employer), "Employer's account doesn't exist");
      wage_table wage_table(get_self(), employer.value);
      auto wage = wage_table.find(id);
      check(wage != wage_table.end(), "There's no wage contract with such an id");
      // check(wage->is_charged == true, "The wage contract isn't charged");
      check(wage->worker == worker, "You are not the worker of this wage contract");
      check(wage->is_accepted == true, "The wage contract isn't accepted");
      check(wage->end_date < now(), "The contract isn't ended");

      cash_out_transaction(wage, wage_table);
    }

    [[eosio::action]]
    void acceptwage(const name& worker, const name& employer, const uint64_t& id, const bool& isaccepted) {
      require_auth(worker);
      check(is_account(employer), "Employer's account doesn't exist"); // If employer deletes his account it may cause a problem
      wage_table wage_table(get_self(), employer.value);
      auto wage = wage_table.find(id);
      check(wage != wage_table.end(), "There's no wage contract with such an id");
      check(wage->is_charged == true, "The wage contract isn't charged. Contract must be charge before accepted");
      check(wage->is_accepted == false, "The wage contract is already accepted");

      if(isaccepted) {
        wage_table.modify(wage, get_self(), [&](auto& row) {
          uint32_t start = now();
          uint32_t end = start + (86400 * row.term_days);
          row.is_accepted = true;
          row.start_date = start;
          row.end_date = end;
        });
        print("Job is successfully accepted! Job starts at this moment");
        notify_user(employer, std::string(" the wage contract is accepted by worker. Job is started. Worker: ")
        + name{worker}.to_string()
        + ", id: " + std::to_string(id));
      } else {
        print("You have declined the job. Come back if you've changed your mind");
        notify_user(employer, std::string(" the wage contract is declined by worker. Close wage or try to change his mind.")
         + name{worker}.to_string()
         + ", id: " + std::to_string(id));
      }
    }

    [[eosio::action]]
    void notify(const name& user, const std::string& msg) {
      require_auth(get_self());
      require_recipient(user);
    }

    [[eosio::action]]
    void expireclean(const name& employer, const uint64_t& id) {
      require_auth(get_self());
      // require_recipient(user);
      check(is_account(employer), "Employer's account doesn't exist"); // If employer deletes his account it may cause a problem
      wage_table wage_table(get_self(), employer.value);
      auto wage = wage_table.find(id);
      check(wage != wage_table.end(), "There's no wage contract with such an id");
      check(wage->is_charged == false, "The wage contract is charged. No need to erase it");
      wage_table.erase(wage);
    }

  private:
    void send_expiration_cleaner(const name& employer, const uint64_t& id, const uint32_t& delay) {
      eosio::transaction deferred;

      deferred.actions.emplace_back (
        permission_level{get_self(),"active"_n},
        get_self(), "expireclean"_n,
        std::make_tuple(employer, id)
      );
      deferred.delay_sec = delay;

      deferred.send(get_self().value, get_self());
    }

    void send_auto_cashout(const name& employer, const uint64_t& id) {
      // eosio::transaction deferred;
      //
      // deferred.actions.emplace_back (
      //   permission_level{get_self(),"active"_n},
      //   get_self(), "expireclean"_n,
      //   std::make_tuple(employer, id)
      // );
      //
      // deferred.send(user.value, get_self());
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
