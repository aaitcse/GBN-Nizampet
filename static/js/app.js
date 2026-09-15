/*
 * GBN festival attendee app.
 *
 * Every interaction is a plain Django form POST first; this file intercepts
 * those forms with fetch() so the phone UI never does a full page reload.
 * With JavaScript disabled the same forms still work, they just redirect.
 */
(function () {
    "use strict";

    const shell = document.getElementById("app-container");
    if (!shell) return; // console pages share base.html but not this UI

    const urls = JSON.parse(shell.dataset.config);
    const state = {
        day: document.querySelector(".day-btn.bg-fest-accent")?.dataset.day || "Day 1",
        query: "",
        savedOnly: false,
        category: "All",
        photo: null,
    };

    const $ = (sel, root = document) => root.querySelector(sel);
    const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

    function csrf() {
        return $("#csrf-form [name=csrfmiddlewaretoken]").value;
    }

    function post(url, body) {
        return fetch(url, {
            method: "POST",
            headers: { "X-CSRFToken": csrf(), "X-Requested-With": "fetch" },
            body: body,
        });
    }

    function load(url, params) {
        const qs = new URLSearchParams(params).toString();
        return fetch(url + (qs ? "?" + qs : ""), {
            headers: { "X-Requested-With": "fetch" },
        }).then((r) => r.text());
    }

    function toast(text, tone) {
        const area = $("#toast-area");
        const node = document.createElement("div");
        node.className =
            "toast glass-panel px-4 py-2.5 rounded-2xl text-xs font-bold border text-white " +
            (tone === "error" ? "border-rose-500/50" : "border-fest-cyan/50");
        node.textContent = text;
        area.appendChild(node);
        setTimeout(() => node.remove(), 3200);
    }

    // ---------------------------------------------------------------- tabs
    function switchTab(tab) {
        $$(".tab-content").forEach((s) => s.classList.add("hidden"));
        $("#tab-" + tab)?.classList.remove("hidden");
        $$(".nav-btn").forEach((b) => {
            const on = b.dataset.tab === tab;
            b.classList.toggle("text-fest-accent", on);
            b.classList.toggle("text-gray-400", !on);
        });
        const url = new URL(window.location);
        url.searchParams.set("tab", tab);
        history.replaceState({}, "", url);
    }

    $$(".nav-btn").forEach((btn) =>
        btn.addEventListener("click", () => switchTab(btn.dataset.tab))
    );

    // -------------------------------------------------------------- events
    function refreshEvents() {
        return load(urls.events, {
            day: state.day,
            q: state.query,
            saved: state.savedOnly ? "1" : "",
        }).then((html) => {
            $("#events-list-container").innerHTML = html;
        });
    }

    $$(".day-btn").forEach((btn) =>
        btn.addEventListener("click", () => {
            state.day = btn.dataset.day;
            $$(".day-btn").forEach((b) => {
                const on = b === btn;
                b.className =
                    "day-btn px-4 py-1.5 rounded-full text-xs font-bold transition whitespace-nowrap " +
                    (on
                        ? "bg-fest-accent text-white shadow-md"
                        : "bg-white/5 border border-white/10 text-gray-400 hover:text-white");
            });
            refreshEvents();
        })
    );

    $$(".saved-btn").forEach((btn) =>
        btn.addEventListener("click", () => {
            state.savedOnly = btn.dataset.saved === "1";
            $$(".saved-btn").forEach((b) => {
                const on = b === btn;
                b.className =
                    "saved-btn px-3 py-1 rounded-lg text-[11px] font-bold " +
                    (on ? "bg-white/20 text-white" : "bg-white/5 text-gray-400 border border-white/10");
            });
            refreshEvents();
        })
    );

    let searchTimer;
    $("#event-search")?.addEventListener("input", (e) => {
        state.query = e.target.value;
        clearTimeout(searchTimer);
        searchTimer = setTimeout(refreshEvents, 220);
    });

    // Bookmark toggles live inside re-rendered HTML, so listen on the container.
    $("#events-list-container").addEventListener("submit", (e) => {
        const form = e.target.closest(".js-bookmark");
        if (!form) return;
        e.preventDefault();
        post(form.action, new FormData(form))
            .then((r) => r.json())
            .then((data) => {
                $("#agenda-count").textContent = data.agenda_count;
                toast(data.saved ? "Added to your agenda" : "Removed from your agenda");
                return refreshEvents();
            })
            .catch(() => toast("Could not save that event", "error"));
    });

    // ------------------------------------------------------------- gallery
    function refreshGallery() {
        return load(urls.gallery, { category: state.category }).then((html) => {
            $("#gallery-grid-container").innerHTML = html;
        });
    }

    $$(".gal-cat-btn").forEach((btn) =>
        btn.addEventListener("click", () => {
            state.category = btn.dataset.category;
            $$(".gal-cat-btn").forEach((b) => {
                const on = b === btn;
                b.className =
                    "gal-cat-btn px-3 py-1 rounded-full text-[11px] font-bold whitespace-nowrap " +
                    (on ? "bg-fest-cyan text-black" : "bg-white/10 border border-white/10 text-gray-300");
            });
            refreshGallery();
        })
    );

    // ------------------------------------------------------------ lightbox
    const lightbox = $("#lightbox");

    function openLightbox(card) {
        state.photo = card.dataset;
        $("#lb-image").src = card.dataset.image;
        $("#lb-caption").textContent = card.dataset.title;
        $("#lb-author").textContent = "Uploaded by " + card.dataset.author;
        $("#lb-likes").textContent = card.dataset.likes;
        paintLike(card.dataset.liked === "1");
        lightbox.classList.remove("hidden");
        lightbox.classList.add("flex");
    }

    function paintLike(liked) {
        const btn = $("#lb-like");
        btn.classList.toggle("bg-fest-accent", liked);
        btn.classList.toggle("text-white", liked);
        btn.classList.toggle("bg-fest-accent/20", !liked);
        btn.classList.toggle("text-fest-accent", !liked);
    }

    $("#gallery-grid-container").addEventListener("click", (e) => {
        const card = e.target.closest(".js-photo");
        if (card) openLightbox(card);
    });

    $("#lb-close").addEventListener("click", () => {
        lightbox.classList.add("hidden");
        lightbox.classList.remove("flex");
    });

    $("#lb-like").addEventListener("click", () => {
        if (!state.photo) return;
        post(state.photo.likeUrl, new FormData())
            .then((r) => r.json())
            .then((data) => {
                $("#lb-likes").textContent = data.likes;
                state.photo.likes = data.likes;
                state.photo.liked = data.liked ? "1" : "0";
                paintLike(data.liked);
                return refreshGallery();
            })
            .catch(() => toast("Could not register that like", "error"));
    });

    // -------------------------------------------------------- photo upload
    const uploadModal = $("#upload-modal");

    $("#open-upload").addEventListener("click", () => {
        uploadModal.classList.remove("hidden");
        uploadModal.classList.add("flex");
    });

    $("#upload-close").addEventListener("click", () => closeUpload());

    function closeUpload() {
        uploadModal.classList.add("hidden");
        uploadModal.classList.remove("flex");
        $("#upload-error").classList.add("hidden");
    }

    $$(".preset-btn").forEach((btn) =>
        btn.addEventListener("click", () => {
            $("#up-url").value = btn.dataset.url;
        })
    );

    $("#upload-form").addEventListener("submit", (e) => {
        e.preventDefault();
        const form = e.target;
        post(form.action, new FormData(form))
            .then((r) => r.json().then((data) => ({ ok: r.ok, data })))
            .then(({ ok, data }) => {
                if (!ok) {
                    const box = $("#upload-error");
                    box.textContent = Object.values(data.errors || {})
                        .flat()
                        .join(" ");
                    box.classList.remove("hidden");
                    return;
                }
                form.reset();
                closeUpload();
                toast(data.message);
                if (data.approved) refreshGallery();
            })
            .catch(() => toast("Upload failed, try again", "error"));
    });

    // ---------------------------------------------------------------- polls
    $("#polls-container").addEventListener("submit", (e) => {
        const form = e.target.closest(".js-vote-form");
        if (!form) return;
        e.preventDefault();
        const body = new FormData(form);
        if (e.submitter) body.set("option", e.submitter.value);
        const card = form.closest(".js-poll");
        post(form.action, body)
            .then((r) => r.text())
            .then((html) => {
                card.outerHTML = html;
                toast("Vote counted - thanks!");
            })
            .catch(() => toast("Could not record your vote", "error"));
    });

    $("#refresh-polls").addEventListener("click", () => {
        load(urls.polls, {}).then((html) => {
            $("#polls-container").innerHTML = html;
            toast("Results refreshed");
        });
    });

    // ------------------------------------------------------------- feedback
    const ratingInput = $("#fb-rating");

    function paintStars(value) {
        $$(".star-btn").forEach((btn) => {
            const on = Number(btn.dataset.star) <= value;
            btn.classList.toggle("text-fest-gold", on);
            btn.classList.toggle("text-gray-600", !on);
        });
    }

    $$(".star-btn").forEach((btn) =>
        btn.addEventListener("click", () => {
            ratingInput.value = btn.dataset.star;
            paintStars(Number(btn.dataset.star));
        })
    );

    $("#feedback-form").addEventListener("submit", (e) => {
        e.preventDefault();
        const form = e.target;
        post(form.action, new FormData(form))
            .then((r) => r.json().then((data) => ({ ok: r.ok, data })))
            .then(({ ok }) => {
                if (!ok) {
                    toast("Please add a comment first", "error");
                    return;
                }
                form.reset();
                ratingInput.value = 5;
                paintStars(5);
                form.classList.add("hidden");
                $("#feedback-success").classList.remove("hidden");
            })
            .catch(() => toast("Could not send feedback", "error"));
    });

    $("#feedback-again").addEventListener("click", () => {
        $("#feedback-success").classList.add("hidden");
        $("#feedback-form").classList.remove("hidden");
    });

    // Fade out any server-rendered messages.
    setTimeout(() => $$("#toast-area .toast").forEach((t) => t.remove()), 3600);
    paintStars(Number(ratingInput.value));
})();
