import click

from .eval import main as eval_cmd


@click.group()
def cli():
    pass


cli.add_command(eval_cmd, name="eval")
main = cli
