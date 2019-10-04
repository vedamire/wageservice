#include <eosio/eosio.hpp>
#include <eosio/print.hpp>
#include <eosio/asset.hpp>
#include <eosio/system.hpp>

using namespace eosio;

typedef float amount;

class [[eosio::contract("wageservice")]] wageservice : public eosio::contract {
  private:
    const symbol wage_symbol;

    struct [[eosio::table]] wage
    {
      uint64_t id;
      name employer;
      name worker;
      eosio::asset wage_frozen;
      bool is_charged;
      uint32_t term_days;
      uint32_t start_date;
      uint32_t end_date;
      uint64_t primary_key() const { return id; }
    };
    using wage_table = eosio::multi_index<"wage"_n, wage>;
  public:
    using contract::contract;
    wageservice(name receiver, name code, datastream<const char *> ds) : contract(receiver, code, ds), wage_symbol("SYS", 4){}
    uint32_t now() {
      return current_time_point().sec_since_epoch();
    }

    // [[eosio::action]]
    // void hellosomeone(name user) {
    //   require_auth(user);
    //   print("Hello, ", user);
    // }

    [[eosio::action]]
    void placewage(const name& employer, const name& worker, const amount& wage, const uint32_t& days) {
      require_auth(employer);
      // check(worker.)s
      check(wage > 0, "Wage must be positive");
    }

    [[eosio::on_notify("eosio.token::transfer")]]
    void chargewage(const name& hodler, const name& to, const eosio::asset& quantity, const std::string& memo)
    {
      if (to != get_self() || hodler == get_self())
      {
        print("These are not the droids you are looking for.");
        return;
      }
      check(quantity.amount > 0, "When pigs fly");
      check(quantity.symbol == wage_symbol, "These are not the droids you are looking for.");
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
