import subprocess
import sys
import tomllib
from os.path import exists


if __name__ == "__main__":
    with open("certificates.toml", "rb") as file:
        try:
            toml = tomllib.load(file)
        except tomllib.TOMLDecodeError:
            print("Could not decode certificates.toml", file=sys.stderr)
            sys.exit(1)

        for name, domains in toml.items():
            if exists(f"/etc/letsencrypt/live/{name}/fullchain.pem") and exists(
                "/etc/letsencrypt/live/{name}/privkey.pem"
            ):
                print("✅ {name} already exists!")
            else:
                d_str = " ".join([f"-d {d}" for d in domains])
                ret = subprocess.call(
                    f"/snap/bin/certbot certonly --cert-name {name} "
                    f"--webroot -w /var/www/html {d_str}"
                )
                if ret == 0:
                    print(f"✅ {name} is done!")
                else:
                    print(
                        f"😥 Something went wrong requesting a certificate for {name}.",
                        file=sys.stderr,
                    )
                    sys.exit(1)
