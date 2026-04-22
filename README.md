# Arus — Banjir Drill · docs site

Static one-page site for the hackathon submission.

## Deploy to GitHub Pages

```bash
# From this directory, push to the gh-pages branch of SunflowersLwtech/arus
cd /Users/chenyu/Documents/dev/MyAI/hackathon/docs-site

git init
git add .
git commit -m "arus docs site"
git branch -M gh-pages
git remote add origin git@github.com:SunflowersLwtech/arus.git
git push -u origin gh-pages --force
```

Then in GitHub repo settings → Pages → set source to `gh-pages` branch,
`/ (root)`. URL will be `https://sunflowerslwtech.github.io/arus/`.

## Local preview

```bash
cd docs-site
python3 -m http.server 8080
# open http://localhost:8080
```

## Layout

- `index.html` — one-page site, all inline CSS
- `video/arus-demo-5min.mp4` — the 5-min submission video (43 MB)
- `assets/s00..s07.png` — Remotion-rendered section hero images
