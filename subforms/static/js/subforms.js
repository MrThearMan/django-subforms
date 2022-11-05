function addItem(element) {
    const items = parseInt(element.getAttribute("data-count"));
    element.removeAttribute("data-count")

    const initialElement = element.querySelector(":scope > ul > li");
    const newElement = initialElement.cloneNode(true);
    const subElements = newElement.querySelectorAll("input");

    subElements.forEach(element => {
        let element_id = element.getAttribute("id");
        element_id = element_id.replace(
            /-index-(?<index>\d+)_?\d*$/,
            ($index) => "-index-" + String(items),
        )

        element.setAttribute("id", element_id);
        element.removeAttribute("value");
    })

    initialElement.parentElement.appendChild(newElement);
    element.setAttribute("data-count", String(items + 1))
}

function removeItem(element) {
    if (element.parentElement.childElementCount > 1) {
        element.remove();
    }
}
