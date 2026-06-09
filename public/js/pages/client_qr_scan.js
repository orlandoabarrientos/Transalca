(function () {
            var params = new URLSearchParams(window.location.search);
            var id = params.get('id') || '';
            var target = '/scanner' + (id ? ('?qr=' + encodeURIComponent(id)) : '');
            var link = document.getElementById('manualRedirect');
            if (link) link.href = target;
            window.location.replace(target);
        })();
