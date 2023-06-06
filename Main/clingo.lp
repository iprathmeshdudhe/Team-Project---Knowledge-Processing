father(bob, david) .
mother(bob, anna) .
father(anna, richard) .
mother(richard, lucy) .
father(alice, bob) .
mother(alice, brenda) .
father(josh, david) .
mother(josh, paula) .
parent(X, Y) :- father(X, Y).
parent(X, Y) :- mother(X, Y).
ancestor(X, Y) :- parent(X, Y).
ancestor(X, Y) :- parent(X, Z), ancestor(Z, Y).
result(Y) :- ancestor(alice, Y).
#show result/1.