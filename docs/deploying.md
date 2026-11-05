# Deploying

**The build writes the invitations and nothing else**
([cli.md](cli.md#build)). The response headers, `robots.txt`, the root page
and the "not found" page belong to the site that publishes the output. This
page describes what that site should provide: without it the pages still
work, but they lose their protective headers and their protection from
search engines. The samples are for a site that publishes the invitations
under `/invite` and for the `_headers` syntax of Cloudflare Pages; other
static hosts have equivalents.

## Publishing into a directory of a site

The output goes into a directory of the site and is built with the path that
directory has on the site:

```
python3 build.py build --data path/to/data --media path/to/media --out path/to/site/invite --base-path /invite
```

Every address inside the pages then starts with `/invite`: the shared files
are at `/invite/assets/…` and a guest's page is at `/invite/<token>/`. The
layout of the output does not depend on `--base-path`: with another path only
the prefix of the addresses inside the pages differs (`"/assets/` becomes
`"/invite/assets/`), and the media, calendar files and the link preview
image are the same bytes under the same names. `--out` must not be the
directory of the whole site: the build replaces `--out` as a whole and
refuses a directory that looks like a site ([cli.md](cli.md#the-output-directory)).

Look at a build under a prefix from the directory above it, the way the site
will publish it:

```
python3 -m http.server -d path/to/site 8000     # http://localhost:8000/invite/<token>/
```

A build for the root of a site (`--base-path /`, the default) is served from
its own directory:

```
python3 -m http.server -d path/to/out 8000      # http://localhost:8000/<token>/
```

The built-in server answers an unknown address with its own error page: the
"not found" page belongs to the site ([below](#the-not-found-page)).

A sample build step of a deployment (GitHub Actions, `ubuntu-24.04`). Chrome
is preinstalled on the runner and there is no separate step for the image:
`build` renders it. The address of the site is not passed. The invitations go
into the directory `dist/invite` of the site and are published under
`/invite`; a later step puts the other files of the site into `dist/`.

```yaml
- name: Build the invitations
  env:
    SITE_NAME: ${{ vars.SITE_NAME }}
  run: |
    google-chrome --version
    python3 path/to/build.py build --data path/to/data --media path/to/media --out dist/invite --base-path /invite
```

The pages that the event links lead to under `--allow-path`
([cli.md](cli.md#--allow-path-links-to-other-pages-of-the-site)) belong to the
site as well: the build does not look for them, so the site makes sure that
every such link has its page.

## Headers and the Content Security Policy

A sample `_headers` at the root of the site (the syntax of Cloudflare Pages):

```
/*
  X-Robots-Tag: noindex, nofollow
  Referrer-Policy: no-referrer
  X-Content-Type-Options: nosniff
  X-Frame-Options: DENY
  Content-Security-Policy: default-src 'self'; style-src 'self'; img-src 'self' data:; media-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'
/invite/:token/
  ! X-Robots-Tag
  Cache-Control: private, no-cache
```

A request that matches several rules gets the headers of **all** of them, and
an exclamation mark with a space before a header name removes a header set by
a rule **higher up in the file**. So `X-Robots-Tag` stays on `/*` (the root
and wrong addresses outside the pages) and is removed on the block of the
pages, `/invite/:token/`: the invitation pages are the only thing that needs
link previews in messengers. The same block adds
`Cache-Control: private, no-cache`. The placeholder `:token` matches exactly
**one segment** of the path, so the **shared files** (`/invite/assets/…`, one
segment deeper) do not match the rule of the pages and get exactly what `/*`
gives. Cloudflare Pages redirects `/invite/<token>` and
`/invite/<token>/index.html` to `/invite/<token>/`, so the rule of the pages
covers them too. The protective headers and the policy come from the `/*`
block, for the whole site.

**The order of the blocks matters.** The rules apply in the order of the
file, so `! ` removes only what a rule **above** it has added; a removal
placed above its rule does nothing. Swap the `/*` and `/invite/:token/`
blocks, and `noindex` silently returns to every page. A check of the site is
a good way to pin the order; on the host, check the result with a request
(`curl -I`) to a page, a shared file and a wrong address.

A side effect worth knowing: `/invite/:token/` matches not only the
invitation pages but also **wrong** one-segment addresses inside `/invite/`
(a typo in a token). They get the "not found" page, with `X-Robots-Tag`
removed. The two cases cannot be told apart by path: that page is served as
a 404 response, not at an address of its own. There is no harm as long as it
has the `robots` meta tag ([below](#the-not-found-page)), and a search engine
never comes to those addresses anyway: `Disallow: /` of the `*` group keeps it
out.

**The policy works because the pages need no exceptions**: every script and
style sheet is a file in `<base-path>/assets/`, there are no inline scripts,
no embedded widgets or maps, and the only external addresses are links to map
services that open on a tap. Styles come only from files:
`style-src 'self'` without `'unsafe-inline'`. The built pages have neither
`style` attributes nor `<style>` elements (a test checks this), and the
styles the script sets while it runs (the width of the hidden scroll bar
while the viewer is open, the proportion of a video frame in it) go through
the CSSOM (`element.style.setProperty`), which the policy does not restrict.
So the markup and the scripts never use `style="…"` or
`setAttribute('style', …)`: the browser would not apply such a style. Scripts
(`script-src`) need no exceptions either.

The `referrer` meta tag of `template.html` repeats the header, for a host
that does not understand `_headers`.

## The "not found" page

**One neutral page for the root and every wrong address**: the same page,
with no data and no link preview tags, with
`<meta name="robots" content="noindex, nofollow">` and
`<meta name="referrer" content="no-referrer">`. It gives no hint about the
structure of the links and does not tell how close a guess came. On
Cloudflare Pages **a `404.html` at the root of the site is required**: without
it the host switches to single-page-application mode, and every address
returns the root page with code 200. `404.html` is looked up from the
directory of the request upwards, so a wrong address inside `/invite/` gets
the root one; the build writes no `404.html` of its own.

A "not found" page that uses `app.css` gets the plain canvas: the
`invitation` class that paints it in the colour of the cover bar is only on
the invitation pages ([design-system.md](design-system.md#the-browser-colour)).

## `robots.txt` and link preview bots

A sitemap is not needed, and `robots.txt` at the root of the site looks like
this:

```
User-agent: TelegramBot
User-agent: TwitterBot
User-agent: facebookexternalhit
User-agent: WhatsApp
User-agent: Discordbot
User-agent: Slackbot
User-agent: Slackbot-LinkExpanding
User-agent: ViberBot
User-agent: SkypeUriPreview
Allow: /

User-agent: *
Disallow: /
```

A named group wins over `*` not by the order of lines but by the rules of the
format: a robot follows **exactly one** group, the one whose agent name
matches it most closely, and named groups are **not merged** with the `*`
group, so the listed bots do not inherit `Disallow: /`. Several
`User-agent:` lines in a row form one group, and names are compared
regardless of letter case. Search engine robots (Googlebot, YandexBot,
Bingbot) fall into the `*` group and never fetch a page. The file lists no
addresses: `Allow: /` names nothing.

The invitation pages deliberately have no `robots` meta tag: a preview bot
that gets `noindex` builds no card (the tag is for the "not found" page
only). While `robots.txt` says `Disallow: /` for `*`, a search engine never
fetches the page and so would never read the tag anyway: the protection from
indexing rests on the `*` group, not on the tag.

## The cost of link previews

A preview in a messenger is not free. An address sent in Telegram is fetched
by **Telegram's servers**: the address of the invitation becomes known to
them and goes into their preview cache, which has no documented lifetime and
cannot be cleared by hand; the preview image moves to their CDN and stays
available to everybody who has the message, whatever happens to the site.
The same holds for the other listed bots. If that is not acceptable,
`noindex` is not the answer: do not send the link through a messenger at
all. Send the picture as a file, and the address over a channel that fetches
no previews.

Test a preview with a **new** message, after running the address through
[@WebpageBot](https://t.me/webpagebot): a message already sent never changes
its card, and the preview cache lives until it is refreshed by hand.

There is a risk with the image itself: the WhatsApp documentation asks for an
absolute `og:image` address and calls `og:url` required, and guides to
Telegram say that relative paths are not resolved. The build never knows the
address of the site, so the pages have neither
([cli.md](cli.md#link-preview-options)), and a card may come **without the
image** (the title and the description stay). Check it on the published site
([testing.md](testing.md#on-real-devices)).

## Privacy on the site

The pages are private by construction ([README](../README.md#privacy-model));
the site keeps them so:

- the root and every wrong address get the same "not found" page, which says
  nothing about the structure of the links;
- `robots.txt` keeps every crawler out except the named group of link
  preview bots, and the invitation pages have no `noindex`, so the cards are
  built; the price of that is above;
- `Referrer-Policy: no-referrer` keeps the address of a page, token
  included, from leaking to the sites its links lead to;
- when the host offers rate limiting, a limit on `<base-path>/*` slows down
  guessing of tokens ([data-format.md](data-format.md#tokens)).
