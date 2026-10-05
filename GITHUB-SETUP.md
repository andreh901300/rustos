# Set up RustOS updates on GitHub (one time, ~15 minutes)

After this, every time you make a new version of RustOS you run **`publish.bat`**, and every installed
RustOS picks it up by itself (within a day, or at once with `sudo rustos-autoupdate now`). Nobody
re-installs anything.

**How it works:** GitHub builds a small package called `rustos-base` (your branding, tools, the auto-updater
and the list of apps) and hosts it as a signed update repository on GitHub Pages (free). Installed
systems already check it every day together with the normal Arch updates.

## 1. Create the repository

1. Make a free account at https://github.com (skip if you have one).
2. Click **+ -> New repository**. Name it e.g. `rustos`. Choose **Public** (free GitHub Pages needs a public repo).
   Do NOT tick "Add a README". Click **Create repository**.

## 2. Make the signing key (one time)

Double-click **`repo-setup.bat`**, type your GitHub username and the repository name.
It creates a key that proves updates really come from you, and writes `rustos.conf`.
Notepad opens with a long text starting `-----BEGIN PGP PRIVATE KEY BLOCK-----`. Keep it open.

## 3. Give GitHub the private key (as a secret)

1. On GitHub open your repository -> **Settings -> Secrets and variables -> Actions -> New repository secret**.
2. Name: `GPG_PRIVATE_KEY`
3. Secret: paste ALL the text from Notepad. **Add secret**.

The key never goes in the repository: the folder `.secrets` is ignored by git. Never share that file.

## 4. Turn on GitHub Pages

Repository -> **Settings -> Pages -> Build and deployment -> Source: GitHub Actions**.

## 5. Upload the project (git)

Install Git once (open a terminal): `winget install Git.Git`, then close and reopen the terminal.
In the RustOS folder open a terminal (type `cmd` in the folder's address bar) and run, replacing the URL:

```
git init
git add -A
git commit -m "first version"
git branch -M main
git remote add origin https://github.com/YOURNAME/rustos.git
git push -u origin main
```
A browser window asks you to sign in to GitHub the first time.

## 6. Watch it build

Repository -> **Actions** tab. The "Publish RustOS update repository" run turns green in 2-3 minutes.
If it fails on "deploy", Pages was not enabled (step 4): enable it, then **Re-run all jobs**.

Check: open `https://YOURNAME.github.io/rustos/x86_64/` ... or just `https://YOURNAME.github.io/rustos/`.
You should see the RustOS page.

## 7. Rebuild the ISO once

Run **`build.bat`** again. The ISO now knows your update address and trusts your key. Install RustOS
from this ISO (the installer says "RustOS repository OK - this system will receive RustOS updates
automatically"). **This is the last time you re-install for updates.**

## Every new version

1. Change whatever you want in the project (branding, scripts, `packages-extra.txt`, ...).
2. Optionally raise the number in `VERSION` (cosmetic; every publish is a new version anyway).
3. Double-click **`publish.bat`**, type a short message.

GitHub builds it, and installed systems install it on their next daily update.
Add an app: put its Arch package name in `packages-extra.txt` -> publish -> it appears on every RustOS.

## Good to know

- Removing a package from `packages-extra.txt` does not uninstall it on existing systems (new installs
  just won't get it). To remove something everywhere, tell people `sudo pacman -R name`.
- The repository must be public, so your project files are public too. Secrets are not (see step 3).
- Keep the same repository. If you delete and recreate it, also create a new key and rebuild the ISO.
- If the update repository is down or not set up when someone installs, the installer still works;
  that install just won't get RustOS updates (only the normal Arch ones).
- Systems installed from an ISO built BEFORE this setup keep working but never get RustOS updates;
  re-install them once.

## Releasing a new version (what happens)

1. Change anything (scripts, packages-extra.txt, branding, ...).
2. Double-click **publish.bat**. Type what you changed (this becomes a line in the "What's new" popup).
   Type a new version number for a big release (like `1.2`), or press Enter.
3. GitHub builds and signs the update in about 3 minutes (Actions tab).
4. Every installed RustOS gets it with its next daily update, and shows the "RustOS updated" popup.
   Right away: `sudo rustos-autoupdate now`, or Update Center -> Check for updates.
