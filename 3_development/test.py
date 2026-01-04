from e2b_code_interpreter import Sandbox
from dotenv import load_dotenv

load_dotenv()
s = Sandbox.create()
print(dir(s)) # This will list all valid methods like 'run_command', 'files', etc.
print(Sandbox.create.__doc__)

s.kill()
