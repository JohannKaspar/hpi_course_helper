"use strict";
// This file contains all typescript code for the base.html template.
// Fix autofocus on bootstrap modals -> Focus the first element with `autofocus` attribute
document.addEventListener("shown.bs.modal", e => {
    if (!e.target)
        return;
    const modalEl = e.target;
    const autofocusEl = modalEl.querySelector("[autofocus]");
    if (autofocusEl) {
        autofocusEl.focus();
    }
});
