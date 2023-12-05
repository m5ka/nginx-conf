# my nginx configuration 🌸
this repo stores the nginx configuration for my personal server

## 🪐 requirements
* nginx, compiled with...
    * [image-filter](https://nginx.org/en/docs/http/ngx_http_image_filter_module.html) (`--with-http_image_filter_module`)
    * [brotli](https://github.com/google/ngx_brotli) (manual install)
    * pcre (`--with-pcre`)
    * [ssl](https://nginx.org/en/docs/http/ngx_http_ssl_module.html) (`--with-http_ssl_module`)

## ✍️ editing
you can add more site `.conf` files in the `sites/` directory. they are all automagically included.

### ssl certificates

if you include any new ssl certificates, make sure these are included in `certificates.toml`. this file is in the format of:

```toml
certificate_name = ["domain1.example.org", "domain2.example.org"]
```

the assumption is that certbot is set up so the certificate files (`fullchain.pem` and `privkey.pem`) will end up in the directory `/etc/letsencrypt/live/{certificate_name}/`.

## 🚀 deploying
The `nginx.conf` file from this repository should be used as nginx's config using the `-c` flag. this can be set in nginx's systemd configuration file, for example.

when set up like this, the relative include paths in this repository should resolve as expected.

### before restarting nginx
if you've just pulled in new changes, it's worth making sure ssl certificates are all in place before reloading nginx config. you can do this with a simple python script (run as root):

```bash
sudo python prepare.py
```

you can use the `--force-remake` flag if you want to renew all certificates, not just those that don't already exist.

make sure you are using python 3.11 or above! the script relies on the `tomllib` package that was included in the standard library from 3.11.

## 🐬 license
like pretty much everything i put online, this comes along with the bsd 2-clause license. [read it and weep](LICENSE).