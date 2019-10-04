#include <eosio/eosio.hpp>
#include <eosio/print.hpp>
#include <eosio/asset.hpp>
#include <eosio/system.hpp>

#include <utility>
#include <functional>
// #include <eosio/transaction.hpp>

using namespace eosio;

class CommitOrRollback
{
    bool committed;
    std::function<void()> rollback;

public:
    CommitOrRollback(std::function<void()> &&fail_handler)
        : committed(false),
          rollback(std::move(fail_handler))
    {
    }

    void commit() noexcept { committed = true; }

    ~CommitOrRollback()
    {
        if (!committed)
            rollback();
    }
};
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

      wage_table.emplace(get_self(), [&](auto &row) {
        int primary_key = wage_table.available_primary_key();
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
        row.start_date = NULL;
        row.end_date = NULL;
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

      wage_table wage_table(get_self(), employer.value);
      auto wage = wage_table.begin();
      check(wage != wage_table.end(), "Not found any wage of this employer");
      while(wage->wage_amount.amount != quantity.amount && wage != wage_table.end()) {
        wage++;
      }

      check(wage != wage_table.end(), "Not found any wage with this amount. Please check your placed wage.");
      wage_table.modify(wage, get_self(), [&](auto& raw) {
        uint32_t start = now();
        uint32_t end = start + (86400 * raw.term_days);
        raw.is_charged = true;
        raw.wage_frozen = quantity;
        raw.start_date = start;
        raw.end_date = end;
      });
    }

    [[eosio::action]]
    void closewage(const name& employer, const uint64_t& id) {
      require_auth(employer);
      wage_table wage_table(get_self(), employer.value);
      auto wage = wage_table.find(id);
      check(wage != wage_table.end(), "This wage doesn't exist");
      if(wage->is_charged == true) {
        cashOutTransaction(wage, wage_table);
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
      check(wage->is_charged == true, "The wage contract isn't charged");
      check(wage->end_date < now(), "The contract isn't ended");

      cashOutTransaction(wage, wage_table);
    }

    [[eosio::action]]
    void acceptwage(const name& worker, const bool& isaccepted) {

    }

    // const in wage_table probably overloaded because it causes an error
    void cashOutTransaction(const wage_table::const_iterator& wage, wage_table& table) {
      wage_table::const_iterator wage_copy = wage;
      auto eraseRollback = [&]() {
        table.emplace(get_self(), [&](auto &row) {
          // int primary_key = wage_table.available_primary_key();
          // int64_t whole_wage = wage_per_day * days;
          row.id = wage_copy->id;
          row.employer = wage_copy->employer;
          row.worker = wage_copy->worker;
          row.wage_amount = wage_copy->wage_amount;
          row.wage_frozen = wage_copy->wage_frozen;
          row.wage_per_day = wage_copy->wage_per_day;
          row.is_charged = wage_copy->is_charged;
          row.term_days = wage_copy->term_days;
          row.worked_days = wage->worked_days;
          row.start_date = wage_copy->start_date;
          row.end_date = wage_copy->end_date;
        });
      };
      CommitOrRollback rollbackTransaction(eraseRollback);

      eosio::asset fullwage = wage->wage_per_day * wage->worked_days;
      eosio::asset rest = wage->wage_frozen - fullwage;
      table.erase(wage);

      action{
        permission_level{get_self(), "active"_n},
        "eosio.token"_n,
        "transfer"_n,
        std::make_tuple(get_self(), wage_copy->worker, fullwage, std::string("You have got your wage! Congratulations"))
      }.send();

      action{
        permission_level{get_self(), "active"_n},
        "eosio.token"_n,
        "transfer"_n,
        std::make_tuple(get_self(), wage_copy->employer, rest, std::string("You have got the rest of wage money"))
      }.send();
      rollbackTransaction.commit();
    }
};
