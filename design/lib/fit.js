/* =========================================================================
   Fitting pass, shared by the app screens and the share card.

   The artwork is drawn for English, and SVG neither wraps nor ellipsizes, so
   a longer translation would run out of its box. Three annotations fix that,
   all of them no-ops for English, where everything already fits:

     data-fit="120"       shrink this text until it is at most 120 units wide
     data-pill="saveBtn"  resize that rect around this text, right edge pinned
     data-bar-title /     an app bar: re-centre the title in whatever room the
     data-bar-action      action leaves it, shrinking only if that is not enough

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

function fitAll(root) {
  const notes = [];
  root.querySelectorAll('svg').forEach(svg => {
    svg.querySelectorAll('[data-pill]').forEach(fitPill);
    const barred = fitBar(svg);
    if (barred) notes.push(barred);
    svg.querySelectorAll('[data-fit]:not([data-bar-title])').forEach(t => {
      const n = fitOne(t);
      if (n) notes.push(n);
    });
  });
  return notes;
}
