document.querySelectorAll('.main-nav a').forEach(link => {
  if (link.pathname === location.pathname) link.setAttribute('aria-current', 'page');
});
