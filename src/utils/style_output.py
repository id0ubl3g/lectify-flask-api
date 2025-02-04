RESET = "\033[0m"
BOLD = "\033[1m"
BLUE = "\033[34m"
RED = "\033[91m"
ORANGE = "\033[38;5;208m"
GREEN = "\033[92m"
PURPLE = "\033[35m"

import sys

def welcome_message() -> None:
    print(rf'''{BLUE}{BOLD}
 __       ______   ______   ______  __   ______  __  __   
/\ \     /\  ___\ /\  ___\ /\__  _\/\ \ /\  ___\/\ \_\ \  
\ \ \____\ \  __\ \ \ \____\/_/\ \/\ \ \\ \  __\\ \____ \ 
 \ \_____\\ \_____\\ \_____\  \ \_\ \ \_\\ \_\   \/\_____\
  \/_____/ \/_____/ \/_____/   \/_/  \/_/ \/_/    \/_____/

        {RESET}{BLUE}AI-powered Flask {PURPLE}API{BLUE} to summarize video lectures with detailed insights.{RESET}{BLUE}
    
    [*]__author__: {RESET}George Victor | @id0ubl3g{BLUE}
    [*]__github__: {RESET}github.com/id0ubl3g/lectify-flask-api{BLUE}
''')

def interruption_message() -> None:
    print(f'\n{ORANGE}[!]{RESET} Operation interrupted by user')
    sys.exit(0)
