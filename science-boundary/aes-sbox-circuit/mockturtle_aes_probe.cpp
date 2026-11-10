// Independent XAG optimization probe for a verified AES S-box circuit.
// Outputs a full, complement-aware XAG netlist for independent GF(2) checking.
#include <mockturtle/networks/xag.hpp>
#include <mockturtle/algorithms/xag_resub.hpp>
#include <mockturtle/algorithms/cleanup.hpp>
#include <mockturtle/algorithms/resubstitution.hpp>
#include <mockturtle/views/depth_view.hpp>
#include <mockturtle/views/fanout_view.hpp>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>
#include <stdexcept>
using namespace mockturtle;
int main(int argc, char** argv) {
  if (argc != 6) {
    std::cerr << "usage: aes_xag_probe input.net output.net max_pis max_inserts odc\n";
    return 2;
  }
  const auto max_pis = static_cast<uint32_t>(std::stoi(argv[3]));
  const auto max_inserts = static_cast<uint32_t>(std::stoi(argv[4]));
  const auto odc_levels = std::stoi(argv[5]);
  std::ifstream in(argv[1]);
  if (!in) throw std::runtime_error("missing input");
  int n=0; in >> n;
  xag_network xag;
  std::vector<xag_network::signal> wires;
  for (int k=0;k<8;k++) wires.push_back(xag.create_pi());
  for (int k=0;k<n;k++){
    char op;int a,b;
    in >> op >> a >> b;
    if (!in || a>=static_cast<int>(wires.size()) || b>=static_cast<int>(wires.size()))
      throw std::runtime_error("malformed gate input");
    xag_network::signal next;
    if(op=='A') next=xag.create_and(wires[a],wires[b]);
    else if(op=='X') next=xag.create_xor(wires[a],wires[b]);
    else if(op=='N') next=xag.create_xnor(wires[a],wires[b]);
    else throw std::runtime_error("bad op");
    wires.push_back(next);
  }
  for(int k=0;k<8;k++){int idx;in>>idx;if(!in || idx>=static_cast<int>(wires.size()))throw std::runtime_error("bad PO");xag.create_po(wires[idx]);}
  xag=cleanup_dangling(xag);
  std::cerr << "[stage] initial XAG built, gates " << xag.num_gates() << "\n";
  const uint32_t before=xag.num_gates();
  resubstitution_params ps;
  ps.max_pis=max_pis;
  ps.max_divisors=150;
  ps.max_inserts=max_inserts;
  ps.odc_levels=odc_levels;
  ps.max_trials=200;
  ps.window_size=12;
  ps.use_dont_cares=(odc_levels!=0);
  depth_view depth_xag{ xag };
  fanout_view fanout_xag{ depth_xag };
  std::cerr << "[stage] wrapped fanout/depth views\n";
  xag_resubstitution(fanout_xag, ps);
  std::cerr << "[stage] xag_resubstitution returned\n";
  xag=cleanup_dangling(fanout_xag);
  std::cerr << "[stage] cleaned, gates " << xag.num_gates() << "\n";
  std::ofstream out(argv[2]);
  out << "C " << xag.num_gates() << " " << before << "\n";
  xag.foreach_pi([&](auto const& node){out << "I " << node << "\n";});
  xag.foreach_gate([&](auto const& node){
    char typ = xag.is_and(node)?'A':'X';
    std::vector<xag_network::signal> fs;
    xag.foreach_fanin(node,[&](auto const& f){fs.push_back(f);});
    out << "G " << node << " " << typ << " " << fs[0].index << " " << int(fs[0].complement)
        << " " << fs[1].index << " " << int(fs[1].complement) << "\n";
  });
  xag.foreach_po([&](auto const& s){out << "O " << s.index << " " << int(s.weight) << "\n";});
  std::cout << "{\"initial_xag_gates\":" << before
            << ",\"optimized_xag_gates\":" << xag.num_gates()
            << ",\"max_pis\":" << max_pis
            << ",\"max_inserts\":" << max_inserts
            << ",\"odc_levels\":" << odc_levels << "}\n";
  return 0;
}
