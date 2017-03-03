import os
import sys
import time
from subprocess import PIPE, run

# import parser from original file. It is ugly but works.
sys.path.insert(0, '../Code/')
# TIMEOUT for a solver in seconds
TO = 60 * 2 # 2 minutes
from aghSolver import parser, run_solver


def write_to_timestat_file(string, basename):
    stat_file = open(basename + "/TimeStat.result", 'a')
    stat_file.write(string)
    stat_file.close()


def find_cnf_files(directory):
    if not os.path.isdir(directory):
        return False
    files = [str(cnf_file) for cnf_file in os.listdir(directory) if cnf_file.endswith(".dimacs") or cnf_file.endswith(".cnf")]
    return files


# consider filename as dir name with .cnf and .dimacs files
prs = parser()
prs.add_argument('--bump')
args = prs.parse_args()
cnf_files = find_cnf_files(args.file)

# basename is the name of folder under proceeding
base_name = os.path.basename(os.path.normpath(args.file))
program_argvs = [x for x in sys.argv if x.startswith("--") and not x.startswith("--bump")]

whole_loop_time = time.time()

if args.bump != None:
    result_dir = "./Results" + args.bump + "/" + base_name
else:
    result_dir = "./Results/" + base_name

if not os.path.exists(result_dir):
    os.makedirs(result_dir)

times_timed_out = 0
for file in cnf_files:
    start_time = time.time()
    file = os.path.join(args.file, file)
    write_to_timestat_file("RUNNING SOLVER ON PATH:\n" + file, result_dir)
    filename = os.path.basename(file)
    out_file = open(result_dir + "/" + filename, 'w')
    try:
        result = run('ulimit -v 4000000; ' + str(sys.executable) + ' ../Code/aghSolver.py ' + file + " " + " ".join(program_argvs),
                         stdout=PIPE,
                         stderr=PIPE,
                         universal_newlines=True,
                         timeout=TO,
                         shell=True)
    except:
        out_file.write("PROBABLY TIMEOUT APPEARED")
        write_to_timestat_file("\nTimed out at: " + file + "\n\n", result_dir)
        times_timed_out += 1
    else:
        # put results to correct file
        out_file.write(result.stdout)
        out_file.write(result.stderr)
        write_to_timestat_file("\nelapsed time: " + str(time.time()-start_time) + " seconds\n\n", result_dir)
    out_file.close()

write_to_timestat_file("Overall elapsed time for whole dir: " + str(time.time() - whole_loop_time) + " seconds", result_dir)
if times_timed_out:
    write_to_timestat_file("\n\nTimed out: " + str(times_timed_out) + " time(s)", result_dir)
