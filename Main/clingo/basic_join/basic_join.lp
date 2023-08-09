j1(X, Y, Z) :- sourceA(X, Z, Y), sourceB(X, Y, T).
j2(X, Y, Z) :- sourceA(Z, Y, X), sourceC(X, Y, T).
j3(X, Y, W) :- sourceA(T, Y, X), sourceB(T, Y, X), sourceC(X, Y, W).