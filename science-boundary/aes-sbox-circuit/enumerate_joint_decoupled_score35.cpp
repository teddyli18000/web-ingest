// Enumerate the 136 score-35 pairs from screen_joint_decoupled_helper_frontier.cpp.
//
// This deliberately reuses the existing frontier implementation in the same
// translation unit so its closure semantics and regression constants cannot drift.
// Output is CSV: front_id,final_id,middle_support,pre_lb,output_lb,distance.

#define main p008_helper_frontier_original_main
#include "screen_joint_decoupled_helper_frontier.cpp"
#undef main

#include <cstdlib>

int main() {
    for (int i = 0; i < 8; ++i) is_input[1 << i] = true;

    int x[8]; for (int i = 0; i < 8; ++i) x[i] = 1 << i;
    vector<int> q;
    q.push_back(x[5]^x[0]); q.push_back(x[1]^x[5]); q.push_back(q[1]^x[2]);
    q.push_back(q[2]^x[0]); q.push_back(q[2]^x[6]); q.push_back(x[0]^x[1]);
    q.push_back(q[5]^x[4]); q.push_back(q[6]^q[4]); q.push_back(q[7]^x[3]);
    q.push_back(q[8]^x[7]); q.push_back(q[9]^q[3]); q.push_back(q[9]^q[5]);
    q.push_back(q[10]^x[4]); q.push_back(q[11]^x[6]); q.push_back(q[12]^x[5]);
    q.push_back(q[12]^q[0]); q.push_back(q[14]^q[8]); q.push_back(q[16]^q[10]);
    planes = {{{q[11],q[10]},{q[3],q[12]},{q[15],q[2]},{q[8],q[7]},
               {x[6],q[17]},{q[4],x[7]},{q[13],q[16]},{q[9],q[6]},{q[0],q[14]}}};

    const int output_columns[18] = {200,230,68,227,185,8,113,183,241,
                                    17,64,245,128,16,84,1,136,19};
    for (int i = 0; i < 9; ++i) outpairs[i] = {output_columns[i], output_columns[i+9]};

    constexpr int N = 19683;
    vector<array<int,9>> choices(N);
    vector<int> middle(N), output_lb(N);
    vector<Bits> output_bits(N);
    for (int id = 0; id < N; ++id) {
        int z = id;
        for (int i = 8; i >= 0; --i) { choices[id][i] = z % 3; z /= 3; }
        middle[id] = middle_support_lb(choices[id]);
        Bits t;
        for (int i = 0; i < 9; ++i) {
            auto p = dual_columns(outpairs[i], choices[id][i]);
            for (int v : {p.first,p.second}) if (v && !is_input[v]) set_bit(t,v);
        }
        output_bits[id] = t;
        output_lb[id] = helper_lb_0(t);
    }

    constexpr int U = 262144;
    vector<int> pre_lb(U);
    vector<Bits> pre_bits(U);
    for (int id = 0; id < U; ++id) {
        int z = id;
        Bits t;
        for (int i = 8; i >= 0; --i) {
            int state = z & 3; z >>= 2;
            if (state < 3) {
                auto p = orient(planes[i], state);
                for (int v : {p.first,p.second}) if (v && !is_input[v]) set_bit(t,v);
            } else {
                auto [a,b] = planes[i];
                for (int v : {a,b,a^b}) if (v && !is_input[v]) set_bit(t,v);
            }
        }
        pre_bits[id] = t;
        pre_lb[id] = helper_lb_0(t);
    }

    auto union_id = [&](const array<int,9>& f, const array<int,9>& g) {
        int id = 0;
        for (int i = 0; i < 9; ++i) id = (id << 2) | (f[i] == g[i] ? f[i] : 3);
        return id;
    };

    unordered_set<int> union_survivors, output_survivors, front_survivors;
    long long pass0 = 0;
    for (int f = 0; f < N; ++f) for (int g = 0; g < N; ++g) {
        int u = union_id(choices[f], choices[g]);
        if (pre_lb[u] + middle[f] + output_lb[g] <= 36) {
            ++pass0;
            union_survivors.insert(u); output_survivors.insert(g); front_survivors.insert(f);
        }
    }
    if (pass0 != 464931) return 2;

    for (int u : union_survivors) pre_lb[u] = helper_lb_1(pre_bits[u]);
    for (int g : output_survivors) output_lb[g] = helper_lb_1(output_bits[g]);

    cout << "front_id,final_id,middle_support,pre_lb,output_lb,distance\n";
    long long score35 = 0, pass1 = 0;
    for (int f : front_survivors) for (int g : output_survivors) {
        int u = union_id(choices[f], choices[g]);
        if (!union_survivors.count(u)) continue;
        int score = pre_lb[u] + middle[f] + output_lb[g];
        if (score > 36) continue;
        ++pass1;
        if (score != 35) continue;
        int d = 0; for (int i = 0; i < 9; ++i) d += choices[f][i] != choices[g][i];
        cout << f << ',' << g << ',' << middle[f] << ',' << pre_lb[u] << ',' << output_lb[g] << ',' << d << '\n';
        ++score35;
    }
    if (pass1 != 9761 || score35 != 136) return 3;
    return 0;
}
