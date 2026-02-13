// ToC-related Functionality
var tocManuallyOpen = false;

function toggleToc() {
  var toc = document.getElementById("TableOfContents");
  if (window.getComputedStyle(toc, null).display == "none") {
    toc.style.display = "block";
    tocManuallyOpen = true;
    // Show all nested sections on mobile
    $(toc).find("li > ul").show();
    $(toc).find("a.current").removeClass("current");
  } else {
    toc.style.display = "none";
    tocManuallyOpen = false;
  }
}

function handleTocVisibility() {
  var toc = document.getElementById("TableOfContents");
  if (!toc) return;

  if (window.innerWidth < 1280) {
    if (!tocManuallyOpen) {
      toc.style.display = "none";
    }
    var toc_btn = document.getElementById("toc-btn");
    if (toc_btn && !toc.childNodes.length) {
      toc_btn.style.display = "none";
    }
  } else {
    toc.style.display = "block";
    tocManuallyOpen = false;
    var title = document.querySelector(".page-title");
    if (title) {
      toc.style.top = title.getBoundingClientRect().top + window.scrollY + "px";
    }
  }
}

(function () {
  var $toc = $("#TableOfContents");

  if ($toc.length > 0) {
    var $window = $(window);

    function onScroll() {
      if (window.innerWidth < 1280) {
        return true;
      }
      var currentScroll = $window.scrollTop();
      var h = $(".body h1, .body h2, .body h3, .body h4, .body h5, .body h6");
      var id = "";
      h.each(function (i, e) {
        e = $(e);
        if (e.offset().top - 10 <= currentScroll) {
          id = e.attr("id");
        }
      });
      var current = $toc.find("a.current");

      function isVisible(el) {
        if (typeof jQuery === "function" && el instanceof jQuery) {
          el = el[0];
        }
        var rect = el.getBoundingClientRect();
        return (
          rect.bottom >= 0 &&
          rect.right >= 0 &&
          rect.top <=
          (window.innerHeight || document.documentElement.clientHeight) &&
          rect.left <=
          (window.innerWidth || document.documentElement.clientWidth)
        );
      }

      if (!isVisible(document.getElementById("article-content"))) {
        current.each(function (i, e) {
          $(e).removeClass("current");
        });
        $toc.find("li > ul").hide();
        return true;
      }

      if (current.length == 1 && current.eq(0).attr("href") == "#" + id)
        return true;

      current.each(function (i, e) {
        $(e).removeClass("current");
      });
      $toc.find("li > ul").hide();

      $toc
        .find('a[href="#' + id + '"]')
        .parentsUntil("#TableOfContents")
        .each(function (i, e) {
          $(e).children("a").addClass("current").siblings("ul").show();
        });
    }

    function adjustToc() {
      handleTocVisibility();

      if (!tocManuallyOpen) {
        $toc.find("a.current").removeClass("current");
        $toc.find("li > ul").hide();
      }

      onScroll();
    }

    $window.on("scroll", onScroll);
    $window.on("resize", adjustToc);

    if (document.readyState != "loading") {
      adjustToc();
    } else {
      document.addEventListener("DOMContentLoaded", adjustToc);
    }
  }
})();
