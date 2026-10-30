const motion = document.querySelector('#motion');
const preference = window.matchMedia('(prefers-reduced-motion: reduce)');
let paused = preference.matches;
function setPaused(value) { paused = value; document.body.classList.toggle('paused', value); if (motion) { motion.setAttribute('aria-pressed', String(value)); motion.textContent = value ? 'Resume motion' : 'Pause motion'; } }
setPaused(paused);
motion?.addEventListener('click', () => setPaused(!paused));
preference.addEventListener('change', event => setPaused(event.matches));
document.querySelector('#check')?.addEventListener('click', () => {
 document.querySelector('#checked').textContent = 'Demo checked: ' + new Intl.DateTimeFormat(undefined, {month:'short',day:'numeric',hour:'numeric',minute:'2-digit',second:'2-digit',timeZoneName:'short'}).format(new Date());
});
