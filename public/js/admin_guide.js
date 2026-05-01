$(document).ready(function() {
    $('#sidebarContainer').load('/components/admin_sidebar.html', () => {
        document.querySelector('[data-page="guide"]')?.classList.add('active');
    });
    $('#navbarContainer').load('/components/admin_navbar.html', () => loadNavSession());
});
