"""Exercise the workflow's actual decision script without a runner or network."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = json.loads(subprocess.check_output(
    ['ruby', '-rjson', '-ryaml', '-e',
     'puts JSON.generate(YAML.load_file(ARGV[0]))',
     str(ROOT / '.github/workflows/go-ci.yml')], text=True))
STEPS = WORKFLOW['jobs']['test']['steps']
SELECTOR = next(s for s in STEPS if s.get('id') == 'execution')['run']
SHA = 'a' * 40
CONTRACT = {
    'image': 'ghcr.io/example/test@sha256:' + 'b' * 64,
    'config_id': 'sha256:' + 'c' * 64,
    'platform': 'linux/amd64',
    'command': '/usr/local/bin/test-contract',
    'signing_identity': 'https://github.com/example/repo/.github/workflows/image.yml@refs/heads/main',
}


class TestContractSelection(unittest.TestCase):
    def select(self, contract='', reuse='', **overrides):
        with tempfile.TemporaryDirectory() as d:
            output = Path(d) / 'output'
            env = dict(os.environ, CONTRACT=contract, REUSE_SHA=reuse,
                       CANDIDATE_SHA=SHA, CROSS_PLATFORM='false', MODULE_PATH='.',
                       COVERAGE='true', GITHUB_OUTPUT=str(output))
            env.update(overrides)
            result = subprocess.run(['bash', '-c', SELECTOR], env=env,
                                    text=True, capture_output=True, check=False)
            return result.returncode, output.read_text() if output.exists() else ''

    def test_existing_callers_keep_host_tests(self):
        self.assertEqual(self.select(), (0, 'mode=host\n'))

    def test_container_runs_by_default(self):
        self.assertEqual(self.select(json.dumps(CONTRACT)), (0, 'mode=container\n'))

    def test_only_exact_candidate_authorizes_reuse(self):
        self.assertEqual(self.select(json.dumps(CONTRACT), SHA), (0, 'mode=reuse\n'))
        for wrong in ['b' * 40, 'HEAD', 'a' * 39, SHA + '\n', '']:
            with self.subTest(wrong=wrong):
                self.assertEqual(self.select(json.dumps(CONTRACT), wrong),
                                 (0, 'mode=container\n'))

    def test_no_contract_cannot_skip_host_tests(self):
        status, output = self.select(reuse=SHA)
        self.assertNotEqual(status, 0)
        self.assertNotIn('mode=reuse', output)

    def test_invalid_contracts_never_authorize_reuse(self):
        invalid = ['{}', 'null', '[]', '{', json.dumps(CONTRACT) + '\n{}']
        for key, value in [('image', 'example:latest'), ('config_id', 'sha256:bad'),
                           ('platform', 'linux/arm64'), ('command', 'echo pass'),
                           ('command', '/bin/test;echo_pass'), ('signing_identity', ''),
                           ('extra', 'unreviewed')]:
            invalid.append(json.dumps(dict(CONTRACT, **{key: value})))
        for contract in invalid:
            with self.subTest(contract=contract):
                status, output = self.select(contract, SHA)
                self.assertNotEqual(status, 0)
                self.assertNotIn('mode=reuse', output)

    def test_unsupported_scopes_fail_closed(self):
        for override in [{'CROSS_PLATFORM': 'true'}, {'MODULE_PATH': 'submodule'},
                         {'COVERAGE': 'false'}]:
            with self.subTest(override=override):
                status, output = self.select(json.dumps(CONTRACT), SHA, **override)
                self.assertNotEqual(status, 0)
                self.assertNotIn('mode=reuse', output)

    def test_no_checkout_or_install_before_reuse_decision(self):
        self.assertEqual(STEPS[0]['id'], 'execution')
        for step in STEPS:
            if 'uses' in step:
                self.assertIn('steps.execution.outputs.mode', step['if'])
                self.assertNotEqual(step['if'], "steps.execution.outputs.mode == 'reuse'")

    def test_container_runs_candidate_head_and_original_check_survives(self):
        checkout = next(s for s in STEPS if 'actions/checkout@' in s.get('uses', ''))
        self.assertFalse(checkout['with']['persist-credentials'])
        self.assertIn('github.event.pull_request.head.sha', checkout['with']['ref'])
        self.assertEqual(WORKFLOW['jobs']['test']['name'], 'Test')
        self.assertEqual(WORKFLOW['jobs']['test']['permissions'], {'contents': 'read'})

    def test_run_command_preserves_observation_boundaries(self):
        script = next(s for s in STEPS if s.get('name') == 'Run signed offline test contract')['run']
        for required in ['cosign verify --certificate-identity',
                         '--certificate-oidc-issuer https://token.actions.githubusercontent.com',
                         '.[0].Id == $config', '--network none --user 10001:10001',
                         'test -s coverage.out']:
            self.assertIn(required, script)
        self.assertLess(script.index('cosign verify'), script.index('docker pull'))
        self.assertLess(script.index('docker image inspect'), script.index('docker run'))


class TestContainerBoundary(unittest.TestCase):
    def run_contract(self, signature_ok=True, config_ok=True):
        script = next(s for s in STEPS if s.get('name') == 'Run signed offline test contract')['run']
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            calls = root / 'calls'
            stub = root / 'stub'
            stub.write_text(r"""#!/usr/bin/env python3
