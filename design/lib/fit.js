/* =========================================================================
   Fitting pass, shared by the app screens and the share card.

   The artwork is drawn for English, and SVG neither wraps nor ellipsizes, so
   a longer translation would run out of its box. Three annotations fix that,
   all of them no-ops for English, where everything already fits:

     data-fit="120"       shrink this text until it is at most 120 units wide
     data-pill="saveBtn"  resize that rect around this text, right edge pinned
     data-bar-title /     an app bar: re-centre the title in whatever room the
     data-bar-action      action leaves it, shrinking only if that is not enough
     data-row-label /     a row with a label on the left and a right-anchored
     data-row-value       value: keep a gap between them, shrinking the value
                          first and the label only if that was not enough
     data-fit-group="x"   these texts are read as one control (the two halves
                          of a segmented switch, say), so they all end up at
                          the size the longest of them needed

   fitAll() returns what it changed, so a caller can surface it.
   ========================================================================= */

const MIN_FONT = 9.5;

function fitOne(text) {
  const max = parseFloat(text.dataset.fit);
  const start = parseFloat(getComputedStyle(text).fontSize) ||
                parseFloat(text.getAttribute('font-size'));
  let size = start;
  while (size > MIN_FONT && text.getBBox().width > max) {
    size = Math.round((size - 0.25) * 100) / 100;
    text.setAttribute('font-size', size);
  }
  return size < start ? { text: text.textContent, from: start, to: size } : null;
}

function fitPill(text) {
  const rect = text.ownerSVGElement.getElementById(text.dataset.pill);
  if (!rect) return;
  // Only grow: English already fits, and the design's own padding stays.
  const pad = 8;
  const right = rect.x.baseVal.value + rect.width.baseVal.value;
  const width = Math.max(rect.width.baseVal.value, text.getBBox().width + pad * 2);
  rect.setAttribute('x', right - width);
  rect.setAttribute('width', width);
  text.setAttribute('x', right - width / 2);
}

function fitBar(svg) {
  const title = svg.querySelector('[data-bar-title]');
  const action = svg.querySelector('[data-bar-action]');
  if (!title || !action) return;
  const gap = 10;
  const left = 38;                       // clear of the back chevron
  const pill = action.dataset.pill && svg.getElementById(action.dataset.pill);
  const right = (pill ? pill.x.baseVal.value : action.getBBox().x) - gap;

  title.dataset.fit = String(right - left);
  const shrunk = fitOne(title);

  // The title is centred on the artboard, which is only the middle of the bar
  // while the action is narrow. Once it is not, centre it on what is left.
  const box = title.getBBox();
  if (box.x < left || box.x + box.width > right) {
    title.setAttribute('x', left + (right - left) / 2);
  }
  return shrunk;
}

/* A label and a right-anchored value share one line: the label's left edge and
   the value's right edge are both pinned, and between them is the room. When a
   translation needs more than that, both give way by the same proportion —
   shrinking only one of them leaves a 9.5pt value beside a 14pt label, which
   reads as a mistake rather than as a tighter row. */
function fitRow(label, value) {
  const gap = 12;
  const sizeOf = el => parseFloat(getComputedStyle(el).fontSize) ||
                       parseFloat(el.getAttribute('font-size'));
  const startLabel = sizeOf(label), startValue = sizeOf(value);
  const room = (value.getBBox().x + value.getBBox().width) - label.getBBox().x - gap;
  const tooWide = () => label.getBBox().width + value.getBBox().width > room;

  let scale = 1;
  while (scale > 0.55 && tooWide()) {
    scale -= 0.02;
    label.setAttribute('font-size', Math.round(startLabel * scale * 100) / 100);
    value.setAttribute('font-size', Math.round(startValue * scale * 100) / 100);
  }
  if (scale === 1) return [];
  return [{ text: `${label.textContent.trim()} / ${value.textContent.trim()}`,
            from: `${startLabel}/${startValue}`,
            to: `${sizeOf(label)}/${sizeOf(value)}` }];
}

function fitAll(root) {
  const notes = [];
  root.querySelectorAll('svg').forEach(svg => {
    svg.querySelectorAll('[data-pill]').forEach(fitPill);
    svg.querySelectorAll('[data-row-value]').forEach(value => {
      const label = svg.querySelector(`[data-row-label="${value.dataset.rowValue}"]`);
      if (label) notes.push(...fitRow(label, value));
    });
    const barred = fitBar(svg);
    if (barred) notes.push(barred);
    svg.querySelectorAll('[data-fit]:not([data-bar-title])').forEach(t => {
      const n = fitOne(t);
      if (n) notes.push(n);
    });

    // Members of a group are one control to the eye, so they must not end up
    // at different sizes: level them to whatever the longest one needed.
    const groups = {};
    svg.querySelectorAll('[data-fit-group]').forEach(t => {
      (groups[t.dataset.fitGroup] = groups[t.dataset.fitGroup] || []).push(t);
    });
    Object.values(groups).forEach(members => {
      const sizes = members.map(m => parseFloat(getComputedStyle(m).fontSize) ||
                                     parseFloat(m.getAttribute('font-size')));
      const smallest = Math.min(...sizes);
      members.forEach((m, i) => {
        if (sizes[i] > smallest) m.setAttribute('font-size', smallest);
      });
    });
  });
  return notes;
}
