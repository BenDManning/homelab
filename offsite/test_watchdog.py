"""Behavioral tests using only disposable state and loopback fixtures."""
import unittest
import watchdog


class ClassificationTests(unittest.TestCase):
    def test_distinguishes_management_and_multitarget_outage(self):
        roles = ('management_http', 'management_ssh', 'core', 'network', 'public1', 'public2')
        samples = [
            ((True, True, True, True, True, True), 'HEALTHY'),
            ((False, True, True, True, True, True), 'MONITORING_ONLY_LOSS'),
            ((False, False, True, True, True, True), 'MANAGEMENT_HOST_LOSS'),
            ((False, False, False, False, True, True), 'HOME_MULTI_TARGET_LOSS'),
            ((False, False, False, False, False, False), 'OFFSITE_CONNECTIVITY_LOSS'),
        ]
        for values, expected in samples:
            with self.subTest(expected=expected):
                self.assertEqual(watchdog.classify(dict(zip(roles, values))), expected)


class StateTests(unittest.TestCase):
    def setUp(self):
        import contextlib
        import io
        import tempfile
        capture = contextlib.ExitStack()
        self.addCleanup(capture.close)
        capture.enter_context(contextlib.redirect_stdout(io.StringIO()))
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = self.tmp.name + '/state.db'
        self.engine = watchdog.Engine(self.path, failures=3, recoveries=2,
                                      reminder=1800, max_gap=150, label='TEST')
        self.addCleanup(self.engine.close)

    def test_debounce_reset_recovery_and_persistence(self):
        e = self.engine
        for state, now in [('MANAGEMENT_HOST_LOSS', 0), ('MANAGEMENT_HOST_LOSS', 60),
                           ('HEALTHY', 120), ('MANAGEMENT_HOST_LOSS', 180),
                           ('MANAGEMENT_HOST_LOSS', 240)]:
            e.observe(state, now)
        self.assertEqual(e.pending(), [])
        e.observe('MANAGEMENT_HOST_LOSS', 300)
        self.assertEqual([x['kind'] for x in e.pending()], ['FIRING'])
        e.close()
        e = watchdog.Engine(self.path, failures=3, recoveries=2,
                            reminder=1800, max_gap=150, label='TEST')
        self.addCleanup(e.close)
        e.observe('HEALTHY', 360)
        self.assertEqual(len(e.pending()), 1)
        e.observe('HEALTHY', 420)
        self.assertEqual([x['kind'] for x in e.pending()], ['FIRING', 'RECOVERY'])
        self.assertEqual(e.pending()[1]['previous'], 'MANAGEMENT_HOST_LOSS')

    def test_stale_or_backwards_observations_restart_debounce(self):
        for times in [(0, 60, 1000), (200, 260, 10)]:
            with self.subTest(times=times):
                for t in times:
                    self.engine.observe('MANAGEMENT_HOST_LOSS', t)
                self.assertEqual(self.engine.pending(), [])
                self.engine.observe('HEALTHY', times[-1] + 1)

    def test_delivery_is_ordered_and_limited_to_twenty_events(self):
        e = self.engine
        now = 0
        for index in range(22):
            condition = 'HOME_MULTI_TARGET_LOSS' if index % 2 == 0 else 'HEALTHY'
            for _ in range(3 if index % 2 == 0 else 2):
                e.observe(condition, now)
                now += 1
        expected = [event['event_id'] for event in e.pending()]
        received = []

        def send(event):
            received.append(event['event_id'])
            return 'fixture-receipt'

        self.assertTrue(e.deliver(send))
        self.assertEqual(received, expected[:20])
        self.assertEqual(len(e.pending()), 2)
        self.assertTrue(e.deliver(send))
        self.assertEqual(received, expected)
        self.assertEqual(e.pending(), [])

    def test_failed_delivery_retries_in_order_then_reminds(self):
        e = self.engine
        for t in (0, 60, 120):
            e.observe('HOME_MULTI_TARGET_LOSS', t)
        original = e.pending()[0]['event_id']

        def failed(event):
            raise OSError('simulated delivery transport failure')

        self.assertFalse(e.deliver(failed))
        self.assertEqual(e.pending()[0]['event_id'], original)
        received = []

        def ok(event):
            received.append(event)
            return 'receipt-' + event['event_id']

        self.assertTrue(e.deliver(ok))
        self.assertEqual(e.pending(), [])
        for t in range(180, 1980, 60):
            e.observe('HOME_MULTI_TARGET_LOSS', t)
        self.assertEqual([x['kind'] for x in e.pending()], ['REMINDER'])
        for t in range(1980, 3900, 60):
            e.observe('HOME_MULTI_TARGET_LOSS', t)
        self.assertEqual(len(e.pending()), 1)
        self.assertTrue(e.deliver(ok))
        self.assertEqual(len(received), 2)

