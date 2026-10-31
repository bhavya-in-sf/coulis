"""One request contract for local SDK, REST and CLI, using the existing MCP tools.

The MCP module remains the compatibility dispatcher; profile overrides are request-local.
Local callers are trusted to select a directory. Remote callers cannot select paths.
"""
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location('coulis_mcp_dispatch', Path(__file__).resolve().parents[1] / 'mcp/server.py')
_dispatch = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_dispatch)
OPERATIONS = {t['name'].removeprefix('coulis_'): t['inputSchema'] for t in _dispatch.TOOLS}


def call(folder, operation, arguments=None):
    if operation not in OPERATIONS:
        raise ValueError('Unknown operation')
    if not isinstance(arguments or {}, dict):
        raise ValueError('Arguments must be a JSON object')
    args = dict(arguments or {})
    schema = OPERATIONS[operation]
    if 'profile_dir' in args:
        raise ValueError('Select a profile on the client, not in arguments')
    if set(args) - set(schema['properties']):
        raise ValueError('Unknown argument')
    if set(schema.get('required', [])) - set(args):
        raise ValueError('Missing required arguments')
    return _dispatch.call_tool('coulis_' + operation, {**args, 'profile_dir': str(Path(folder).resolve())})
