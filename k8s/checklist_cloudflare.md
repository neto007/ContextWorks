# Checklist: Cloudflare Quick Tunnel (Dynamic URL)

This setup uses Cloudflare's free "TryCloudflare" feature to generate a random public URL (e.g., `https://random-name.trycloudflare.com`). No token required.

- [ ] **1. Deploy**
    - Run `./deploy.sh`.
    - No secrets needed.

- [ ] **2. Get the URL**
    - The URL is generated dynamically on pod startup. View it in the logs:
      ```bash
      kubectl logs -l app=cloudflared -n contextworks-platform
      ```
    - Look for a line like: `+--------------------------------------------------------------------------------------------+`
    - Or `https://.*.trycloudflare.com`

- [ ] **3. Note**
    - This URL changes every time the pod restarts.
    - Not recommended for production (use Token/Zero Trust for permanent URLs).
