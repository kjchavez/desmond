#!/usr/bin/env python

# Command line utility for managing a Desmond network.
from __future__ import print_function
import click
import os
import subprocess
import json
import yaml

VAR_DIR = os.path.join(os.path.expanduser('~'), 'var', 'desmond')
NODES_FILENAME = os.path.join(VAR_DIR, "nodes.yaml")
WELL_KNOWN_LAUNCHERS = ['python','python2', 'python3']
RUN_STATE_FILENAME = os.path.join(VAR_DIR, '_run_state.yaml')
DEBUG_LOGDIR = os.path.join("/tmp", "desmond", "logs")

def make_if_not_exists(filename):
    dirname = os.path.dirname(filename)
    if not os.path.isdir(dirname):
        os.makedirs(dirname)

    if not os.path.exists(filename):
        with open(filename, 'w'):
            pass

def get_yaml_file(filename):
    make_if_not_exists(filename)
    with open(filename, 'r') as fp:
        data = yaml.load(fp)
        if not data:
            data = {}
    return data

def save_yaml(data, filename):
    with open(filename, 'w') as fp:
        yaml.dump(data, fp)


def get_nodes():
    return get_yaml_file(NODES_FILENAME)


def get_run_state():
    return get_yaml_file(RUN_STATE_FILENAME)


def check_pid(pid):
    """ Check For the existence of a unix pid. """
    try:
        os.kill(pid, 0)
    except OSError as e:
        return e.errno != 3
    else:
        return True

@click.group()
def cli():
    if not os.path.exists(VAR_DIR):
        # Note this may require root access
        os.makedirs(VAR_DIR)

    make_if_not_exists(NODES_FILENAME)

@cli.command()
@click.argument("node_name")
@click.option("--executable", default=None,
        type=click.Path(exists=True),
        help="Runs a DesmondNode.")
@click.option("--launcher", default="python3",
        help="Specialized launcher for the executable")
def install(node_name, executable, launcher):
    with open(NODES_FILENAME, 'r') as fp:
        nodes = yaml.load(fp)
        if not nodes:
            nodes = {}

    if node_name in nodes:
        print("Node %s is already installed." % node_name)
        return

    if executable is None:
        # Try to find an installed python module with this name!
        raise NotImplementedError("Python module discovery not implemented")

    abs_path = os.path.abspath(executable)
    if launcher not in WELL_KNOWN_LAUNCHERS:
        launcher = os.path.abspath(launcher)

    command = "{0} {1}".format(launcher, abs_path)
    nodes[node_name] = {
        'launcher': launcher,
        'executable': abs_path
    }
    with open(NODES_FILENAME, 'w') as fp:
        yaml.dump(nodes, fp)

@cli.command()
@click.option("--force", '-f', is_flag=True)
def remove_all(force):
    if not force:
        confirm = click.prompt("This will remove all Desmond nodes. Proceed (y/n)?")
        if confirm not in ('y', 'Y'):
            return

    # Fancier uninstall?
    with open(NODES_FILENAME, 'w') as fp:
        yaml.dump({}, fp)

@cli.command()
@click.option("--dry-run", is_flag=True)
@click.option("--nologs", is_flag=True)
def start(dry_run, nologs):
    if nologs:
        print("Debug logs are suppressed.")
    else:
        if not os.path.isdir(DEBUG_LOGDIR):
            os.makedirs(DEBUG_LOGDIR)
        print("Debug logs going to %s" % DEBUG_LOGDIR)

    nodes = get_nodes()
    run_state = get_run_state()
    for name, config in nodes.items():
        if dry_run:
            print("Would execute:", config['launcher'], config['executable'])
            continue

        if name in run_state:
            if check_pid(run_state[name]['pid']):
                print("Node %s is already running. Ignoring." % name)
                continue
            else:
                print("Node seems to have died. Restarting...")

        stdout_fname = os.devnull if nologs \
                      else os.path.join(DEBUG_LOGDIR, name + '.stdout')
        stdout = open(stdout_fname, 'w')
        stderr_fname = os.devnull if nologs \
                      else os.path.join(DEBUG_LOGDIR, name + '.stderr')
        stderr = open(stderr_fname, 'w')
        p = subprocess.Popen([config['launcher'], config['executable']],
                             stdout=stdout, stderr=stderr)
        run_state[name] = {'pid': p.pid}
        save_yaml(run_state, RUN_STATE_FILENAME)
        print("Running %s with pid=%d" % (name, p.pid))

@cli.command()
def stop():
    run_state = get_run_state()
    if not run_state:
        print("Nothing is running.")
        return

    for name, state in run_state.items():
        if 'pid' in state:
            print("Killing %s (pid=%d)" % (name, state['pid']))
            try:
                os.kill(state['pid'], 9)
            except OSError as e:
                print(e.strerror)
                pass

    save_yaml({}, RUN_STATE_FILENAME)

@cli.command()
def show():
    """ Shows all nodes that are running. """
    nodes = get_nodes()
    run_state = get_run_state()
    print("== Installed ==")
    print(json.dumps(nodes, indent=2))
    print("== Run State ==")
    print(json.dumps(run_state, indent=2))

if __name__ == "__main__":
    cli()
