# Really crude testing, as it (also) requires latencytop enabled :P
test:
	$(MAKE) run >/dev/null
run:
	egrep '^./latencytop' README.md | bash -ve
