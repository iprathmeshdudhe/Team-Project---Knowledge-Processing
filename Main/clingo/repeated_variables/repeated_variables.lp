repeatBody(R, S) :- sourceA(X, X, R), sourceB(S, Y, Y).
repeatHead(X, Y, X, Y, Z, Z, X) :- sourceA(X, Z, Y), sourceB(X, Y, T).
repeatAll(X, X, X, X) :- sourceC(X, X, X).
repeatAlternative(R, S) :- sourceA(R, X, X), sourceB(S, Y, Y).