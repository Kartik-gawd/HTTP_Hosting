# Enabling HTTPS:

By default, this server runs on HTTP. While this is perfectly fine for a local area network (LAN), you might want to enable HTTPS to encrypt traffic or to use modern web features that require a secure context.

However, enabling HTTPS on a local network using a basic **self-signed certificate** introduces a major headache:

|> Modern browsers may block file downloads from untrusted certificates as a security measure.

This guide explains how to properly set up HTTPS using **mkcert** so you get a trusted certificate and avoid download restrictions.
It is a one time setup

---

## `mkcert`

[`mkcert`](https://github.com/FiloSottile/mkcert) is a simple tool that creates a local Certificate Authority (CA) on your machine and generates certificates that your OS and browser trust automatically.

## Step 1: Install `mkcert`

### Windows ([scoop](https://scoop.sh))

```powershell
scoop bucket add extras
scoop install mkcert
```

### macOS (Homebrew)

```bash
brew install mkcert
```

### Linux

```bash
sudo apt install libnss3-tools
brew install mkcert
```

> For additional installation methods, see the official mkcert repository:
>
> https://github.com/FiloSottile/mkcert

---

## Step 2: Install the Local CA

Run:

```bash
mkcert -install
```

This creates a local Certificate Authority and adds it to your system trust store.

You may be prompted for administrator permissions.

---

## Step 3: Generate the Certificates

Find your server's local IPv4 address (for example `192.168.1.50`).

Generate certificates for your LAN IP and localhost:

```bash
mkcert 192.168.1.50 localhost 127.0.0.1
```

This command creates two files:

- Certificate file
- Private key file

---

## Step 4: Apply the Certificates to the Server

1. Rename the generated files to:

   ```text
   cert.pem
   key.pem
   ```

2. Move both files into the same directory as your `server.py` script.

3. Restart the server.

The server will automatically detect the certificates, enable TLS, and switch to:

```text
https://
```

---

# Trusting the Server on Other LAN Devices

## 1. Locate the Root CA

On the server machine run:

```bash
mkcert -CAROOT
```

This opens the directory containing the local Certificate Authority files.

Locate:

```text
rootCA.pem
```

> ⚠️ Never share `rootCA-key.pem`.
>
> That file is the private key for your Certificate Authority and must remain secret.

---

## 2. Transfer the Root CA

Copy `rootCA.pem` to the client device using:

- USB drive
- Email
- Shared network folder
- Temporary HTTP download

---

## 3. Install the Root CA

### Windows

1. Double-click the certificate file.
2. (You may need to rename it to `.crt`.)
3. Click **Install Certificate**.
4. Choose:

   ```text
   Trusted Root Certification Authorities
   ```

5. Complete the wizard.

---

### Android

Navigate to:

```text
Settings
→ Security
→ Encryption & Credentials
→ Install a Certificate
→ CA Certificate
```

Select `rootCA.pem`.

---

### iPhone / iPad (iOS)

1. AirDrop, email, or otherwise transfer the certificate.
2. Open the file and install the profile.
3. Go to:

   ```text
   Settings
   → Profile Downloaded
   ```

4. Install the profile.
5. Then enable full trust:

   ```text
   Settings
   → General
   → About
   → Certificate Trust Settings
   ```

6. Enable trust for your newly installed Root CA.

---

## Note

For a temporary file-sharing server, this may be too much,
If your use case is simply sharing files with people on the same local network, running the server over standard HTTP is usually the most practical option.
