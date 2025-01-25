// https://docs.readthedocs.com/platform/stable/intro/mkdocs.html#configure-read-the-docs-search
document.addEventListener("DOMContentLoaded", function(event) {
// Trigger Read the Docs' search addon instead of Material MkDocs default
document.querySelector(".md-search__input").addEventListener("focus", (e) => {
        const event = new CustomEvent("readthedocs-search-show");
        document.dispatchEvent(event);
    });
});


// Use CustomEvent to generate the version selector
// https://docs.readthedocs.com/platform/stable/intro/mkdocs.html#integrate-the-read-the-docs-version-menu-into-your-site-navigation
document.addEventListener(
        "readthedocs-addons-data-ready",
        function (event) {
        const config = event.detail.data();
        const versioning = `
<div class="md-version">
<button class="md-version__current" aria-label="Select version">
    ${config.versions.current.slug}
</button>

<ul class="md-version__list">
${ config.versions.active.map(
    (version) => `
    <li class="md-version__item">
    <a href="${ version.urls.documentation }" class="md-version__link">
        ${ version.slug }
    </a>
            </li>`).join("\n")}
</ul>
</div>`;

    document.querySelector(".md-header__topic").insertAdjacentHTML("beforeend", versioning);
});