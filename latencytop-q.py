#!/usr/bin/python
# Author: JuanJo Ciarlante <jjo@canonical.com>
# Copyright 2013, Canonical Ltd.
# License : GPLv3
#
# pylint: disable=C0103,W0142
"""
#
# Non UI latencytop stats reporter
#
# Usage examples ->
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
"""

import subprocess
import sys
import argparse
import os
import re
import signal

FIELD_TO_NUM = {
    'cnt': 0,
    'sum': 1,
    'max': 2,
    'avg': 3,
}

GROUPBY = ['top', 'low', 'sys']


def gen_pids(procname, args):
    "Return a generator for pids matched by pgrep (also LWPs if args.threads"
    if args.threads:
        cmd = "pgrep -f '{}' | xargs ps -olwp= -Lp".format(procname)
    else:
        cmd = "pgrep -f '{}'".format(procname)
    pipe = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                            close_fds=True)
    while pipe.returncode is None:
        (stdout, stderr) = pipe.communicate()
        if stderr:
            raise Exception("stderr from pgrep/ps: " + stderr)
        for pid in stdout.splitlines():
            if int(pid) == os.getpid() or int(pid) == os.getppid():
                continue
            yield pid.strip()


def gen_proc_filenames(pids):
    "Transform pids to /proc/pid entries"
    for pid in pids:
        yield "/proc/{}".format(pid)


def gen_read_file(filenames):
    "Generate latencytop lines from each /proc filename"
    for filename in filenames:
        lat_file = "{}/latency".format(filename)
        comm_file = "{}/comm".format(filename)
        if not os.path.exists(filename):
            continue
        cmd = open(comm_file).read().rstrip()
        for line in open(lat_file).readlines():
            if not line[0].isdigit():
                continue
            yield (cmd, line.rstrip())


def gen_read_global():
    "Generate latencytop lines from global latency_stats"
    for line in open('/proc/latency_stats').readlines():
        if not line[0].isdigit():
            continue
        yield ("GLOBAL", line.rstrip())


def merge_data(data_dict, key, values):
    "Merge/aggregate each new latencytop line"
    # Below indexes must be in sync w/FIELD_TO_NUM values
    curr_val = data_dict.get(key, [0] * len(FIELD_TO_NUM.keys()))
    # cnt: accumulate
    curr_val[0] += int(values[0])
    # sum: accumulate
    curr_val[1] += int(values[1])
    # max: compare and set new max
    curr_val[2] = max(curr_val[2], int(values[2]))
    # avg: calculate avg as sum/cnt
    curr_val[3] = curr_val[1] / curr_val[0]
    # store back to dict
    data_dict[key] = curr_val


def format_bt(cmd, backtrace, args):
    "Filter backtrace line by: heuristics (cleanup), --groupby"
    backtrace = re.sub(r'__refrigerator ', '', backtrace)
    backtrace = re.sub(r' system_call_fastpath', '', backtrace)
    if args.only_sys or args.groupby == 'sys':
        # Try leaving only e.g. SyS_write
        backtrace = re.sub(r'.* ([Ss]y[Ss]_[a-z_]+) *', r'\g<1>', backtrace)
        # else leave only the top from backtrace
        backtrace = backtrace.split(" ")[-1]
    elif args.groupby == 'top':
        backtrace = backtrace.split(" ")[-1]
    elif args.groupby == 'low':
        backtrace = backtrace.split(" ")[0]
    if args.show_cmd:
        return '{}:\t{}'.format(cmd, backtrace)
    else:
        return backtrace


def latency_show(procname, args):
    "Main loop to print stats"
    data = {}
    orderby = FIELD_TO_NUM[args.orderby]
    if procname:
        cmd_lines = gen_read_file(gen_proc_filenames(gen_pids(procname, args)))
    else:
        cmd_lines = gen_read_global()

    for (cmd, line) in cmd_lines:
        (ncalls, acc, top, backtrace) = line.split(" ", 3)
        merge_data(data, format_bt(cmd, backtrace, args), (ncalls, acc, top))

    if not args.no_headers:
        print "{0:>6s}\t{1:>8s}\t{2:>8s}\t{3:>8s}\t{key:8s}".format(
            *("cnt", "sum", "max", "avg"), key="key")
    output = []
    for btrace, metrics in sorted(data.items(), key=lambda t: t[1][orderby]):
        output.append("{0:6d}\t{1:8d}\t{2:8d}\t{3:8d}\t{key}".format(
            *metrics, key=btrace))
    print "\n".join(output[-args.limit:])


def latencytop_enabled():
    "True if latencytop statictics collection is enabled"
    latencytop_val = int(open('/proc/sys/kernel/latencytop').read())
    return latencytop_val != 0


def main():
    "The main()"
    par = argparse.ArgumentParser(description='Linux latencytop simple stats')
    par.add_argument('procname', type=str, nargs='*',
                     help=('process names regex (man pgrep), else use\n'
                           '/proc/latency_stats (global)'))
    par.add_argument('-o', '--orderby', choices=FIELD_TO_NUM.keys(),
                     default='max', help='metric to orderby')
    par.add_argument('-c', '--show-cmd', action='store_true',
                     default=False,
                     help='use also process name with backtrace')
    par.add_argument('-n', '--no-headers', action='store_true',
                     default=False, help='omit headers')
    par.add_argument('-s', '--only-sys', action='store_true',
                     default=False,
                     help='use only sys_call from backtrace (same as "-g sys"')
    par.add_argument('-g', '--groupby', choices=GROUPBY, default=None,
                     help='group backtrace by different hi/low-level symbols')
    par.add_argument('-l', '--limit', type=int, action='store',
                     default=0, help='limit output to last LIMIT lines')
    par.add_argument('-t', '--threads', action='store_true',
                     default=False, help='also expand threads (LWPs)')
    args = par.parse_args()
    if args.only_sys and args.groupby:
        raise argparse.ArgumentTypeError(
            'Conflicting options: -s is a shortcut for "-g sys"')
    if len(args.procname) > 0:
        latency_show(args.procname[0], args)
    else:
        latency_show(None, args)

if __name__ == '__main__':
    if not latencytop_enabled():
        print >> sys.stderr, ('ERROR: latencytop collection not enabled, do:\n'
                              'sudo sysctl -w kernel.latencytop=1')
        sys.exit(1)
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    try:
        main()
    except KeyboardInterrupt:
        pass
