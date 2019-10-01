import os
import re
import time
import argparse
import concurrent
import asyncio

def get_line(cmd_file):
    p_server = re.compile('^server:\d+')
    p_gpu = re.compile('^gpu:\d(,\d)*')
    p_python = re.compile('^python')
    p_open = re.compile('^{$')
    p_close = re.compile('^}$')

    while True:
        line = cmd_file.readline()
        if not line: return (None, 'eof')

        line = line.strip()

        if p_server.match(line):
            line = p_server.match(line).group()
            return (line, 'server')

        elif p_gpu.match(line):
            line = p_gpu.match(line).group()
            return (line, 'gpu')

        elif p_python.match(line):
            return (line, 'python')

        elif p_open.match(line):
            return (line, 'open')
        
        elif p_close.match(line):
            return (line, 'close')

def get_gpu_num_wrapper(max_gpu_num):
    def get_gpu_num(line):
        gpu_list = list(map(int, line.split(':')[1].split(',')))
        for gpu_num in gpu_list:
            assert gpu_num < max_gpu_num, 'gpu:{} is not available.'.format(gpu_num)

        gpu_num = ','.join(list(map(str, gpu_list)))

        return gpu_num
    return get_gpu_num

def get_cmd_list(args):
    cmd_file = open(args.file, 'r')
    gpu_str = 'CUDA_VISIBLE_DEVICES={} '
    get_gpu_num = get_gpu_num_wrapper(args.max_gpu_num)

    cmd_list = []

    # read until 'server:{args.server_num}'
    while True:
        line, line_type = get_line(cmd_file)
        if line_type == 'eof':
            cmd_file.close()
            return cmd_list

        if line_type == 'server':
            server_num = int(line.split(':')[1])

            if server_num == args.server_num:
                break

    # next string of 'server:{args.server_num}'
    # must be 'gpu:{gpu_number}'
    line, line_type = get_line(cmd_file)
    if not line_type == 'gpu':
        cmd_file.close()
        return cmd_list

    # set current gpu
    cur_gpu_num = get_gpu_num(line)

    # parse description
    is_open = False
    while True:
        line, line_type = get_line(cmd_file)
        if line_type == 'eof' or line_type == 'server':
            assert not is_open, "Syntax Error."
            cmd_file.close()
            return cmd_list

        if line_type == 'open':
            assert not is_open, "Syntax Error."
            is_open = True
            cmd_queue = []

        elif line_type == 'gpu':
            assert not is_open, "Syntax Error."
            cur_gpu_num = get_gpu_num(line)

        elif line_type == 'python':
            if is_open:
                cmd_queue.append(gpu_str.format(cur_gpu_num) + line)
            else:
                cmd_list.append(gpu_str.format(cur_gpu_num) + line)

        elif line_type == 'close':
            assert is_open, "Syntax Error."
            is_open = False
            cmd_list.append(cmd_queue)

def run_parallel(commands, sequential):
    assert commands and type(commands) == list
    p_int = re.compile('\d+$')
    p_gpu = re.compile('\d(,\d)*$')

    def func(command):
        if isinstance(command, list):
            for cmd in command:
                os.system(cmd)
        else:
            os.system(command)

    async def main():
        with concurrent.futures.ThreadPoolExecutor(
                max_workers=len(commands)) as executor:
            loop = asyncio.get_event_loop()

            futures = []
            is_exit = False
            for idx in range(len(commands)):

                if sequential:
                    for i, cmd in enumerate(commands):
                        print('{}: {}'.format(i, cmd))

                    while True:
                        try:
                            info = input('Enter command_index/gpu_num (e.g. 3/0,3): ')

                            if len(info.split('/')) < 2:
                                continue

                            cmd_idx = info.split('/')[0].strip()
                            gpu_num = info.split('/')[1].strip()

                            if p_int.match(cmd_idx) and p_gpu.match(gpu_num):
                                cmd_idx = int(cmd_idx)
                                gpu_str = 'CUDA_VISIBLE_DEVICES={} '.format(gpu_num)
                                break
                        except KeyboardInterrupt:
                            is_exit = True
                            print('')
                            break

                    if is_exit:
                        break

                    futures.append(loop.run_in_executor(executor, func, gpu_str+commands[cmd_idx]))
                    commands[cmd_idx] = '(Deployed) ' + commands[cmd_idx]

                    enter = input('Press Enter to Continue...\n')

                else:
                    time.sleep(0.5*idx)
                    futures.append(loop.run_in_executor(executor, func, commands[idx]))

            for response in await asyncio.gather(*futures):
                pass

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--file',
        type=str,
        default='cmd2deploy.txt')
    parser.add_argument(
        '--server_num',
        type=int,
        default=0)
    parser.add_argument(
        '--max_gpu_num',
        type=int,
        default=4)
    parser.add_argument(
        '--sequential', '--seq',
        action='store_true')
    args = parser.parse_args()

    cmd_list = get_cmd_list(args)

    if len(cmd_list) > 0:
        if args.sequential:
            merge_list = []
            for cmd in cmd_list:
                if isinstance(cmd, list):
                    for c in cmd:
                        merge_list.append(' '.join(c.split(' ')[1:]))
                else:
                    merge_list.append(' '.join(cmd.split(' ')[1:]))

            cmd_list = merge_list

        else:
            for cmd in cmd_list:
                if isinstance(cmd, list):
                    print('{')
                    for c in cmd:
                        print('\t{}'.format(c))
                    print('}')
                else:
                    print(cmd)

        run_parallel(cmd_list, args.sequential)
    else:
        print('Command list is empty.')