class ProbeTests(unittest.TestCase):
    def setUp(self):
        import http.server
        import threading
        self.body = b'[]'
        test = self
        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *args): pass
            def do_GET(self):
                self.send_response(200)
                self.end_headers()
                self.wfile.write(test.body)
        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        self.target = {'kind': 'http', 'ip': '127.0.0.1', 'port': server.server_port}

    def test_valid_json_without_health_object_is_unhealthy(self):
        self.assertFalse(watchdog.probe(self.target, 1))

    def test_oversized_health_response_is_unhealthy(self):
        self.body = b'{"healthy":true}' + b' ' * 4096
        self.assertFalse(watchdog.probe(self.target, 1))

class PublishTests(unittest.TestCase):
    def setUp(self):
        import http.server
        import threading
        self.requests = []
        self.status = 200
        self.body = b'{"id":"fixture-receipt"}'
        test = self
        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *args): pass
            def do_POST(self):
                test.requests.append(self.path)
                self.rfile.read(int(self.headers['Content-Length']))
                self.send_response(test.status)
                self.send_header('Location', '/redirected')
                self.end_headers()
                self.wfile.write(test.body)
            def do_GET(self):
                test.requests.append(self.path)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"id":"redirect-receipt"}')
        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        self.url = f'http://127.0.0.1:{server.server_port}'
        self.event = {'observed_at': 0, 'label': 'TEST', 'kind': 'FIRING',
                      'condition': 'HOME_MULTI_TARGET_LOSS', 'previous': 'HEALTHY',
                      'event_id': 'fixture-event'}

    def send(self):
        return watchdog.publish(self.url, 'fixture-topic',
                                {'username': 'fixture', 'password': 'not-a-secret'},
                                self.event, 1)

    def test_oversized_or_invalid_receipt_is_not_an_acknowledgment(self):
        import json
        for data in ({'id': 'receipt', 'padding': 'x' * 5000},
                     {'id': '  '}, {'id': 1}, {}, []):
            with self.subTest(data_type=type(data).__name__):
                self.body = json.dumps(data).encode()
                with self.assertRaises(ValueError):
                    self.send()

    def test_publisher_ignores_environment_proxy(self):
        import os
        from unittest.mock import patch
        with patch.dict(os.environ, {'http_proxy': self.url, 'HTTP_PROXY': self.url,
                                     'no_proxy': '', 'NO_PROXY': ''}):
            self.assertEqual(self.send(), 'fixture-receipt')
        self.assertEqual(self.requests, ['/'])

    def test_redirect_cannot_forward_credentials_or_acknowledge(self):
        import urllib.error
        self.status = 302
        with self.assertRaises(urllib.error.HTTPError):
            self.send()
        self.assertEqual(self.requests, ['/'])

