#include <eosio/eosio.hpp>
#include <eosio/print.hpp>
#include <eosio/asset.hpp>
#include <eosio/system.hpp>

using namespace eosio;

// typedef float amount;

class [[eosio::contract("wageservice")]] wageservice : public eosio::contract {
  private:
    const symbol wage_symbol;

    struct [[eosio::table]] wage
    {
      uint64_t id;
      name employer;
      name worker;
      int64_t wage_amount;
      eosio::asset wage_frozen;
      bool is_charged;
      uint32_t term_days;
      uint32_t start_date;
      uint32_t end_date;
      uint64_t primary_key() const { return id; }
    };
    using wage_table = eosio::multi_index<"wage"_n, wage>;

    uint32_t now() {
      return current_time_point().sec_since_epoch();
    }
  public:
    using contract::contract;
    wageservice(name receiver, name code, datastream<const char *> ds) : contract(receiver, code, ds), wage_symbol("SYS", 4){}

    [[eosio::action]]
    void placewage(const name& employer, const name& worker, const int64_t& wage, const uint32_t& days) {
      require_auth(employer);
      check(is_account(worker), "Worker's account doesn't exist");
      check(wage > 0, "Wage must be positive");
      check(days >= 1, "Wage must be minimum for 1 day");

      wage_table wage_table(get_self(), employer.value);

      wage_table.emplace(get_self(), [&](auto &row) {
        int primary_key = wage_table.available_primary_key();
        row.id = primary_key;
        row.employer = employer;
        row.worker = worker;
        row.wage_amount = wage;
        row.wage_frozen = eosio::asset(0, wage_symbol);
        row.is_charged = false;
        row.term_days = days;
        row.start_date = NULL;
        row.end_date = NULL;
      });
      // auto hodl_it = balance.find(hodl_symbol.raw());
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
      while(wage->wage_amount != quantity.amount && wage != wage_table.end()) {
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
    void claimback(const name& employer) {

    }

    [[eosio::action]]
    void claimwage(const name& worker) {

    }

    [[eosio::action]]
    void acceptwage(const name& worker, const bool& isaccepted) {

    }

    [[eosio::action]]
    void closewage(const name& employer) {

    }
};
