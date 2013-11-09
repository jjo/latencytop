latencytop
==========

linux latencytop tools

# Usage
```shell
# Show system-wide latencytop stats:
./latencytop-q.py

# Ditto, top10:
./latencytop-q.py -l10

# Ditto, collapse backtraces to sys_calls:
./latencytop-q.py -l10 -s

# Ditto, for apache2 processes:
./latencytop-q.py -l10 -s apache2

# Ditto, for apache2 and squid processes:
./latencytop-q.py -l10 -s 'apache2|squid'

# Ditto, also discriminate by cmdline:
./latencytop-q.py -c -l10 -s 'apache2|squid'

# Ditto, order by avg time (instead of all time max):
./latencytop-q.py -c -l10 -s -o max 'apache2|squid'
```
