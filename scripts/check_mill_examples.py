#!/usr/bin/env python3
"""Compile/run the Mill fixtures and verify packaging, cache invalidation, and selection."""
import argparse
import re
import shutil
import subprocess
import tempfile
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
VERSION = '1.1.10'
LAUNCHER = f'https://repo.maven.apache.org/maven2/com/lihaoyi/mill-dist/{VERSION}/mill-dist-{VERSION}-mill.sh'


def run(command, cwd, expected=None):
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, timeout=300)
    if result.returncode:
        raise RuntimeError(f'{command} failed:\n{result.stdout}\n{result.stderr}')
    if expected is not None and expected not in result.stdout:
        raise AssertionError(f'missing expected output {expected!r}:\n{result.stdout}\n{result.stderr}')
    return re.sub(r'\x1b\[[0-9;]*m', '', result.stdout)


def check(root):
    with tempfile.TemporaryDirectory(prefix='dot-agents-mill-') as temporary:
        workspace = Path(temporary)
        launcher = workspace / 'mill'
        with urllib.request.urlopen(LAUNCHER, timeout=60) as response:
            launcher.write_bytes(response.read())
        launcher.chmod(0o755)
        fixtures = [
            ('declarative', 'mill-project-models/assets/declarative', ['run'], 'declarative Mill'),
            ('script', 'mill-project-models/assets/script', ['Hello.scala', 'Mill'], 'script Mill: Mill'),
            ('codegen', 'mill-build-logic/assets/codegen', ['app.run'], 'generated with Mill'),
            ('mixed-jvm', 'mill-jvm-modules/assets/mixed-jvm',
             ['app.run', '+', 'scalaService.test', '+', 'unrelated.compile'], 'Hello, Mill from Scala'),
            ('multi-file', 'mill-monorepo/assets/multi-file',
             ['app.run', '+', 'scalaService.test'], 'Hello, Mill from Scala'),
            ('ox-app', 'mill-vss/assets/ox-app', ['app.run'], 'VSS with Mill and Ox'),
        ]
        completed = []
        try:
            for name, relative, args, expected in fixtures:
                source = root / relative
                work = workspace / name
                shutil.copytree(source, work)
                completed.append(work)
                print(f'Checking {name} on Mill {VERSION}', flush=True)
                run([str(launcher), *args], work, expected)
                if name == 'codegen':
                    generated, = (work / 'out').rglob('Generated.java')
                    before = generated.stat().st_mtime_ns
                    run([str(launcher), 'app.generatedSources'], work)
                    assert generated.stat().st_mtime_ns == before, 'unchanged generator did not stay cached'
                    (work / 'app/message.txt').write_text('changed tracked input\n')
                    run([str(launcher), 'app.run'], work, 'changed tracked input')
                    assert 'changed tracked input' in generated.read_text()
                if name == 'mixed-jvm':
                    run([str(launcher), 'app.assembly'], work)
                    artifact = work / 'out/app/assembly.dest/out.jar'
                    assert artifact.is_file(), 'assembly missing'
                    run(['java', '-jar', str(artifact)], work, 'Hello, Mill from Scala')
                    selector = '{scalaService.test,unrelated.compile}'
                    run([str(launcher), 'selective.prepare', selector], work)
                    kotlin = work / 'kotlinImpl/src/example/KotlinGreeting.kt'
                    kotlin.write_text(kotlin.read_text() + '\n// changed tracked source\n')
                    selected = run([str(launcher), 'selective.resolve', selector], work)
                    lines = [line.strip() for line in selected.splitlines()]
                    assert any(line.startswith('scalaService.test') for line in lines), selected
                    assert 'unrelated.compile' not in lines, selected
                    run([str(launcher), 'selective.run', selector], work)
                print(f'PASS: {name}', flush=True)
        finally:
            for work in completed:
                subprocess.run([str(launcher), 'shutdown'], cwd=work, capture_output=True, timeout=30)
    print('OK: six examples, mixed-language tests, executable assembly, tracked generation/cache, selective baseline')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skills-root', type=Path, default=REPO / 'collections/shared')
    args = parser.parse_args()
    check(args.skills_root.resolve())


if __name__ == '__main__':
    main()
