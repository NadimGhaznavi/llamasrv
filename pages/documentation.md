---
title: "Maintaining the documentation"
lang: en
locale: en-US
language_name: English
translation_key: llamasrv-documentation
---

The documentation site is configured for
[llamasrv.osoyalce.com](https://llamasrv.osoyalce.com/). Its source lives in this
repository and its shared presentation comes from the
[Minimal Mistakes theme](https://github.com/NadimGhaznavi/minimal-mistakes).

## Editing the site

Use `index.md` as the documentation entry point, `pages/` for guides, and
`pages/images/` for images. Link each new guide from the index and include a
link back to the index in the guide. Keep `README.md` short and record changes
under `Unreleased` in `CHANGELOG.md`.

Give every guide a front-matter title and the English metadata used on this
page: `lang: en`, `locale: en-US`, and `language_name: English`. Assign a unique,
stable `translation_key` beginning with `llamasrv-`. The shared theme renders
the title, so begin body sections at heading level two.

Use baseurl-aware links and images so the content also works under a repository
subpath. For example:

{% raw %}
```liquid
[Documentation index]({{ site.baseurl }}{% link index.md %})
![{{ site.title }} logo]({{ site.logo | relative_url }})
```
{% endraw %}

The site uses the dark skin, wide content, and author sidebar supplied by the
theme. Both the masthead and homepage use the original project logo at
`pages/images/llamasrv-logo.svg`, selected through `logo` in `_config.yml`.

English is the default language. Multilingual support is enabled; add translated
pages only when requested, reusing the corresponding English translation key.

## Publishing

The workflow in `.github/workflows/jekyll-gh-pages.yml` builds the repository
root on GitHub, uploads the generated site, and deploys it to GitHub Pages.
Pushes to `main` trigger it; manual runs build and publish only when `main` is
selected. Site builds and generated output stay on GitHub.

Before the first publication, check the repository's **Settings → Pages**:

1. Select **GitHub Actions** as the publishing source.
2. Set the custom domain to `llamasrv.osoyalce.com`, matching the root `CNAME`
   file and `_config.yml`.
3. Confirm the DNS CNAME record points to `NadimGhaznavi.github.io` and enable
   **Enforce HTTPS** when GitHub makes it available.

After an authorized publication, verify both workflow jobs, HTTPS, the homepage,
this guide, and the changelog. Check the logo, dark theme, wide layout, sidebar,
and mobile view. The shared MyCount endpoint must use the `llamasrv` site
identifier. Check translated navigation and the language selector when
translations are added.

## Pinned BMForge skill

The project pins `bmforge-github-pages` specification `0.1.0` in
`.agents/bmforge/lock.json`. Check local integrity and compare with the cached
BMForge source using:

```sh
python3 .agents/bmforge/manage.py check --project .
```

This check uses the local source snapshot and does not fetch or upgrade skills.

---

[Documentation index]({{ site.baseurl }}{% link index.md %})
