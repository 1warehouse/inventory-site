/* =========================================================================
   Overlap audit, shared by the app screens and the share card.

   The fitting pass keeps a translation inside the box it was given. It cannot
   know that two boxes sit on the same line — a row's label and its value, say
   — so a long translation can still collide. This looks at what actually got
   drawn and reports any two visible texts whose ink overlaps.

   Occlusion matters: a sheet is painted over a dimmed list, so the list's
   words are behind an opaque rect and are not a collision. A text is ignored
   when a later, opaque shape covers it completely.

   Run it from the gallery page (window.auditOverlaps()), or headless through
   design/check.py, which loads every screen in every language.
   ========================================================================= */

/* Text can also escape the shape it sits in — a segmented switch's option
   running out of its half — without touching any other text. Which shape is
   the container cannot be guessed from the drawing: a label sits inside the
   screen, a card, a chip and whatever decorative blob happens to be behind
   it, and only one of those says anything about whether it fits. So the
   template declares it with data-fit, and this checks the declaration held.
   A text still too wide after fitting has hit the size floor, which means the
   string needs to be shorter, not smaller. */
function auditFit(root = document) {
  const found = [];
  root.querySelectorAll('svg').forEach(svg => {
    const label = svg.closest('figure')?.querySelector('figcaption')
                     ?.textContent.split('—')[0].trim()
                  || svg.getAttribute('data-id') || 'screen';
    svg.querySelectorAll('text[data-fit]').forEach(t => {
      const max = parseFloat(t.dataset.fit);
      const width = t.getBBox().width;
      if (width > max + 0.5) {
        found.push({ screen: label, a: t.textContent.replace(/\s+/g, ' ').trim(),
                     b: `its box (${max.toFixed(0)} units)`,
                     overlap: `${(width - max).toFixed(0)} too wide at the size floor` });
      }
    });
  });
  return found;
}

function auditOverlaps(root = document) {
  const found = [];
  const contains = (outer, inner) =>
    outer.left <= inner.left + 0.5 && outer.right >= inner.right - 0.5 &&
    outer.top <= inner.top + 0.5 && outer.bottom >= inner.bottom - 0.5;

  root.querySelectorAll('svg').forEach(svg => {
    const label = svg.closest('figure')?.querySelector('figcaption')
                     ?.textContent.split('—')[0].trim()
                  || svg.getAttribute('data-id') || 'screen';
    const all = [...svg.querySelectorAll('*')];

    const texts = all
      .map((el, idx) => ({ el, idx }))
      .filter(n => n.el.tagName === 'text')
      .map(n => ({ ...n, rect: n.el.getBoundingClientRect(),
                   text: n.el.textContent.replace(/\s+/g, ' ').trim() }))
      .filter(n => n.text && n.rect.width > 0);

    const hidden = n => all.some((el, idx) => {
      if (idx <= n.idx || el.tagName === 'text' || el.tagName === 'tspan') return false;
      const fill = el.getAttribute('fill') || '';
      if (!fill || fill === 'none') return false;
      if (parseFloat(el.getAttribute('opacity') ?? '1') < 0.95) return false;
      return contains(el.getBoundingClientRect(), n.rect);
    });

    const visible = texts.filter(n => !hidden(n));
    for (let i = 0; i < visible.length; i++) {
      for (let j = i + 1; j < visible.length; j++) {
        const a = visible[i].rect, b = visible[j].rect;
        const w = Math.min(a.right, b.right) - Math.max(a.left, b.left);
        const h = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
        // Two lines stacked in a paragraph share box height — a descender
        // beside an ascender — without their ink meeting. A real clash is
        // two texts on the same line, so require most of the height to be
        // shared, not a few pixels of it.
        const sameLine = h > 0.55 * Math.min(a.height, b.height);
        if (w > 1 && sameLine) {
          found.push({ screen: label, a: visible[i].text, b: visible[j].text,
                       overlap: `${w.toFixed(0)}x${h.toFixed(0)}` });
        }
      }
    }
  });
  return found;
}
