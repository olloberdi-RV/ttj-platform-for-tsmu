import sys, types

# Ensure backwards-compatibility whether imported as 'backend' or 'ttj_platform.backend'
if 'ttj_platform' not in sys.modules:
    import backend
    _mod = types.ModuleType('ttj_platform')
    _mod.backend = backend
    sys.modules['ttj_platform'] = _mod
    sys.modules['ttj_platform.backend'] = backend
