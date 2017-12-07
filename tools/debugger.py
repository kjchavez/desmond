# Commandline tool to debug the Desmond network.
import click
import time

from desmond.motor import MotorService

@click.group()
def cli():
    pass

@cli.command()
def list_actuators():
    service = MotorService()
    click.echo("Actuators")
    click.echo("="*80)
    for actuator in service.actuators:
        click.echo("{0} @ {1}".format(actuator.name, actuator.address))
    service.shutdown()

@cli.command()
@click.argument("name")
@click.argument("payload")
def actuate(name, payload):
    service = MotorService()
    actuators = [a for a in service.actuators if a.name == name]
    if not actuators:
        click.echo("Couldn't find actuator with name {0}".format(name))
        return

    for actuator in actuators:
        unescaped = bytes(payload, 'utf8').decode('unicode_escape')
        status = actuator.send(bytes(unescaped, 'latin1'))
        click.echo(str(actuator))
        click.echo("Status: {0}".format(status))

    service.shutdown()


if __name__ == "__main__":
    cli()
