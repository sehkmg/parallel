# Run parallel experiments with AsyncIO
Scheduler for deploying lots of python(usually machine learning) experiments.

## Environment
- Python 3

## How to use
1. Write description of deployment. (Most of the exceptions are handled.)
In cmd2deploy.txt:
<pre><code>server:0
gpu:0
python -c 'print("Start: 0"); import torch, time; torch.ones(1).cuda(); time.sleep(5)'
{
    python -c 'print("Start: 1"); import torch, time; torch.ones(1).cuda(); time.sleep(5)'
    python -c 'print("Start: 2"); import torch, time; torch.ones(1).cuda(); time.sleep(5)'
    python -c 'print("Start: 3"); import torch, time; torch.ones(1).cuda(); time.sleep(5)'
}

gpu:1
python -c 'print("Start: 4"); import torch, time; torch.ones(1).cuda(); time.sleep(5)'
python -c 'print("Start: 5"); import torch, time; torch.ones(1).cuda(); time.sleep(5)'

gpu:2
python -c 'print("Start: 6"); import torch, time; torch.ones(1).cuda(); time.sleep(5)'

gpu:3
python -c 'print("Start: 7"); import torch, time; torch.ones(1).cuda(); time.sleep(5)'
python -c 'print("Start: 8"); import torch, time; torch.ones(1).cuda(); time.sleep(5)'

server:1
gpu:0
python -c 'print("Start: 9"); import torch, time; torch.ones(1).cuda(); time.sleep(5)'

gpu:1
python -c 'print("Start: 10"); import torch, time; torch.ones(1).cuda(); time.sleep(5)'
{
    python -c 'print("Start: 11"); import torch, time; torch.ones(1).cuda(); time.sleep(5)'
    python -c 'print("Start: 12"); import torch, time; torch.ones(1).cuda(); time.sleep(5)'
    python -c 'print("Start: 13"); import torch, time; torch.ones(1).cuda(); time.sleep(5)'
}
python -c 'print("Start: 14"); import torch, time; torch.ones(1).cuda(); time.sleep(5)'</code></pre>

2-1. Run every experiments.
<pre><code>python3 parallel.py --server_num=0</code></pre>

2-2. Run experiments sequentially.
<pre><code>python3 parallel.py --server_num=0 --seq</code></pre>
