# Simple implementation of P-Q SRP from 2017.
# Representation of polynomials: constant -> x^n. E.g. 5x^3 + 2x^2 + 1 = [1, 0, 2, 5]

import math
import random
from utils.polynomial import add, sub, mul_simple, generate_modulo_polynomial, generate_random_polynomial, \
    generate_correct_complementary_coefficient, generate_constant_polynomial, generate_discrete_gaussian_polynomial
from utils.infinity_norm import infinity_norm_iterable, symmetric_mod
from utils.magic import signal_function, robust_extractor, hint_function
from cryptography.hazmat.primitives import hashes
from kyber import create_one_cbd_poly

# Params based on Section 4.1
N = 1024
Q = 1073479681
STD_DEV = 3.192

ETA = 2

# THIS IS NOT HOW TO DO IT !!! THIS IS JUST FOR PROOF-OF-CONCEPT !!! THIS IS NOT HOW TO DO IT
I = "identity123"
PWD = "password123"
SALT = "salt123".encode()
# THIS IS NOT HOW TO DO IT !!! THIS IS JUST FOR PROOF-OF-CONCEPT !!! THIS IS NOT HOW TO DO IT


def create_seeds():
    # seed1 = SHA3-256(salt||SHA3-256(I||pwd))
    digest_inner = hashes.Hash(hashes.SHA3_256())
    digest_inner.update((I + PWD).encode())
    inner_hash = digest_inner.finalize()
    digest_outer = hashes.Hash(hashes.SHA3_256())
    digest_outer.update(SALT + inner_hash)
    seed1 = digest_outer.finalize()
    # seed2 = SHA3-256(seed1)
    digest = hashes.Hash(hashes.SHA3_256())
    digest.update(seed1)
    seed2 = digest.finalize()
    return seed1, seed2


# Phase 0 in the protocol - verifier creation.
def phase_0(a):
    # CLIENT: v = asv + 2ev
    modulo_polynomial = generate_modulo_polynomial(N)
    # seed1 = SHA3-256(salt||SHA3-256(I||pwd)); seed2 = SHA3-256(seed1)
    seed1, seed2 = create_seeds()
    sv = create_one_cbd_poly(N, ETA, seed1, Q)
    ev = create_one_cbd_poly(N, ETA, seed2, Q)
    a_sv = mul_simple(a, sv, modulo_polynomial, Q)
    two_ev = mul_simple(generate_constant_polynomial(2, N), ev, modulo_polynomial, Q)
    v = add(a_sv, two_ev, Q)
    return v, sv  # Returning sv just for debugging reasons - In phase1 client should generate new, not use the old one.


# Prints both sigmas and compute statistics on how many bits they agree.
def compare_sigmas(si, sj):
    #print("Client's side: ", si)
    #print("Server's side: ", sj)
    assert len(si) == len(sj)
    num_of_correct_ones = 0
    for i in range(len(si)):
        num_of_correct_ones += 1 if si[i] == sj[i] else 0
    print(f"Sigmas agreed on {num_of_correct_ones} number of bits out of {len(si)} number of bits. That is {num_of_correct_ones * 100 / len(si)} percent.")


# Checks how many tuples (also with positions) of ki and kj have the same parity, correct error tolerance,
# how many tuples (again with positions) fulfill my condition.
# Lastly checks how many of those (without and with my condition) generate the same output.
def compare_ki_kj(ki, kj, si, sj):  # TODO: maybe do better statistics?
    ok_parity = []
    ok_error_tolerance = []
    assert len(ki) == len(kj) == len(si) == len(sj)
    for i in range(len(si)):
        parity = (ki[i] - kj[i]) % 2 == 0  # they have the same parity
        #error_tolerance = infinity_norm(ki[i] - kj[i], Q) <= math.floor(Q / 4) - 2
        error_tolerance = abs(ki[i] - kj[i]) <= math.floor(Q / 4) - 2
        if parity:
            ok_parity.append(i)
        if error_tolerance:
            ok_error_tolerance.append(i)
    #print(ok_parity)
    #print(f"Number of elements with same parity: {len(ok_parity)}. That is {len(ok_parity) * 100 / len(si)} percent.")
    #print(ok_error_tolerance)
    #print(f"Number of elements with correct error tolerance: {len(ok_error_tolerance)}. That is {len(ok_error_tolerance) * 100 / len(si)} percent.")


