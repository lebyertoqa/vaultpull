"""CLI entry point for vaultpull."""
import sys
import click

from vaultpull.config import load_config, validate
from vaultpull.secrets import fetch_secrets, VaultClientError
from vaultpull.dotenv_writer import write_env_file


@click.command()
@click.option(
    "--config",
    "config_path",
    default="vaultpull.yaml",
    show_default=True,
    help="Path to vaultpull config file.",
)
@click.option(
    "--output",
    "output_path",
    default=".env",
    show_default=True,
    help="Path to write the .env file.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Print secrets as env lines without writing to disk.",
)
@click.option(
    "--overwrite/--no-overwrite",
    default=True,
    show_default=True,
    help="Overwrite existing .env file.",
)
def main(config_path, output_path, dry_run, overwrite):
    """Sync secrets from HashiCorp Vault into a local .env file."""
    try:
        config = load_config(config_path)
    except FileNotFoundError:
        click.echo(f"[error] Config file not found: {config_path}", err=True)
        sys.exit(1)
    except Exception as exc:
        click.echo(f"[error] Failed to load config: {exc}", err=True)
        sys.exit(1)

    errors = validate(config)
    if errors:
        for err in errors:
            click.echo(f"[error] {err}", err=True)
        sys.exit(1)

    try:
        secrets = fetch_secrets(config)
    except VaultClientError as exc:
        click.echo(f"[error] Vault error: {exc}", err=True)
        sys.exit(1)

    if dry_run:
        from vaultpull.dotenv_writer import secrets_to_env_lines
        lines = secrets_to_env_lines(secrets)
        for line in lines:
            click.echo(line)
        return

    written = write_env_file(secrets, output_path, overwrite=overwrite)
    if written:
        click.echo(f"[ok] Wrote {len(secrets)} secret(s) to {output_path}")
    else:
        click.echo(f"[skip] {output_path} already exists and --no-overwrite is set.")


if __name__ == "__main__":
    main()
