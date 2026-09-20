# Share card

The picture that shows up when someone posts a 1inventory link — in Slack,
WhatsApp, LinkedIn, iMessage, a Google result preview. One per language, so a
German link does not preview in English.

```
template.svg        the card, 1200 × 630, with {{tokens}} for text
content/<lang>.json the strings
index.html          ?lang=de for one card, no query for all five stacked
card.js             fills the tokens
render.py           photographs each card into img/
../fonts/ ../lib/   shared with ../app-screens/
```

## Rendering

```bash
python3 design/share-card/render.py             # all five
python3 design/share-card/render.py --lang fr
```

English writes `img/og-cover-1200x630.png`, the rest
`img/<lang>/og-cover-1200x630.png`. `tools/i18n_build.py` already rewrites any
`/img/<file>` to `/img/<lang>/<file>` when that file exists, and the `og:image`
and `twitter:image` tags are absolute URLs containing that path, so they follow
automatically — there is no separate rule for them.

The board is the finished size, so this renders at scale 1; a share card is
never shown larger than it is. 1200 × 630 is what every platform asks for, and
the `og:image:width` / `og:image:height` tags on each page say so — change the
board and you change those too.

## Strings

`headline` is the site's own `s081`, the same sentence as `og:title`, split at
its sentence break onto the design's two lines. It is already translated in
`i18n/<lang>.json`, so the card and the page it previews always say the same
thing — if the headline changes there, re-split it here and re-render.

`features` is this card's own copy: three short phrases, bullets between them.
They are one `<text>` with `<tspan>`s, so the bullets land wherever the words
end and no translation needs re-positioning.

Long translations shrink rather than overflow (`data-fit` on all three text
rows, handled by `../lib/fit.js`) — French and Portuguese headlines both use
this. Anything that shrank is listed in `document.body.dataset.shrunk`.

## Cache

Social platforms cache a card against its URL, so the tags carry `?v=22`. Bump
that in the root pages when the artwork changes, or the old picture keeps being
served to anyone who has shared the link before.