# Phase 1 in the protocol - shared secret creation.
def phase_1(a, vs, sv):  # {u,v}s = u / verifier on server's side, {u,v}c = u / verifier on client's side
    modulo_polynomial = generate_modulo_polynomial(N)
    constant_two_polynomial = generate_constant_polynomial(2, N)
    # CLIENT: pi = as1 + 2e1
    s1 = generate_discrete_gaussian_polynomial(N, STD_DEV, Q)
    e1 = generate_discrete_gaussian_polynomial(N, STD_DEV, Q)
    a_s1 = mul_simple(a, s1, modulo_polynomial, Q)
    two_e1 = mul_simple(constant_two_polynomial, e1, modulo_polynomial, Q)
    pi = add(a_s1, two_e1, Q)
    # SERVER: pj = as1' + 2e1' + v
    s1prime = generate_discrete_gaussian_polynomial(N, STD_DEV, Q)
    e1prime = generate_discrete_gaussian_polynomial(N, STD_DEV, Q)
    a_s1prime = mul_simple(a, s1prime, modulo_polynomial, Q)
    two_e1prime = mul_simple(constant_two_polynomial, e1prime, modulo_polynomial, Q)
    added_fst_two = add(a_s1prime, two_e1prime, Q)
    pj = add(added_fst_two, vs, Q)
    # SERVER: u = XOF(H(pi||pj))
    us = generate_random_polynomial(N, Q)  # TODO for future: use XOF(H(pi||pj))
    # SERVER: kj = (v + pi)s1' + uv + 2e1'''
    e1_triple_prime = generate_discrete_gaussian_polynomial(N, STD_DEV, Q)
    bracket = add(vs, pi, Q)
    fst_multi = mul_simple(bracket, s1prime, modulo_polynomial, Q)
    snd_multi = mul_simple(us, vs, modulo_polynomial, Q)
    trd_multi = mul_simple(constant_two_polynomial, e1_triple_prime, modulo_polynomial, Q)
    added_fst_two = add(fst_multi, snd_multi, Q)
    kj = add(added_fst_two, trd_multi, Q)
    # SERVER: wj = Cha(kj)
    wj = [signal_function(x, Q) for x in kj]
    # SERVER: sigmaj = Mod_2(kj, wj)
    sigmaj = [robust_extractor(k, w, Q) for k, w in zip(kj, wj)]
    # SERVER: skj = SHA3-256(sigmaj)  # TODO for future: implement it, now it is not useless
    # CLIENT: u = XOF(H(pi||pj))  # TODO for future: compute it again
    uc = us
    # CLIENT: v = asv + 2ev  # TODO for future: compute it again using seeds
    vc = vs
    # CLIENT ki = (pj − v)(sv + s1) + uv + 2e1''
    e1_double_prime = generate_discrete_gaussian_polynomial(N, STD_DEV, Q)
    fst_bracket = sub(pj, vc, Q)
    snd_bracket = add(sv, s1, Q)
    fst_multi = mul_simple(fst_bracket, snd_bracket, modulo_polynomial, Q)
    snd_multi = mul_simple(uc, vc, modulo_polynomial, Q)
    trd_multi = mul_simple(constant_two_polynomial, e1_double_prime, modulo_polynomial, Q)
    added_fst_two = add(fst_multi, snd_multi, Q)
    ki = add(added_fst_two, trd_multi, Q)
    # CLIENT: sigmai = Mod_2(ki, wj)
    sigmai = [robust_extractor(k, w, Q) for k, w in zip(ki, wj)]
    # SERVER: ski = SHA3-256(sigmai)  # TODO for future: implement it, now it is useless
    compare_sigmas(sigmai, sigmaj)  # Created just for debugging reasons.
    compare_ki_kj(ki, kj, sigmai, sigmaj)  # Created just for debugging reasons.


def phase_2():  # TODO for future: implement it, now it is useless
    pass


def run_protocol():
    a = generate_random_polynomial(N, Q)  # public parameter  # TODO look how it is done in Kyber
    v, sv = phase_0(a)
    phase_1(a, v, sv)
    phase_2()


if __name__ == '__main__':
    run_protocol()
