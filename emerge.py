#!/usr/bin/env python3

import asyncio
import sys
from re import compile

RE_COLOR = compile(r'\x1b\[\d+(;\d+)?(;\d+)?m')
RE_CONFLICTED_PACKAGES = compile(
    r'^\s+[>=~<]*(?P<package1>[\w/-]+?)(:|\[|-\d+).* required by '
    r'\((?P<package2>[\w/-]+?)-\d+.*, installed\)$'
)

emerge_running = True
packages_reinstalled = set()

class EmergeOutputProtocol(asyncio.SubprocessProtocol):

    def __init__(self, queue):
        global emerge_running
        emerge_running = True
        self.queue = queue


    def pipe_data_received(self, fd, data):
        if fd == 1:
            sys.stdout.buffer.write(data)
        elif fd == 2:
            sys.stderr.buffer.write(data)

            for line in data.decode().split('\n'):
                self.queue.put_nowait(RE_COLOR.sub('', line))


    def process_exited(self):
        global emerge_running
        emerge_running = False

        
@asyncio.coroutine
def emerge_and_collect(args, loop, queue):
    subprocess = loop.subprocess_exec(lambda: EmergeOutputProtocol(queue),
            '/usr/bin/emerge', *args)

    transport, protocol = yield from subprocess

    while emerge_running or not queue.empty():
        try:
            line = queue.get_nowait()

            match = RE_CONFLICTED_PACKAGES.match(line)
            if match:
                #packages_reinstalled.add(match.group('package1'))
                packages_reinstalled.add(match.group('package2'))

        except asyncio.QueueEmpty:
            yield from asyncio.sleep(1)

    transport.close()
    return transport.get_returncode()


@asyncio.coroutine
def main(loop):
    count = 0
    ret = None
    queue = asyncio.Queue(loop=loop)

    yield from emerge_and_collect(['--color=y'] + sys.argv[1:], loop, queue)

    while count != len(packages_reinstalled):
        count = len(packages_reinstalled)

        ret = yield from emerge_and_collect(['--color=y', '--oneshot'] +\
                list(packages_reinstalled), loop, queue)

    if ret == 0:
        subprocess = yield from asyncio.create_subprocess_exec(
                '/usr/bin/emerge', *sys.argv[1:])

        yield from subprocess.wait()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
    loop.close()
