window.MathJax = {
  tex: {
    tags: "ams"
  },
  startup: {
    pageReady: function () {
      return MathJax.startup.defaultPageReady().then(function () {
        document.querySelectorAll('mjx-mtd[id]').forEach(function (td) {
          var id = td.id;
          if (!id.startsWith('mjx-eqn:')) return;
          var tag = 'eqn-' + id.slice('mjx-eqn:'.length);
          var anchor = document.getElementById(tag);
          if (!anchor) return;
          var link = document.createElement('a');
          link.href = '#' + tag;
          link.style.color = 'inherit';
          link.style.textDecoration = 'none';
          while (td.firstChild) link.appendChild(td.firstChild);
          td.appendChild(link);
        });
      });
    }
  }
};
