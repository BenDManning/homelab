"""Offsite reachability observer: stdlib probes and a durable SQLite outbox."""
import argparse
import base64
import concurrent.futures
import fcntl
import http.client
import ipaddress
import json
import math
import os
import socket
import sqlite3
import ssl
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit


class Engine:
    def __init__(self, path, failures=3, recoveries=2, reminder=1800,
                 max_gap=150, label='offsite'):
        self.db = sqlite3.connect(path)
        self.db.execute('PRAGMA max_page_count=16384')
        self.db.execute('PRAGMA synchronous=FULL')
        self.db.execute('CREATE TABLE IF NOT EXISTS state '
                        '(id INTEGER PRIMARY KEY CHECK(id=1), data TEXT NOT NULL)')
        self.db.execute('CREATE TABLE IF NOT EXISTS outbox '
                        '(seq INTEGER PRIMARY KEY, data TEXT NOT NULL, receipt TEXT)')
        self.failures = failures
        self.recoveries = recoveries
        self.reminder = reminder
        self.max_gap = max_gap
        self.label = label
        initial = {'active': 'HEALTHY', 'candidate': 'HEALTHY', 'count': 0,
                   'last_sample': None, 'last_event': 0}
        with self.db:
            self.db.execute('INSERT OR IGNORE INTO state VALUES (1,?)',
                            (json.dumps(initial),))

    def close(self):
        self.db.close()

    def pending(self):
        return [json.loads(row[0]) for row in self.db.execute(
            'SELECT data FROM outbox WHERE receipt IS NULL ORDER BY seq')]

    def observe(self, condition, now):
        with self.db:
            state = json.loads(self.db.execute(
                'SELECT data FROM state WHERE id=1').fetchone()[0])
            if (state['last_sample'] is not None and
                    not 0 <= now - state['last_sample'] <= self.max_gap):
                state['count'] = 0
            if condition != state['candidate']:
                state['candidate'], state['count'] = condition, 0
            state['count'] += 1
            state['last_sample'] = now
            threshold = self.recoveries if condition == 'HEALTHY' else self.failures
            if condition != state['active'] and state['count'] >= threshold:
                event = {
                    'event_id': str(uuid.uuid4()),
                    'kind': 'RECOVERY' if condition == 'HEALTHY' else 'FIRING',
                    'condition': condition, 'previous': state['active'],
                    'observed_at': now, 'label': self.label,
                }
                self.db.execute('INSERT INTO outbox(data) VALUES (?)',
                                (json.dumps(event),))
                state['active'], state['last_event'] = condition, now
            elif (condition == state['active'] and condition != 'HEALTHY' and
                  now - state['last_event'] >= self.reminder and not self.pending()):
                event = {
                    'event_id': str(uuid.uuid4()), 'kind': 'REMINDER',
                    'condition': condition, 'previous': condition,
                    'observed_at': now, 'label': self.label,
                }
                self.db.execute('INSERT INTO outbox(data) VALUES (?)',
                                (json.dumps(event),))
                state['last_event'] = now
            self.db.execute('UPDATE state SET data=? WHERE id=1',
                            (json.dumps(state),))

    def deliver(self, sender):
        # At-least-once: acceptance before the local commit can be duplicated.
        rows = self.db.execute('SELECT seq,data FROM outbox WHERE receipt IS NULL '
                               'ORDER BY seq LIMIT 20').fetchall()
        for seq, data in rows:
            try:
                receipt = sender(json.loads(data))
                if not isinstance(receipt, str) or not receipt:
                    raise ValueError('Missing receipt ID')
            except Exception as exc:
                print(json.dumps({'delivery': 'retry-next-run',
                                  'error_type': type(exc).__name__}), flush=True)
                return False
            with self.db:
                self.db.execute('UPDATE outbox SET receipt=? WHERE seq=?', (receipt, seq))
                self.db.execute('DELETE FROM outbox WHERE receipt IS NOT NULL AND '
                                'seq NOT IN (SELECT seq FROM outbox '
                                'ORDER BY seq DESC LIMIT 2000)')
            print(json.dumps({'delivery': 'accepted', 'receipt': receipt,
                              'event_id': json.loads(data)['event_id']}), flush=True)
        return True


