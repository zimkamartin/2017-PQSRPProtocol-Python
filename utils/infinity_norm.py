# Compute symmetric modulo as defined in https://youtu.be/h5pfTIE6slU?si=-EeOGTV0QD5QzbpY&t=543
def symmetric_mod(r, q):
    r %= q  # make sure that r is in Z_q
    if q % 2 == 0:  # q is even
        return r if r <= q / 2 else r - q
    return r if r <= (q - 1) / 2 else r - q


# Compute infinity norm of an integer as defined in https://youtu.be/h5pfTIE6slU?si=nK9YVFvjD64nnb7Q&t=759
def infinity_norm(r, q):
    return abs(symmetric_mod(r % q, q))  # also make sure that r is in Z_q


# Compute infinity norm of an iterable object (usually representing a polynomial)
# as defined in https://youtu.be/h5pfTIE6slU?si=YH3o7ernOaRmk7F_&t=819
def infinity_norm_iterable(iterable, q):
    return max(infinity_norm(x, q) for x in iterable)
