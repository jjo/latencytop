latencytop
==========
Non UI latencytop stats reporter

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
./latencytop-q.py -c -l10 -s -o avg 'apache2|squid'

# Show top avg latency *with* process name
./latencytop-q.py -c -l20 .

# Ditto, sort by avg latency
./latencytop-q.py -c -o avg -l20 .

# Ditto, group by low level calls
./latencytop-q.py -c -o avg -l20 -g low .

# Delta stats:
./latencytop-q.py -f ~/tmp/lat.last -cs . # 1st: will create if not found
./latencytop-q.py -f ~/tmp/lat.last -cs . # 2nd: will use + update
```