def classify(probes):
    if probes['management_http']:
        return 'HEALTHY'
    if probes['management_ssh']:
        return 'MONITORING_ONLY_LOSS'
    if probes['core'] or probes['network']:
        return 'MANAGEMENT_HOST_LOSS'
    if not (probes['public1'] or probes['public2']):
        return 'OFFSITE_CONNECTIVITY_LOSS'
    return 'HOME_MULTI_TARGET_LOSS'


def probe(target, timeout):
    ipaddress.ip_address(target['ip'])  # Probe connections never resolve home DNS.
    conn = None
    try:
        if target['kind'] == 'tcp':
            with socket.create_connection((target['ip'], target['port']), timeout=timeout):
                return True
        if target['kind'] == 'https':
            conn = http.client.HTTPSConnection(target['hostname'], target['port'],
                                               timeout=timeout)
            raw = socket.create_connection((target['ip'], target['port']), timeout=timeout)
            try:
                conn.sock = ssl.create_default_context().wrap_socket(
                    raw, server_hostname=target['hostname'])
            except Exception:
                raw.close()
                raise
        elif target['kind'] == 'http' and ipaddress.ip_address(target['ip']).is_loopback:
            conn = http.client.HTTPConnection(target['ip'], target['port'], timeout=timeout)
        else:
            raise ValueError('Unsupported probe transport')
        conn.request('GET', target.get('path', '/v1/health'))
        response = conn.getresponse()
        if response.status != 200:
            return False
        body = response.read(4097)
        if len(body) > 4096:
            return False
        data = json.loads(body)
        return isinstance(data, dict) and data.get('healthy') is True
    except (OSError, ValueError, http.client.HTTPException):
        return False
    finally:
        if conn is not None:
            conn.close()


def publish(url, topic, credential, event, timeout):
    timestamp = datetime.fromtimestamp(event['observed_at'], timezone.utc).isoformat()
    payload = {
        'topic': topic,
        'title': f"{event['label']} {event['kind']}: {event['condition']}",
        'message': (f"Observed {timestamp}. Previous: {event['previous']}. "
                    f"Event: {event['event_id']}. Multi-target loss means suspected "
                    'home or overlay-network path failure, not proof of power/ISP cause.'),
        'priority': 3 if event['kind'] == 'RECOVERY' or event['label'].startswith('TEST') else 4,
        'tags': ['white_check_mark'] if event['kind'] == 'RECOVERY' else ['warning'],
    }
    auth = base64.b64encode((credential['username'] + ':' + credential['password']).encode())
    request = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={'Authorization': 'Basic ' + auth.decode(), 'Content-Type': 'application/json'})

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    # Neither redirect targets nor environment proxies may receive these credentials.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    try:
        with opener.open(request, timeout=timeout) as response:
            body = response.read(4097)
            if len(body) > 4096:
                raise ValueError('Publisher response exceeds 4096 bytes')
            data = json.loads(body)
            receipt = data.get('id') if isinstance(data, dict) else None
            if not isinstance(receipt, str) or not receipt.strip():
                raise ValueError('Missing receipt ID')
            return receipt
    except urllib.error.HTTPError as exc:
        exc.close()
        raise


