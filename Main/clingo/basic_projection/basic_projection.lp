a(X, Z) :- data(X, Y, Z).
b(Y, X) :- a(X, Y).
c(Y) :- b(Variablethatisnotneeded, Y).
d(Y, Z) :- data(X, Y, Z).
e(F, E) :- d(E, F).