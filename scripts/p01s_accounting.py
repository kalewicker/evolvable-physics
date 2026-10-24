"""Owned-file fixture ledger. Cooperative limits; no campaign or processes."""
import hashlib
import json
import os
import stat
from pathlib import Path


def require(ok, message):
    if not ok:
        raise ValueError(message)


class Ledger:
    def __init__(self, root, cap=134217728, reserve=1048576):
        self.root = Path(root).absolute()
        os.mkdir(self.root)
        self.rows = [dict(slot=i, proposal=6000+i//4, initial=i % 4, status='unstarted') for i in range(128)]
        self.cap, self.reserve = cap, reserve
        self.files, self.stages, self.events = {}, {}, []
        self.total = 0
        self.invalid = False
        self.counts = dict(input_full_scans=0, output_full_scans=0, stage_reconciliations=0,
                           discovered_entries=0, stat_calls=0, hash_read_bytes=0,
                           write_bytes=0, ledger_updates=0, budget_polls=0)
        require(not self.scan(), 'initial root not empty')

    def path(self, name):
        p = Path(name)
        require(not p.is_absolute() and bool(p.parts) and '..' not in p.parts, 'unsafe path')
        here = self.root
        # Include root: substituting a symlink for the owned directory is invalid.
        for part in (None, *p.parts):
            if part is not None:
                here = here/part
            self.counts['stat_calls'] += 1
            try:
                mode = os.lstat(here).st_mode
            except FileNotFoundError:
                continue
            require(not stat.S_ISLNK(mode), 'symlink rejected')
        return self.root/p

    def exists(self, p):
        self.counts['stat_calls'] += 1
        try:
            os.lstat(p)
            return True
        except FileNotFoundError:
            return False

    def read(self, p):
        data = p.read_bytes()
        self.counts['hash_read_bytes'] += len(data)
        return data

    def scan(self, directory=None):
        self.counts['output_full_scans' if directory is None else 'stage_reconciliations'] += 1
        found = {}
        def visit(folder):
            with os.scandir(folder) as entries:
                names = sorted(x.name for x in entries)
            self.counts['discovered_entries'] += len(names)
            for name in names:
                p = folder/name
                self.counts['stat_calls'] += 1
                info = os.lstat(p)
                mode = info.st_mode
                require(not stat.S_ISLNK(mode), 'scan symlink')
                if stat.S_ISDIR(mode):
                    require(directory is None, 'nested stage directory')
                    visit(p)
                else:
                    require(stat.S_ISREG(mode), 'nonregular output')
                    if directory is not None:
                        require(len(found) < 16 and sum(x['size'] for x in found.values())+info.st_size <= self.stages[directory]['allowance'], 'bounded stage scan')
                    data = self.read(p)
                    found[str(p.relative_to(self.root))] = dict(size=len(data), sha256=hashlib.sha256(data).hexdigest())
        visit(self.root if directory is None else self.root/directory)
        return found

    def check_known(self, name):
        p = self.path(name)
        try:
            if name in self.files:
                data = self.read(p)
                require(self.files[name] == dict(size=len(data), sha256=hashlib.sha256(data).hexdigest()), 'external mutation')
            else:
                require(not self.exists(p), 'unlisted file')
        except (ValueError, OSError):
            self.invalid = True
            raise
        return p

    def update(self, name, data, operation):
        old = self.files.get(name, {}).get('size', 0)
        self.files[name] = dict(size=len(data), sha256=hashlib.sha256(data).hexdigest())
        self.total += len(data)-old
        self.counts['ledger_updates'] += 1
        self.events.append(dict(op=operation, name=name, old=old, new=len(data), total=self.total))

    @property
    def reserved(self):
        return sum(s['allowance'] for s in self.stages.values() if not s['done'])

    def budget(self, wall=0, cpu=0, wall_cap=120, cpu_cap=600, seconds_reserve=5):
        self.counts['budget_polls'] += 1
        require(not self.invalid, 'invalid ledger')
        require(wall < wall_cap-seconds_reserve, 'wall reserve')
        require(cpu < cpu_cap-seconds_reserve, 'cpu reserve')
        require(self.total+self.reserved < self.cap-self.reserve, 'byte reserve')

    def write(self, name, data, append=False, fail_after=None, terminal=False):
        require(isinstance(data, bytes), 'bytes required')
        require(not self.invalid or terminal, 'invalid ledger')
        p = self.check_known(name)
        old = self.read(p) if name in self.files else b''
        prefix = old if append else b''
        limit = self.cap-(0 if terminal else self.reserve)
        require(self.total-len(old)+len(prefix)+len(data)+self.reserved < limit, 'write reserve')
        parent = self.root
        for part in Path(name).parts[:-1]:
            parent = parent/part
            try:
                os.mkdir(parent)
            except FileExistsError:
                pass
        fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
        actual = b''
        target = prefix+data
        try:
            while len(actual) < len(target):
                if fail_after is not None and len(actual) >= fail_after:
                    raise OSError('injected partial write')
                end = len(target) if fail_after is None else min(len(target), fail_after)
                n = os.write(fd, target[len(actual):end])
                require(n > 0, 'zero write')
                actual += target[len(actual):len(actual)+n]
                self.counts['write_bytes'] += n
        finally:
            os.close(fd)
            self.update(name, actual, 'write')
        return len(actual)

    def copy(self, source, name, fail_after=None):
        self.write(name, self.read(Path(source)), fail_after=fail_after)

    def register(self, name):
        require(name in self.files, 'unknown registration')
        self.check_known(name)
        return self.files[name]

    def rename(self, source, target):
        require(source != target, 'same rename path')
        src, dst = self.check_known(source), self.check_known(target)
        require(source in self.files, 'missing source')
        os.replace(src, dst)
        old = self.files.pop(source)
        replaced = self.files.pop(target, {}).get('size', 0)
        self.files[target] = old
        self.total -= replaced
        self.counts['ledger_updates'] += 1
        self.events.append(dict(op='rename', source=source, target=target, removed=replaced, total=self.total))

    def delete(self, name):
        p = self.check_known(name)
        require(name in self.files, 'missing delete')
        p.unlink()
        old = self.files.pop(name)['size']
        self.total -= old
        self.counts['ledger_updates'] += 1
        self.events.append(dict(op='delete', name=name, removed=old, total=self.total))

    def declare_stage(self, name, names, allowance=8388608):
        require(name not in self.stages and 0 < allowance <= 8388608, 'stage declaration')
        require(len(names) <= 16 and len(set(names)) == len(names), 'stage files')
        require(all(Path(n).name == n and n not in ('', '.', '..') for n in names), 'stage paths')
        p = self.path(name)
        require(not self.exists(p) and self.total+self.reserved+allowance < self.cap-self.reserve, 'stage reserve')
        p.mkdir()
        self.stages[name] = dict(names=names, allowance=allowance, done=False)

    def reconcile_stage(self, name):
        stage = self.stages[name]
        require(not stage['done'] and not stage.get('failed'), 'stage already reconciled')
        stage['done'] = True
        try:
            found = self.scan(name)
            require(set(found) <= {name+'/'+n for n in stage['names']} and len(found) <= 16, 'unexpected stage files')
            require(sum(x['size'] for x in found.values()) <= stage['allowance'], 'stage size')
            for n, value in found.items():
                require(n not in self.files, 'stage ownership overlap')
                self.files[n] = value
                self.total += value['size']
                self.counts['ledger_updates'] += 1
                self.events.append(dict(op='stage', name=n, old=0, new=value['size'], total=self.total))
        except Exception:
            self.invalid = True
            # Keep the pessimistic reservation after failed reconciliation.
            stage['done'] = False
            stage['failed'] = True
            raise

    def reconcile(self):
        require(self.counts['output_full_scans'] == 1, 'full scan budget')
        try:
            require(self.scan() == self.files, 'inventory mismatch')
            require(sum(x['size'] for x in self.files.values()) == self.total, 'total mismatch')
        except Exception:
            self.invalid = True
            raise
        return True


def terminal(ledger, first_error, write_failure=False):
    rows = [dict(row) for row in ledger.rows]
    rows[0]['status'] = 'failed'
    result = dict(first_error=first_error, closeout_errors=[], rows=rows,
                  reconciliation='incomplete', inventory_scope='maintained_ledger', terminal_receipt='written')
    try:
        if write_failure:
            raise OSError('injected terminal I/O error')
        ledger.write('terminal.json', (json.dumps(result, sort_keys=True)+'\n').encode(), terminal=True)
    except Exception as error:
        result['closeout_errors'].append(repr(error))
        result['terminal_receipt'] = 'missing'
    return result
