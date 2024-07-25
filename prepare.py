import subprocess
import sys
import tomllib
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Self

import click
from cryptography import x509
from cryptography.hazmat.backends import default_backend

FULL_CHAIN_PATH_TEMPLATE = "/etc/letsencrypt/live/%s/fullchain.pem"
PRIVATE_KEY_PATH_TEMPLATE = "/etc/letsencrypt/live/%s/privkey.pem"


class CertificateValidity(Enum):
    """Represents the validity of the SSL certificates for a particular site."""

    valid = "valid"
    not_exist = "not_exist"
    invalid_ssl = "invalid_ssl"
    expired = "expired"
    soon_to_expire = "soon_to_expire"


@dataclass
class Certificate:
    """Represents a set of SSL certificates associated with a particular site."""

    full_chain: Path
    private_key: Path

    @staticmethod
    def from_name(name: str) -> Self:
        return Certificate(
            Path(FULL_CHAIN_PATH_TEMPLATE % name),
            Path(PRIVATE_KEY_PATH_TEMPLATE % name),
        )

    def get_validity(
        self, soon_to_expire_is_invalid: bool = False
    ) -> CertificateValidity:
        if not self.full_chain.is_file():
            return CertificateValidity.not_exist
        if not self.private_key.is_file():
            return CertificateValidity.not_exist
        encrypted_contents = self.full_chain.read_bytes()
        try:
            certificate = x509.load_pem_x509_certificate(
                encrypted_contents, default_backend()
            )
        except:
            return CertificateValidity.invalid_ssl
        if datetime.now(timezone.utc) > certificate.not_valid_after_utc:
            return CertificateValidity.expired
        if soon_to_expire_is_invalid:
            future_date = datetime.now(timezone.utc) + timedelta(days=30)
            if future_date > certificate.not_valid_after_utc:
                return CertificateValidity.soon_to_expire
        return CertificateValidity.valid


@dataclass
class Site:
    """
    Represents a site, which contains a set of SSL certificates for a particular range
    of domains.
    """

    name: str
    domains: list[str]
    certificate: Certificate


def log_issued_certificate(name: str, reason_for_issue: CertificateValidity):
    """
    Prints an appropriate message for a newly issued certificate, depending on the
    previous validity of the certificate.
    """
    if reason_for_issue == CertificateValidity.not_exist:
        click.echo(f"✅ New certificate issued for {click.style(name, fg='cyan')}.")
        return
    match reason_for_issue:
        case CertificateValidity.invalid_ssl:
            reason = " as the old one was invalid"
        case CertificateValidity.expired:
            reason = " as the old one had expired"
        case CertificateValidity.soon_to_expire:
            reason = " as the old one was about to expire"
        case _:
            reason = ""
    click.echo(f"✅ Certificate reissued for {click.style(name, fg='cyan')}{reason}.")


def prepare_certificate(
    site: Site, force_remake: bool = False, soon_to_expire_is_invalid: bool = False
) -> bool:
    """
    Prepares certificates for a particular site if applicable. Returns a boolean
    representing whether the function was successful or not.
    """
    validity = site.certificate.get_validity(soon_to_expire_is_invalid)
    if validity == CertificateValidity.valid and not force_remake:
        click.echo(
            f"🆗 Certificates for {click.style(site.name, fg='cyan')} are already "
            "valid."
        )
        return True

    command = [
        "/snap/bin/certbot",
        "certonly",
        "--cert-name",
        site.name,
        "--webroot",
        "-w",
        "/var/www/html",
        "--non-interactive",
        "--agree-tos",
        "--renew-with-new-domains",
        "--expand",
    ]
    for domain in site.domains:
        command += ["-d", domain]

    process = subprocess.run(command, capture_output=True)
    if process.returncode == 0:
        if force_remake:
            click.echo(
                f"✅ Remade certificates for {click.style(site.name, fg='cyan')}."
            )
        else:
            log_issued_certificate(site.name, validity)
        return True
    else:
        click.echo(process.stderr, err=True)
        click.echo(
            (
                "😥 Something went wrong requesting a certificate for "
                f"{click.style(site.name, fg='cyan')}."
            ),
            err=True,
        )
        return False


@click.command("prepare", help="Prepare SSL certificates for configured domains")
@click.argument("names", nargs=-1)
@click.option(
    "--force-remake",
    is_flag=True,
    default=False,
    help="Remake certificates even if they already exist",
)
@click.option(
    "--soon-is-invalid",
    is_flag=True,
    default=False,
    help="Count certificates as invalid if they will expire in the next 30 days",
)
def prepare(names: list[str], force_remake: bool, soon_is_invalid: bool):
    sites: dict[str, Site] = {}
    with open("certificates.toml", "rb") as file:
        try:
            toml = tomllib.load(file)
        except tomllib.TOMLDecodeError:
            print("Could not decode certificates.toml", file=sys.stderr)
            sys.exit(1)

        for name, domains in toml.items():
            site = Site(
                name,
                domains,
                Certificate.from_name(name),
            )
            sites[name] = site

    if names:
        for name in names:
            if name not in sites:
                click.echo(
                    f"😓 {click.style(name, fg='yellow')} is not a valid site.",
                    err=True,
                )
                return
        sites = [s for s in sites if s.name in names]

    for site in sites.values():
        if not prepare_certificate(site, force_remake, soon_is_invalid):
            return


if __name__ == "__main__":
    prepare()
