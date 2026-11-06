// 首頁作品目錄、類型篩選、作品頁資訊欄與上下篇導覽。
// 資料來源：data/works.js（window.WORKS）。
(function () {
  "use strict";
  var works = window.WORKS || [];
  var isWorkPage = document.body.hasAttribute("data-slug");
  var root = isWorkPage ? "../" : ""; // 作品頁在 works/ 底下

  function el(tag, attrs, children) {
    var node = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) {
      if (k === "text") node.textContent = attrs[k];
      else node.setAttribute(k, attrs[k]);
    });
    (children || []).forEach(function (c) { if (c) node.appendChild(c); });
    return node;
  }

  function statusTag(status) {
    return el("span", { "class": "status", "data-status": status, text: status });
  }

  /* ---------- 首頁 ---------- */
  function renderIndex() {
    var list = document.getElementById("work-list");
    var filterBox = document.getElementById("filters");
    if (!list) return;

    function draw(type) {
      list.innerHTML = "";
      var shown = works.filter(function (w) { return type === "全部" || w.type === type; });
      if (!shown.length) {
        list.appendChild(el("li", { "class": "empty", text: "這個類型還沒有作品。" }));
        return;
      }
      shown.forEach(function (w) {
        var meta = el("div", { "class": "meta" }, [
          el("div", {}, [el("b", { text: w.type })]),
          w.event ? el("div", { text: w.event }) : null,
          el("div", { text: w.role }),
          el("div", { text: w.team }),
          statusTag(w.status)
        ]);
        var thumb = el("div", { "class": "thumb" }, [
          el("img", { src: root + w.cover, alt: "", loading: "lazy" })
        ]);
        var a = el("a", { href: root + "works/" + w.slug + ".html" }, [
          el("span", { "class": "year", text: w.date.replace("-", ".") }),
          el("div", {}, [
            el("span", { "class": "title", text: w.title }),
            el("span", { "class": "sub", text: w.subtitle })
          ]),
          meta,
          thumb
        ]);
        list.appendChild(el("li", { "class": "work-row" }, [a]));
      });
    }

    if (filterBox) {
      var types = ["全部"];
      works.forEach(function (w) { if (types.indexOf(w.type) < 0) types.push(w.type); });
      types.forEach(function (t, i) {
        var b = el("button", { type: "button", "aria-pressed": i === 0 ? "true" : "false", text: t });
        b.addEventListener("click", function () {
          filterBox.querySelectorAll("button").forEach(function (x) { x.setAttribute("aria-pressed", "false"); });
          b.setAttribute("aria-pressed", "true");
          draw(t);
        });
        filterBox.appendChild(b);
      });
    }
    draw("全部");
  }

  /* ---------- 作品頁 ---------- */
  function renderWorkPage() {
    var slug = document.body.getAttribute("data-slug");
    var i = -1;
    works.forEach(function (w, idx) { if (w.slug === slug) i = idx; });
    if (i < 0) return;
    var w = works[i];

    var facts = document.getElementById("facts");
    if (facts) {
      var rows = [
        ["日期", document.createTextNode(w.date.slice(0, 4) + " 年 " + parseInt(w.date.slice(5), 10) + " 月")],
        w.event ? ["比賽／課程", document.createTextNode(w.event)] : null,
        ["類型", document.createTextNode(w.type)],
        ["我的角色", document.createTextNode(w.role)],
        ["團隊", document.createTextNode(w.team)],
        ["狀態", statusTag(w.status)],
        ["技術與工具", el("ul", {}, w.tools.map(function (t) { return el("li", { text: t }); }))]
      ];
      rows.forEach(function (r) {
        if (!r) return;
        facts.appendChild(el("dt", { text: r[0] }));
        facts.appendChild(el("dd", {}, [r[1]]));
      });
    }

    var pager = document.getElementById("pager");
    if (pager) {
      var newer = works[i - 1], older = works[i + 1];
      if (newer) pager.appendChild(el("a", { "class": "prev", href: newer.slug + ".html" }, [
        el("span", { "class": "label", text: "較新的作品" }), document.createTextNode(newer.title)
      ]));
      if (older) pager.appendChild(el("a", { "class": "next", href: older.slug + ".html" }, [
        el("span", { "class": "label", text: "較早的作品" }), document.createTextNode(older.title)
      ]));
    }
  }

  if (isWorkPage) renderWorkPage(); else renderIndex();
})();
