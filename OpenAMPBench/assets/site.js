/* Only directory filtering, code folding and on-demand figure loading. */
document.querySelectorAll('[data-directory]').forEach(directory => {
  const input = directory.querySelector('input[type="search"]');
  const select = directory.querySelector('select');
  const rows = [...directory.querySelectorAll('[data-entry]')];
  const apply = () => {
    const query = (input?.value || '').toLowerCase().trim();
    const project = select?.value || '';
    let count = 0;
    rows.forEach(row => {
      row.hidden = !(row.textContent.toLowerCase().includes(query) && (!project || row.dataset.project === project));
      if (!row.hidden) count++;
    });
    const label = directory.querySelector('[data-count]');
    if (label) label.textContent = `${count} ${count === 1 ? 'entry' : 'entries'}`;
    const empty = directory.querySelector('[data-empty]');
    if (empty) empty.hidden = count !== 0;
  };
  input?.addEventListener('input', apply);
  select?.addEventListener('change', apply);
  const selected = new URLSearchParams(location.search).get('project');
  if (selected && select && [...select.options].some(o => o.value === selected)) select.value = selected;
  apply();
});
document.querySelectorAll('.jp-CodeCell .jp-Cell-inputWrapper').forEach((wrapper, i) => {
  const button = document.createElement('button');
  button.className = 'code-toggle'; button.textContent = 'Hide code';
  const id = `code-input-${i}`; wrapper.id = id;
  button.setAttribute('aria-controls', id); button.setAttribute('aria-expanded', 'true');
  wrapper.before(button);
  button.addEventListener('click', () => {
    wrapper.hidden = !wrapper.hidden;
    button.textContent = wrapper.hidden ? 'Show code' : 'Hide code';
    button.setAttribute('aria-expanded', String(!wrapper.hidden));
  });
});
document.querySelector('[data-toggle-code]')?.addEventListener('click', event => {
  const hide = event.currentTarget.dataset.hidden !== 'true';
  document.querySelectorAll('.code-toggle').forEach(button => {
    document.getElementById(button.getAttribute('aria-controls')).hidden = hide;
    button.textContent = hide ? 'Show code' : 'Hide code';
    button.setAttribute('aria-expanded', String(!hide));
  });
  event.currentTarget.dataset.hidden = String(hide);
  event.currentTarget.textContent = hide ? 'Show all code' : 'Hide all code';
});
document.querySelectorAll('[data-viewer]').forEach(surface => {
  const frame = surface.querySelector('iframe');
  let source = surface.dataset.src;
  if (surface.dataset.kind === 'luxar') {
    const scene = new URL(surface.dataset.scene, document.baseURI);
    const viewer = new URL('https://luxarviewer.dev/');
    viewer.searchParams.set('src', scene.href); viewer.searchParams.set('theme', 'light');
    source = viewer.href;
  }
  surface.querySelector('[data-open-viewer]').href = source;
  surface.querySelector('[data-load-viewer]').addEventListener('click', () => {
    frame.src = source; frame.hidden = false;
    surface.querySelector('.figure-placeholder').hidden = true;
    surface.querySelector('[data-unload-viewer]').hidden = false;
  });
  surface.querySelector('[data-unload-viewer]').addEventListener('click', event => {
    frame.removeAttribute('src'); frame.hidden = true;
    surface.querySelector('.figure-placeholder').hidden = false;
    event.currentTarget.hidden = true;
  });
  const full = surface.querySelector('[data-fullscreen]');
  if (!surface.requestFullscreen) full.hidden = true;
  full.addEventListener('click', async () => {
    try { if (document.fullscreenElement) await document.exitFullscreen(); else await surface.requestFullscreen(); }
    catch { full.textContent = 'Use “Open separately”'; }
  });
});