class ConfigurationTests(unittest.TestCase):
    def test_invalid_runtime_configuration_is_rejected(self):
        import copy
        base = {'label': 'offsite', 'publish_url': 'http://127.0.0.1:2586',
                'topic': 'offsite-alerts', 'probes': {
                    name: {'kind': 'tcp', 'ip': '192.0.2.10', 'port': 443}
                    for name in ('management_http', 'management_ssh', 'core',
                                 'network', 'public1', 'public2')}}
        watchdog.validate_config(base)
        changes = [('timeout', 0), ('timeout', float('nan')), ('timeout', 31),
                   ('failures', True), ('failures', 0), ('recoveries', 1.5),
                   ('reminder', -1), ('max_gap', 0), ('label', []), ('topic', ''),
                   ('publish_url', 'http://ntfy.example.net'),
                   ('publish_url', 'https://user:placeholder@ntfy.example.net'),
                   ('publish_url', 'https://ntfy.example.net/?token=placeholder'),
                   ('publish_url', 'https://ntfy.example.net/#fragment'),
                   ('publish_url', 'file:///dev/null')]
        for key, value in changes:
            cfg = copy.deepcopy(base)
            cfg[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                watchdog.validate_config(cfg)
        for probe in ({'kind': 'tcp', 'ip': 'host.example.net', 'port': 443},
                      {'kind': 'tcp', 'ip': '192.0.2.1', 'port': 0},
                      {'kind': 'http', 'ip': '192.0.2.1', 'port': 80},
                      {'kind': 'https', 'ip': '192.0.2.1', 'port': 443},
                      {'kind': 'unsupported', 'ip': '192.0.2.1', 'port': 443}):
            cfg = copy.deepcopy(base)
            cfg['probes']['core'] = probe
            with self.subTest(probe=probe), self.assertRaises(ValueError):
                watchdog.validate_config(cfg)
        del base['probes']['core']
        with self.assertRaises(ValueError):
            watchdog.validate_config(base)

    def test_unsafe_test_configuration_rejected_before_credentials_or_state(self):
        import copy
        import json
        import subprocess
        import sys
        import tempfile
        from pathlib import Path
        base = {'label': 'TEST fixture', 'publish_url': 'http://127.0.0.1:9',
                'topic': 'fixture-topic', 'probes': {
                    name: {'kind': 'tcp', 'ip': '127.0.0.1', 'port': 9}
                    for name in ('management_http', 'management_ssh', 'core',
                                 'network', 'public1', 'public2')}}
        cases = []
        cfg = copy.deepcopy(base)
        cfg['publish_url'] = 'https://ntfy.example.net'
        cases.append((cfg, 'loopback'))
        cfg = copy.deepcopy(base)
        cfg['probes']['core']['ip'] = '192.0.2.20'
        cases.append((cfg, 'loopback'))
        cfg = copy.deepcopy(base)
        cfg['label'] = 'not-a-test'
        cases.append((cfg, 'TEST'))
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory)
            for cfg, reason in cases:
                for optimized in (False, True):
                    with self.subTest(reason=reason, optimized=optimized):
                        (p / 'config.json').write_text(json.dumps(cfg))
                        command = [sys.executable] + (['-O'] if optimized else [])
                        command += [watchdog.__file__, '--test', '--config',
                                    str(p / 'config.json'), '--state', str(p / 'state.db'),
                                    '--credentials', str(p / 'missing.json')]
                        result = subprocess.run(command, capture_output=True, text=True, timeout=5)
                        self.assertEqual(result.returncode, 2, result.stderr)
                        self.assertIn(reason, result.stderr)
                        self.assertFalse((p / 'state.db').exists())
                        self.assertFalse((p / 'state.db.lock').exists())

class RuntimeTests(unittest.TestCase):
    def test_real_http_failure_recovery_through_cli_and_persistent_outbox(self):
        import http.server
        import threading
        import tempfile
        import subprocess
        import sys
        import json
        from pathlib import Path
        received = []
        healthy = [False]
        publish_status = [200]

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *args): pass
            def do_GET(self):
                self.send_response(200)
                self.end_headers()
                self.wfile.write(json.dumps({'healthy': healthy[0]}).encode())
            def do_POST(self):
                event = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                received.append(event)
                self.send_response(publish_status[0])
                self.end_headers()
                self.wfile.write(json.dumps({'id': 'fixture-' + str(len(received))}).encode())

        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory)
            port = server.server_port
            probes = {name: {'kind': 'tcp', 'ip': '127.0.0.1', 'port': port}
                      for name in ('management_ssh', 'core', 'network', 'public1', 'public2')}
            probes['management_http'] = {'kind': 'http', 'ip': '127.0.0.1', 'port': port}
            cfg = {'label': 'TEST CLI', 'probes': probes,
                   'publish_url': f'http://127.0.0.1:{port}', 'topic': 'fixture-topic', 'timeout': 1}
            (p / 'config.json').write_text(json.dumps(cfg))
            (p / 'credential.json').write_text(json.dumps(
                {'username': 'fixture', 'password': 'fixture-not-secret'}))
            command = [sys.executable, watchdog.__file__, '--test',
                       '--config', str(p / 'config.json'), '--state', str(p / 'state.db'),
                       '--credentials', str(p / 'credential.json')]

            def run(expected):
                result = subprocess.run(command, capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, expected, result.stderr)
                return json.loads(result.stdout.splitlines()[-1])

            for _ in range(3):
                run(0)
            self.assertEqual(len(received), 1)
            self.assertIn('MONITORING_ONLY_LOSS', received[0]['title'])
            healthy[0] = True
            run(0)
            publish_status[0] = 503
            self.assertEqual(run(1)['pending'], 1)
            self.assertIn('RECOVERY', received[1]['title'])
            publish_status[0] = 200
            self.assertEqual(run(0)['pending'], 0)
            self.assertEqual(len(received), 3)
            self.assertEqual(received[1], received[2])  # Same UUID survives a new process.


if __name__ == '__main__':
    unittest.main()
