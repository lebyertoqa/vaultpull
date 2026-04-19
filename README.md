# vaultpull

> CLI tool to sync secrets from HashiCorp Vault into local `.env` files safely.

---

## Installation

```bash
pip install vaultpull
```

Or install from source:

```bash
git clone https://github.com/youruser/vaultpull.git && cd vaultpull && pip install .
```

---

## Usage

Authenticate with Vault and pull secrets into a local `.env` file:

```bash
vaultpull --addr https://vault.example.com \
          --token s.xxxxxxxxxxxxxxxx \
          --path secret/myapp/prod \
          --output .env
```

This will fetch all key-value pairs at the given Vault path and write them to `.env`, creating the file if it does not exist or safely merging with existing values.

### Options

| Flag | Description |
|------|-------------|
| `--addr` | Vault server address |
| `--token` | Vault authentication token |
| `--path` | Secret path in Vault |
| `--output` | Output `.env` file path (default: `.env`) |
| `--overwrite` | Overwrite existing keys without prompting |
| `--dry-run` | Preview changes without writing to disk |

### Example Output

```
[+] Fetched 6 secrets from secret/myapp/prod
[+] Written to .env (2 new, 1 updated, 3 unchanged)
```

---

## License

[MIT](LICENSE)