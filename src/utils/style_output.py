RESET = "\033[0m"
BOLD = "\033[1m"
BLUE = "\033[34m"
RED = "\033[91m"
ORANGE = "\033[38;5;208m"
GREEN = "\033[92m"
PURPLE = "\033[35m"

from time import sleep
import sys

def print_welcome_message() -> None:
    print(rf'''{BLUE}{BOLD}

 ______   ______   __   ______   ______  __       __  __   
/\  == \ /\  == \ /\ \ /\  ___\ /\  ___\/\ \     /\ \_\ \  
\ \  __< \ \  __< \ \ \\ \  __\ \ \  __\\ \ \____\ \____ \ 
 \ \_____\\ \_\ \_\\ \_\\ \_____\\ \_\   \ \_____\\/\_____\
  \/_____/ \/_/ /_/ \/_/ \/_____/ \/_/    \/_____/ \/_____/
            
        {RESET}{BLUE}AI-powered {PURPLE}API{BLUE} to summarize video lectures with detailed insights.{RESET}{BLUE}
    
    [*]__author__: {RESET}George Victor | @id0ubl3g{BLUE}
    [*]__github__: {RESET}github.com/id0ubl3g/briefly-flask-api{BLUE}
''')
    
def loading_bar() -> None:
    print(f'{BLUE}[+]{RESET} Initializing {PURPLE}API{RESET}\n')

    total_steps = 40
    for i in range(total_steps + 1):
        percentage = (i / total_steps) * 100
        bar = f"[{'#' * i}{'.' * (total_steps - i)}]"
        sys.stdout.write(f'\r    {bar} {percentage:.0f}%')
        sys.stdout.flush()
        sleep(0.15)
    print(f'\r\t')
    sleep(1.5)