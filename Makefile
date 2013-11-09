# Really crude testing, as it (also) requires latencytop enabled :P
test:
	egrep '^./latencytop' README.md | bash -x >/dev/null
