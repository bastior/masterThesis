import os
import sys
from subprocess import run

directory = sys.argv[1]

files = [directory+str(files) for files in os.listdir(directory) if os.path.isdir(directory+str(files))]

bump = 0

for i in files:
    pyth = "python3"
    script = "testOnDirectory.py"
    params = ["--var=A", "--val=A", "--backtrack=C", "--restart=S", "--bump=" + str(bump)]

    run(([pyth, script, i]) + params)

bump += 1


for i in files:
    pyth = "python3"
    script = "testOnDirectory.py"
    params = ["--var=N", "--val=T", "--backtrack=C", "--restart=F", "--bump=" + str(bump)]

    run(([pyth, script, i]) + params)

bump += 1
for i in files:
    pyth = "python3"
    script = "testOnDirectory.py"
    params = ["--var=A", "--val=A", "--backtrack=P", "--restart=M", "--bump=" + str(bump)]

    run(([pyth, script, i]) + params)


bump += 1

for i in files:
    pyth = "python3"
    script = "testOnDirectory.py"
    params = ["--var=N", "--val=T", "--backtrack=P", "--restart=F", "--bump=" + str(bump)]

    run(([pyth, script, i]) + params)

bump += 1
for i in files:
    pyth = "python3"
    script = "testOnDirectory.py"
    params = ["--var=H", "--val=F", "--backtrack=C", "--restart=F", "--bump=" + str(bump)]

    run(([pyth, script, i]) + params)

