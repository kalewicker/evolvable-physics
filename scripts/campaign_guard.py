#!/usr/bin/env python3
"""One guarded child. Survives campaign-parent loss long enough to kill/reap its child."""
import json
import os
import resource
import selectors
import signal
import subprocess
import sys
import time
from pathlib import Path


def atomic_json(path, value):
    data = (json.dumps(value, sort_keys=True, indent=2)+'\n').encode()
    pending = path.with_name(path.name+'.pending')
    with pending.open('wb') as out:
        out.write(data); out.flush(); os.fsync(out.fileno())
    os.replace(pending, path)
    fd = os.open(path.parent, os.O_RDONLY)
    try: os.fsync(fd)
    finally: os.close(fd)


def guard(desc):
    if sys.platform not in ('darwin', 'linux'): raise RuntimeError('Unsupported RSS platform')
    started = time.monotonic(); stop = []; proc = None; usage = None
    cancelled = [False]
    signal.signal(signal.SIGTERM, lambda *_: cancelled.__setitem__(0, True))
    limits = desc['limits']; directory = Path(desc['directory'])
    result = {'schema': 'p01-stage-result-v1', 'status': 'starting', 'returncode': None,
              'stdout_bytes': 0, 'stderr_bytes': 0, 'stdout_observed_bytes': 0, 'stderr_observed_bytes': 0,
              'peak_sampled_rss_bytes': 0, 'rss_samples': 0}
    selector = selectors.DefaultSelector()
    streams = {}
    def kill_reap():
        nonlocal usage
        if proc is not None and proc.returncode is None:
            try: os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError: pass
            _, status, usage = os.wait4(proc.pid, 0)
            proc.returncode = os.waitstatus_to_exitcode(status)
    try:
        for name in ('stdout', 'stderr'):
            filename = desc.get('output_names', {}).get(name, name+'.bin')
            if Path(filename).name != filename: raise RuntimeError('Invalid output basename')
            streams[name] = (directory/filename).open('xb')
        if os.getppid() != desc['parent_pid']:
            stop.append('parent_lost')
        else:
            proc = subprocess.Popen(desc['command'], cwd=desc['cwd'], stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, start_new_session=True, bufsize=0)
            atomic_json(directory/'live.json', {'guard_pid': os.getpid(), 'child_pid': proc.pid})
            for name, stream in (('stdout', proc.stdout), ('stderr', proc.stderr)):
                os.set_blocking(stream.fileno(), False); selector.register(stream, selectors.EVENT_READ, name)
        next_sample = started
        while proc is not None and not stop:
            now = time.monotonic()
            if cancelled[0]: stop.append('parent_cancelled')
            elif os.getppid() != desc['parent_pid']: stop.append('parent_lost')
            elif now >= desc['campaign_deadline']: stop.append('campaign_wall_budget_exceeded')
            elif now-started >= limits['wall_seconds']: stop.append('wall_budget_exceeded')
            if stop: break
            if proc.returncode is None:
                pid, status, used = os.wait4(proc.pid, os.WNOHANG)
                if pid: proc.returncode = os.waitstatus_to_exitcode(status); usage = used
            if proc.returncode is None and now >= next_sample:
                try:
                    sample = subprocess.run(['ps', '-o', 'rss=', '-p', str(proc.pid)],
                                            capture_output=True, text=True, timeout=.5)
                    if sample.returncode not in (0, 1): raise RuntimeError('ps failed')
                    rss = int(sample.stdout.strip())*1024 if sample.stdout.strip() else 0
                    result['rss_samples'] += bool(rss)
                    result['peak_sampled_rss_bytes'] = max(result['peak_sampled_rss_bytes'], rss)
                    if rss > limits['rss_bytes']: stop.append('rss_budget_exceeded')
                except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
                    result['error'] = str(error); stop.append('rss_observation_failed')
                next_sample = time.monotonic()+limits['poll_seconds']
            if stop: break
            for key, _ in selector.select(limits['poll_seconds']):
                name = key.data; chunk = os.read(key.fileobj.fileno(), 65536)
                if not chunk:
                    selector.unregister(key.fileobj); key.fileobj.close(); continue
                result[name+'_observed_bytes'] += len(chunk)
                available = limits[name+'_bytes']-result[name+'_bytes']
                retained = chunk[:max(0, available)]
                streams[name].write(retained); result[name+'_bytes'] += len(retained)
                if len(retained) < len(chunk): stop.append(name+'_budget_exceeded'); break
            if proc.returncode is not None and not selector.get_map(): break
        kill_reap()
        result['status'] = stop[0] if stop else ('exited' if proc.returncode == 0 else 'child_failed')
    except BaseException as error:
        result.update(status='guard_error', error=repr(error)); kill_reap()
    finally:
        selector.close()
        if proc is not None:
            for stream in (proc.stdout, proc.stderr):
                if stream and not stream.closed: stream.close()
            result['returncode'] = proc.returncode
        for stream in streams.values(): stream.flush(); os.fsync(stream.fileno()); stream.close()
        result['wall_seconds'] = time.monotonic()-started
        if usage:
            result['child_cpu_seconds'] = usage.ru_utime+usage.ru_stime
            result['peak_rss_bytes'] = int(usage.ru_maxrss)*(1 if sys.platform == 'darwin' else 1024)
        result['guard_self_cpu_seconds'] = sum(resource.getrusage(resource.RUSAGE_SELF)[:2])
        result['guard_and_reaped_children_cpu_seconds'] = (sum(resource.getrusage(resource.RUSAGE_SELF)[:2])+
                                                         sum(resource.getrusage(resource.RUSAGE_CHILDREN)[:2]))
        atomic_json(directory/'result.json', result)
    return result


if __name__ == '__main__':
    guard(json.loads(Path(sys.argv[1]).read_text()))
