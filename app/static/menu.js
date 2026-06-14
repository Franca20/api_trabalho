document.addEventListener('DOMContentLoaded', () => {
  const menuBtn = document.getElementById('menu-btn');
  const menuClose = document.getElementById('menu-close');
  const sideMenu = document.getElementById('side-menu');
  const overlay = document.getElementById('menu-overlay');

  function openMenu() {
    sideMenu.classList.add('open');
    overlay.classList.add('visible');
  }

  function closeMenu() {
    sideMenu.classList.remove('open');
    overlay.classList.remove('visible');
  }

  menuBtn?.addEventListener('click', openMenu);
  menuClose?.addEventListener('click', closeMenu);
  overlay?.addEventListener('click', closeMenu);
});
