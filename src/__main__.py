import argparse
import logging

from . import Config, Trello, GUI


DEFAULT_CONFIG_PATH = os.path.expanduser(os.path.join('~', '.config', 'quickIn.toml'))

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', default=DEFAULT_CONFIG_PATH,
                        help=f'configuration file path (TOML format, defaults to {DEFAULT_CONFIG_PATH}')
    parser.add_argument('-d', '--debug', default=False, action='store_true', help='enable debug logging')
    return parser.parse_args()


args = parse_args()
logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO,
                    format='%(levelname)s %(name)s: %(message)s')

config = Config(args.config)
trello = Trello(config)
app = GUI(trello)

app.loop()

