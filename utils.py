import asyncio
import logging

from cache import AsyncLRU

logger = logging.getLogger(__name__)


class CMDException(Exception):
    pass


async def run_command(cmd: str, *args) -> str:
    process = await asyncio.create_subprocess_exec(
        cmd,
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    if process.returncode is not None and process.returncode != 0:
       logger.error('Command "%s" return code is %d\n%s', cmd, process.returncode, stderr.decode())
       raise CMDException
    if stdout:
       return stdout.decode()
    return ''


@AsyncLRU(maxsize=32)
async def which(cmd: str) -> str:
    cmd_path = await run_command("which", cmd)
    return cmd_path.strip()
