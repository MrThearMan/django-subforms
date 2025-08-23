function addItem(element) {
    console.log(element);

    const common_id_part = element.getAttribute("id");
    const common_name_part = common_id_part.replace(/^id_/, "");

    const items = parseInt(element.getAttribute("data-next"));
    element.removeAttribute("data-next")

    const initialElement = element.querySelector(":scope > ul > li");
    const newElement = initialElement.cloneNode(true);
    const subElements = newElement.querySelectorAll("input");

    subElements.forEach(element => {
        let element_id = element.getAttribute("id");
        element_id = element_id.replace(common_id_part + "__", "")
        element_id = element_id.replace(/\d+/, String(items))
        element_id = common_id_part + "__" + element_id
        element.setAttribute("id", element_id);

        let element_name = element.getAttribute("name");
        element_name = element_name.replace(common_name_part + "__", "")
        element_name = element_name.replace(/\d+/, String(items))
        element_name = common_name_part + "__" + element_name
        element.setAttribute("name", element_name);

        element.removeAttribute("value");
    })

    initialElement.parentElement.appendChild(newElement);
    element.setAttribute("data-next", String(items + 1))
}

function removeItem(element) {
    if (element.parentElement.childElementCount > 1) {
        element.remove();
    }
}
