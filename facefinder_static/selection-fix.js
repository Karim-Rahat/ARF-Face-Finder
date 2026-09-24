(() => {
  let lastIndex = null;
  const gallery = document.querySelector('#gallery');
  const selectAll = document.querySelector('#selectAll');

  // Capture the intended value once. updateSelection() changes the checkbox
  // while files are toggled, so reading event.target.checked inside the loop
  // caused the old handler to select only part of the gallery.
  selectAll.addEventListener('change', event => {
    event.stopImmediatePropagation();
    const shouldSelect = event.target.checked;
    const ids = [...state.results.keys()];
    ids.forEach(id => toggle(id, shouldSelect));
  }, true);

  gallery.addEventListener('mousedown', event => {
    if (event.shiftKey && event.target.closest('.photo-card')) event.preventDefault();
  }, true);

  gallery.addEventListener('click', event => {
    const card = event.target.closest('.photo-card');
    if (!card) return;
    event.preventDefault();
    event.stopImmediatePropagation();

    const cards = [...gallery.querySelectorAll('.photo-card')];
    const currentIndex = cards.indexOf(card);
    if (event.shiftKey && lastIndex !== null) {
      const start = Math.min(lastIndex, currentIndex);
      const end = Math.max(lastIndex, currentIndex);
      for (let index = start; index <= end; index += 1) {
        toggle(cards[index].dataset.id, true);
      }
    } else {
      toggle(card.dataset.id);
    }
    lastIndex = currentIndex;
  }, true);
})();
