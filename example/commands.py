from index.cli import main


@main.command(help='Custom command')
def only_print():
    print('Custom command')
