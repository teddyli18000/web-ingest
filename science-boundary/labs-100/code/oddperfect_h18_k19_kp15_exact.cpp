// RETIRED 2026-10-31.
//
// The first version of this one-file kp15 checker incorrectly reused the
// gamma -> -gamma quotient that is valid only when c=0.  For kc>0, fixing the
// compressed sign representative c means both gamma orientations must be
// scored explicitly: global B->-B sends (c,gamma) to (-c,-gamma), not to
// (c,-gamma).
//
// Use the corrected split implementation instead:
//   oddperfect_h18_k19_kp15_compressed.cpp
//   oddperfect_h18_k19_kp15_fullgamma.cpp
//
// Git history retains the retired implementation as evidence of the audited
// dead end.  This source intentionally fails to compile so it cannot be used
// accidentally as an exclusion certificate.
#error "retired: use kp15_compressed.cpp + kp15_fullgamma.cpp"
