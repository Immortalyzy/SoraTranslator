# Portable Release Layout

SoraTranslator release packaging produces a deterministic portable layout at `build/portable`:

```text
build/portable/
  app/                    # Electron runtime folder (contains packaged frontend .exe)
  backend/                # Python backend sources + runtime helper executables
  run.bat                 # Portable launcher (backend bootstrap + frontend start)
  setup-config.bat        # First-run setup wizard for endpoint/model/key
  config.template.json    # Safe defaults, no plaintext secrets
  .env.example            # Environment variable template for API keys
  translators.json        # Endpoint catalog
```

## Packaging Command

Run from repository root:

```bat
package.bat
```

The script:
- auto-detects frontend runtime folder (`frontend/dist_electron/win-unpacked`, `win-x64-unpacked`, `win-arm64-unpacked`, `frontend/dist_electron/app`, or fallback `build/app`)
- copies backend runtime assets while excluding development-only directories
- copies launch/config artifacts
- runs `scripts/release_smoke_check.ps1` to validate required files
- writes detailed packaging output to `package.log.txt`
- fails fast if `build/portable` cannot be cleaned (for example, locked files from a running app)

## Launcher Runtime Controls

- `run.bat` writes execution logs to `log.txt` (and mirrors to `launcher.log.txt` for compatibility).
- Dev/smoke runs enforce a default runtime timeout; override with `--max-runtime-seconds <N>`.
- Release runs are unlimited by default; pass `--max-runtime-seconds <N>` to enforce a hard timeout.
- Release mode defaults backend port to `5000` for compatibility; override with `--backend-port <N>`.
- Startup/install timeout is separate and configurable with `--startup-timeout-seconds <N>`.
- For quick non-install smoke checks, use `run.bat --smoke --skip-install --max-runtime-seconds 180`.
