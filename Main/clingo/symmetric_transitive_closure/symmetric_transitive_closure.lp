connected(X, Y) :- city(X), city(Y), conn(X, Y).
conn(X, Y) :- conn(Y, X).
connected(X, Y) :- city(X), city(Xy), city(Y), connected(X, Xy), conn(Xy, Y).