def validate_config(cfg, test=False, state='/var/lib/offsite-watchdog/state.db'):
    if not isinstance(cfg, dict):
        raise ValueError('Configuration must be an object')
    for key in ('label', 'topic', 'publish_url'):
        if not isinstance(cfg.get(key), str) or not cfg[key].strip():
            raise ValueError(f'{key} must be a nonempty string')
    for key, default in (('failures', 3), ('recoveries', 2)):
        value = cfg.get(key, default)
        if type(value) is not int or value < 1:
            raise ValueError(f'{key} must be a positive integer')
    for key, default in (('timeout', 5), ('reminder', 1800), ('max_gap', 150)):
        value = cfg.get(key, default)
        if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
            raise ValueError(f'{key} must be finite and positive')
        if key == 'timeout' and value > 30:
            raise ValueError('timeout must be at most 30 seconds')
    probes = cfg.get('probes')
    roles = {'management_http', 'management_ssh', 'core', 'network', 'public1', 'public2'}
    if not isinstance(probes, dict) or set(probes) != roles:
        raise ValueError('Exactly six named probe roles are required')
    for target in probes.values():
        if not isinstance(target, dict):
            raise ValueError('Each probe must be an object')
        address = ipaddress.ip_address(target.get('ip'))
        port = target.get('port')
        if type(port) is not int or not 1 <= port <= 65535:
            raise ValueError('Probe port must be an integer from 1 to 65535')
        kind = target.get('kind')
        if kind not in ('tcp', 'http', 'https'):
            raise ValueError('Unsupported probe transport')
        if kind == 'http' and not address.is_loopback:
            raise ValueError('HTTP probes must use loopback')
        if kind == 'https' and not isinstance(target.get('hostname'), str):
            raise ValueError('HTTPS probes require a TLS hostname')
    url = urlsplit(cfg['publish_url'])
    if (url.scheme not in ('http', 'https') or not url.hostname or
            url.username is not None or url.password is not None or url.query or url.fragment):
        raise ValueError('Publisher needs HTTP(S), no URL credentials, query or fragment')
    if url.port is not None and not 1 <= url.port <= 65535:
        raise ValueError('Invalid publisher port')
    try:
        publisher_loopback = ipaddress.ip_address(url.hostname).is_loopback
    except ValueError:
        publisher_loopback = False
    if url.scheme == 'http' and not publisher_loopback:
        raise ValueError('Plain HTTP publishing requires literal loopback')
    if test:
        if not cfg['label'].startswith('TEST'):
            raise ValueError('TEST labels are mandatory')
        if Path(state).resolve() == Path('/var/lib/offsite-watchdog/state.db'):
            raise ValueError('Production state forbidden in TEST mode')
        if not all(ipaddress.ip_address(p['ip']).is_loopback for p in probes.values()):
            raise ValueError('TEST probes must be loopback')
        if not publisher_loopback:
            raise ValueError('TEST publisher must use a literal loopback address')
    elif cfg['label'].startswith('TEST'):
        raise ValueError('Use --test for TEST labels')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', default='/etc/offsite-watchdog/config.json')
    parser.add_argument('--state', default='/var/lib/offsite-watchdog/state.db')
    parser.add_argument('--credentials', default=os.environ.get(
        'CREDENTIALS_DIRECTORY', '/etc/offsite-watchdog') + '/publisher.json')
    parser.add_argument('--test', action='store_true',
                        help='require TEST label, loopback targets and separate state; not a dry run')
    args = parser.parse_args()
    os.umask(0o077)
    try:
        cfg = json.loads(Path(args.config).read_text())
        validate_config(cfg, args.test, args.state)
    except (ValueError, KeyError, TypeError, OSError) as exc:
        parser.error(str(exc))
    credential = json.loads(Path(args.credentials).read_text())
    with open(args.state + '.lock', 'w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            futures = {key: pool.submit(probe, target, cfg.get('timeout', 5))
                       for key, target in cfg['probes'].items()}
            results = {key: future.result() for key, future in futures.items()}
        condition = classify(results)
        engine = Engine(args.state, failures=cfg.get('failures', 3),
                        recoveries=cfg.get('recoveries', 2), reminder=cfg.get('reminder', 1800),
                        max_gap=cfg.get('max_gap', 150), label=cfg['label'])
        try:
            engine.observe(condition, time.time())
            ok = engine.deliver(lambda event: publish(
                cfg['publish_url'], cfg['topic'], credential, event, cfg.get('timeout', 5)))
            print(json.dumps({'condition': condition, 'probes': results,
                              'pending': len(engine.pending())}), flush=True)
            return 0 if ok else 1
        finally:
            engine.close()


if __name__ == '__main__':
    raise SystemExit(main())
