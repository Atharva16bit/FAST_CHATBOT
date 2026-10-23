// Runs only for a new submission or completed answer. No user text is executed.
(() => {
  const nodes = document.querySelectorAll('[data-fast-scroll]');
  const anchor = nodes[nodes.length - 1];
  if (!anchor) return;
  const event = anchor.dataset.fastScroll;
  if (window.__fastScrollEvent === event) return;
  window.__fastScrollStop?.();
  window.__fastScrollEvent = event;
  const turn = event.split('-')[0];
  if (window.__fastManualTurn === turn) return;
  let stopped = false;
  const timers = [];
  let observer;
  const stop = () => {
    if (stopped) return;
    stopped = true;
    timers.forEach(clearTimeout);
    observer?.disconnect();
    document.removeEventListener('wheel', onUserScroll, true);
    document.removeEventListener('touchmove', onUserScroll, true);
    document.removeEventListener('keydown', onKey, true);
  };
  const onUserScroll = () => { window.__fastManualTurn = turn; stop(); };
  const onKey = e => {
    if (['ArrowUp', 'PageUp', 'Home'].includes(e.key)) onUserScroll();
  };
  const follow = () => {
    if (!stopped && anchor.isConnected) {
      anchor.scrollIntoView({block: 'end', behavior: 'instant'});
    }
  };
  window.__fastScrollStop = stop;
  document.addEventListener('wheel', onUserScroll, {capture: true, passive: true});
  document.addEventListener('touchmove', onUserScroll, {capture: true, passive: true});
  document.addEventListener('keydown', onKey, true);
  requestAnimationFrame(follow);
  [50, 150, 350].forEach(ms => timers.push(setTimeout(follow, ms)));
  if (anchor.dataset.live === 'true') {
    const content = document.querySelector('.stMain .block-container');
    if (content) {
      observer = new ResizeObserver(() => requestAnimationFrame(follow));
      observer.observe(content);
    }
    timers.push(setTimeout(stop, 45000));
  } else {
    timers.push(setTimeout(stop, 800));
  }
})();
