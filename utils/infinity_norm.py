# Compute symmetric modulo as defined in https://youtu.be/h5pfTIE6slU?si=-EeOGTV0QD5QzbpY&t=543
def symmetric_mod(r, q):
    r %= q  # make sure that r is in Z_q
    if q % 2 == 0:  # q is even
        return r if r <= q / 2 else r - q
    return r if r <= (q - 1) / 2 else r - q
