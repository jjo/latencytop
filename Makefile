# Really crude testing, as it (also) requires latencytop enabled :P
SRC=latencytop-q.py
test:
	$(MAKE) run >/dev/null
run:
	egrep '^./latencytop' README.md | bash -ve
lint:
	pep8 $(SRC)
	pylint $(SRC)
