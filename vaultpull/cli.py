"""CLI entry point for vaultpull."""

import sys
from pathlib import Path

import click

from vaultpull.config import load_config, validate
from vaultpull.diff import compute_diff
from vaultpull.dotenv_writer import write_env_file
from vaultpull.audit import record_sync
from vaultpull.rollback import backup_env_file, prune_backups
from vaultpull.secrets import VaultClientError, fetch_secrets


@click.command()
@click.option("--config", "config_path", default=".vaultpull.yml", show_default=True)
@click.option("--env-file", "env_file", default=".env", show_default=True)
@click.option("--no-overwrite", is_flag=True, default=False)
@click.option("--dry-run", is_flag=True, default=False)
@click.option("--backup/--no-backup", default=True, show_default=True)
@click.option("--keep-backups", default=5, show_default=True, type=int)
def main(config_path, env_file, no_overwrite, dry_run, backup, keep_backups):
    """Sync secrets from Vault into a local .env file."""
    try:
        cfg_dict = load_config(config_path)
    except FileNotFoundError:
        click.echo(f"Config not found: {config_path}", err=True)
        sys.exit(1)

    errors = validate(cfg_dict)
    if errors:
        for e in errors:
            click.echo(f"Config error: {e}", err=True)
        sys.exit(1)

    from vaultpull.config import VaultConfig, from_dict
    cfg: VaultConfig = from_dict(cfg_dict)

    if no_overwrite and Path(env_file).exists():
        click.echo("Skipping: .env already exists and --no-overwrite is set.")
        sys.exit(0)

    try:
        secrets = fetch_secrets(cfg)
    except VaultClientError as exc:
        click.echo(f"Vault error: {exc}", err=True)
        sys.exit(1)

    diff = compute_diff(secrets, env_file)

    if not diff.has_changes:
        click.echo("No changes detected.")
        record_sync(env_file, written=[], skipped=list(secrets.keys()))
        sys.exit(0)

    if dry_run:
        click.echo("Dry run — changes detected but not written.")
        for k in diff.added:
            click.echo(f"  + {k}")
        for k in diff.changed:
            click.echo(f"  ~ {k}")
        sys.exit(0)

    backup_path = None
    if backup:
        backup_path = backup_env_file(env_file)
        if backup_path:
            click.echo(f"Backup created: {backup_path}")
            prune_backups(env_file, keep=keep_backups)

    write_env_file(secrets, env_file)
    written = list(diff.added | diff.changed)
    skipped = [k for k in secrets if k not in written]
    record_sync(env_file, written=written, skipped=skipped)
    click.echo(f"Wrote {len(written)} secret(s) to {env_file}.")
