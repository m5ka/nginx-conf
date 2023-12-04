import subprocess
import sys
import tomllib
from os.path import exists


if __name__ == "__main__":
    force_remake = "--force-remake" in sys.argv
    with open("certificates.toml", "rb") as file:
        try:
            toml = tomllib.load(file)
        except tomllib.TOMLDecodeError:
            print("Could not decode certificates.toml", file=sys.stderr)
            sys.exit(1)

        for name, domains in toml.items():
            if (
                exists(f"/etc/letsencrypt/live/{name}/fullchain.pem")
                and exists("/etc/letsencrypt/live/{name}/privkey.pem")
                and not force_remake
            ):
                print("✅ {name} already exists!")
            else:
                command = [
                    "/snap/bin/certbot",
                    "certonly",
                    "--cert-name",
                    name,
                    "--webroot",
                    "-w",
                    "/var/www/html",
                ]
                for domain in domains:
                    command += ["-d", domain]
                process = subprocess.run(command, capture_output=True)
                if process.returncode == 0:
                    print(f"✅ {name} is done!")
                else:
                    print(process.stderr, file=sys.stderr)
                    print(
                        f"😥 Something went wrong requesting a certificate for {name}.",
                        file=sys.stderr,
                    )
                    sys.exit(1)
