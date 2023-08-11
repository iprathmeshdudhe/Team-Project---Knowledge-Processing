samePerson(X, X) :- person(X).
parent(X, Y) :- mother(X, Y).
parent(X, Y) :- father(X, Y).
sameMother(X, Y) :- mother(X, Z), mother(Y, Z), samePerson(X, Y).
sameFather(X, Y) :- father(X, Z), father(Y, Z), samePerson(X, Y).
siblings(X, Y) :- sameMother(X, Y), sameFather(X, Y).
halfSiblings(X, Y) :- sameMother(X, Y), sameFather(X, Y).
halfSiblings(X, Y) :- sameMother(X, Y), sameFather(X, Y).
hasChildDoctor(X) :- parent(Y, X), occupation(Y, doctor).