import json, os, pathlib, sys
name = pathlib.Path(sys.argv[0]).name
with open(os.environ['CALLS'], 'a') as out:
    out.write(json.dumps([name] + sys.argv[1:]) + '\n')
if name == 'cosign' and os.environ['SIGNATURE_OK'] != 'true':
    sys.exit(1)
if name == 'docker' and sys.argv[1:3] == ['image', 'inspect']:
    print(json.dumps([{'Id': os.environ['INSPECT_ID'], 'Os': 'linux', 'Architecture': 'amd64'}]))
if name == 'docker' and sys.argv[1] == 'run':
    pathlib.Path('coverage.out').write_text('mode: atomic\n')
""")
            stub.chmod(0o755)
            for name in ['cosign', 'docker', 'sudo']:
                (root / name).symlink_to(stub)
            env = dict(os.environ, PATH=str(root) + os.pathsep + os.environ['PATH'],
                       CONTRACT=json.dumps(CONTRACT), GITHUB_WORKSPACE=d,
                       CALLS=str(calls), SIGNATURE_OK=str(signature_ok).lower(),
                       INSPECT_ID=CONTRACT['config_id'] if config_ok else 'sha256:' + 'd' * 64)
            result = subprocess.run(['bash', '-c', script], cwd=d, env=env,
                                    capture_output=True, text=True, check=False)
            return result.returncode, [json.loads(line) for line in calls.read_text().splitlines()]

    def test_verified_image_executes_offline_non_root(self):
        status, calls = self.run_contract()
        self.assertEqual(status, 0)
        self.assertEqual([c[0] for c in calls], ['cosign', 'docker', 'docker', 'sudo', 'docker'])
        run = calls[-1]
        self.assertEqual(run[:9], ['docker', 'run', '--rm', '--network', 'none', '--user', '10001:10001', '--env', 'HOME=/tmp'])
        self.assertEqual(run[-2:], [CONTRACT['config_id'], CONTRACT['command']])

    def test_untrusted_signature_never_pulls_or_executes(self):
        status, calls = self.run_contract(signature_ok=False)
        self.assertNotEqual(status, 0)
        self.assertEqual([c[0] for c in calls], ['cosign'])

    def test_wrong_image_config_never_executes(self):
        status, calls = self.run_contract(config_ok=False)
        self.assertNotEqual(status, 0)
        self.assertFalse(any(c[:2] == ['docker', 'run'] for c in calls))


if __name__ == '__main__':
    unittest.main()
