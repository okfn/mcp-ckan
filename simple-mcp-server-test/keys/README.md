# SSH Deploy Keys for Private Repositories

This directory stores SSH private keys used by the fetch script to clone
private git repositories. All files in this directory are gitignored.

**Always use read-only deploy keys.** The MCP server only needs to clone
and pull — it never pushes. Read-only keys limit the damage if a key is
ever compromised.


## Step by step

### 1. Generate a key pair

Run this from the project root (one key per private repo):

```bash
ssh-keygen -t ed25519 -f keys/my-repo-key -N "" -C "deploy@mcp-server"
```

This creates two files:

| File                    | What it is            | Where it goes         |
|-------------------------|-----------------------|-----------------------|
| `keys/my-repo-key`     | Private key (secret)  | Stays here on the server |
| `keys/my-repo-key.pub` | Public key            | Added to the git host |

Ensure protecting the file key `chmod 600 keys/my-repo-key`

### 2. Add the public key to your git host

Copy the public key contents:

```bash
cat keys/my-repo-key.pub
```

Then add it as a **read-only deploy key** on your git hosting platform:

#### GitHub

1. Go to your repository on GitHub
2. **Settings** > **Deploy keys** > **Add deploy key**
3. Paste the public key
4. Title: something descriptive like `mcp-server-deploy`
5. **Leave "Allow write access" unchecked** (read-only)
6. Click **Add key**

#### GitLab

1. Go to your repository on GitLab
2. **Settings** > **Repository** > **Deploy keys**
3. Paste the public key
4. Title: `mcp-server-deploy`
5. **Uncheck "Grant write permissions"** (read-only)
6. Click **Add key**.

### 3. Reference the key in tool_sources.yaml

```yaml
sources:
  - name: my-private-tools
    repo: git@github.com:your-org/my-private-tools.git
    path: src/tools
    ref: main
    key: keys/my-repo-key
```

The `key` path is relative to the project root.

### 4. Test the connection

```bash
python scripts/fetch_remote_tools.py
```

If authentication fails, verify:
- The private key file has correct permissions: `chmod 600 keys/my-repo-key`
- The public key was added to the correct repository
- The repo URL uses SSH format (`git@...`), not HTTPS

## Security notes

- **Never commit private keys.** This directory is gitignored but stay careful.
- **Use one key per repository.** If a key is compromised, you only need to
  rotate it for one repo. GitHub enforces this — a deploy key can only be
  added to one repository.
- **Read-only is enough.** The fetch script only clones and pulls.
- **Set restrictive permissions:** `chmod 600 keys/*` (owner read/write only).
