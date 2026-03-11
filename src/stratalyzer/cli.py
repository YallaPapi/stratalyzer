import click


@click.group()
def main():
    """Stratalyzer - Extract strategies from influencer content."""
    pass


@main.command()
@click.argument("folder", type=click.Path(exists=True))
def analyze(folder: str):
    """Analyze a folder of influencer content."""
    click.echo(f"Analyzing {folder}...")
