combined(X, Y, Z) :- source(X, Y, Z).
constant(X) :- combined(X, b, c).
constant(X) :- combined(X, y, Z).